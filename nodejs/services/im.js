/**
 * IM 业务：1:1 会话创建/列表、消息分页与发送（计划 5.4、4.2、10.2）
 */
const { getDb } = require('../db/pg');
const config = require('../config/default');

const MSG_MAX = config.MSG_MAX_LENGTH;

async function getConversationsForUser(userId) {
  const pool = getDb();
  const result = await pool.query(
    `
    SELECT c.id, c.type, c.title, c.peer_ids, c.updated_at, c.avatar_url, c.announcement,
           (SELECT content FROM messages m WHERE m.conversation_id = c.id AND m.is_deleted = 0 ORDER BY m.created_at DESC LIMIT 1) AS last_content,
           (SELECT created_at FROM messages m WHERE m.conversation_id = c.id AND m.is_deleted = 0 ORDER BY m.created_at DESC LIMIT 1) AS last_created_at,
           (SELECT COUNT(*)::int FROM messages m WHERE m.conversation_id = c.id AND m.is_deleted = 0 AND m.sender_id != $1
              AND (ucs.last_read_msg_id IS NULL OR m.id > ucs.last_read_msg_id)) AS unread_count,
           (SELECT COUNT(*)::int FROM messages m WHERE m.conversation_id = c.id AND m.is_deleted = 0 AND m.sender_id != $1
              AND (ucs.last_read_msg_id IS NULL OR m.id > ucs.last_read_msg_id)
              AND m.mention_user_ids IS NOT NULL AND $1 = ANY(m.mention_user_ids)) AS mention_unread_count
    FROM conversations c
    INNER JOIN participants p ON p.conversation_id = c.id AND p.user_id = $1
    LEFT JOIN user_conversation_status ucs ON ucs.conversation_id = c.id AND ucs.user_id = $1 AND (ucs.deleted_at IS NULL)
    WHERE c.dismissed_at IS NULL
    ORDER BY c.updated_at DESC
    LIMIT 100
  `,
    [userId]
  );
  const rows = result.rows || [];
  const userIdNum = Number(userId);
  const out = [];
  const seenDirectPeerIds = new Set();
  for (const r of rows) {
    let title = r.title;
    let peerIdForDirect = null;
    if (r.type === 'direct' && r.peer_ids) {
      const ids = r.peer_ids.split(',').map(Number);
      const otherId = ids.find((id) => id !== userIdNum);
      peerIdForDirect = otherId != null ? otherId : null;
      if (peerIdForDirect != null) {
        if (seenDirectPeerIds.has(peerIdForDirect)) continue;
        seenDirectPeerIds.add(peerIdForDirect);
        const uResult = await pool.query('SELECT name FROM users WHERE id = $1', [peerIdForDirect]);
        const u = uResult.rows[0] ?? null;
        title = u ? `与 ${u.name} 的对话` : `会话 ${r.id}`;
      }
    }
    out.push({
      id: r.id,
      type: r.type,
      title: title || `会话 ${r.id}`,
      last_message: r.last_content
        ? { content: r.last_content.slice(0, 40), created_at: r.last_created_at }
        : null,
      updated_at: r.updated_at,
      unread_count: r.unread_count != null ? Number(r.unread_count) : 0,
      mention_unread_count: r.mention_unread_count != null ? Number(r.mention_unread_count) : 0,
      avatar_url: r.avatar_url || null,
      announcement: r.announcement != null ? r.announcement : null,
    });
  }
  return out;
}

async function findOrCreateDirectConversation(userId, peerUid) {
  const pool = getDb();
  const uidStr = peerUid != null ? String(peerUid).trim() : '';
  if (!uidStr) return { error: '请提供对方用户 uid', status: 400 };

  const isJoytrunk = uidStr.toLowerCase() === 'joytrunk';
  let peerRow;
  if (isJoytrunk) {
    const joytrunkResult = await pool.query('SELECT id FROM users WHERE uid = 0 AND deleted_at IS NULL');
    peerRow = joytrunkResult.rows[0] ?? null;
    if (!peerRow) return { error: 'JoyTrunk 系统用户未就绪', status: 500 };
  } else {
    try {
      const peerResult = await pool.query(
        'SELECT id FROM users WHERE uid = $1 AND deleted_at IS NULL',
        [uidStr]
      );
      peerRow = peerResult.rows[0] ?? null;
    } catch (e) {
      if (e.code === '22P02' || e.code === '22003') return { error: '对应用户不存在', status: 404 };
      throw e;
    }
  }
  if (!peerRow) return { error: '对应用户不存在', status: 404 };

  const peerUserId = peerRow.id;
  const a = Number(userId);
  const b = Number(peerUserId);
  if (a === b) return { error: '不能与自己创建会话', status: 400 };
  const peerIds = [a, b].sort((x, y) => x - y).join(',');

  const existingResult = await pool.query('SELECT id FROM conversations WHERE type = $1 AND peer_ids = $2', ['direct', peerIds]);
  const existing = existingResult.rows[0] ?? null;
  if (existing) {
    if (isJoytrunk) {
      await pool.query('UPDATE conversations SET joytrunk_conversation = true WHERE id = $1', [existing.id]);
    }
    return { conversationId: existing.id };
  }

  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const insertResult = await client.query(
      isJoytrunk
        ? 'INSERT INTO conversations (type, peer_ids, creator_id, updated_at, joytrunk_conversation) VALUES ($1, $2, $3, CURRENT_TIMESTAMP, true) RETURNING id'
        : 'INSERT INTO conversations (type, peer_ids, creator_id, updated_at) VALUES ($1, $2, $3, CURRENT_TIMESTAMP) RETURNING id',
      ['direct', peerIds, userId]
    );
    const convId = insertResult.rows[0].id;
    await client.query('INSERT INTO participants (conversation_id, user_id, role) VALUES ($1, $2, $3)', [convId, a, 'member']);
    await client.query('INSERT INTO participants (conversation_id, user_id, role) VALUES ($1, $2, $3)', [convId, b, 'member']);
    await client.query('COMMIT');
    return { conversationId: convId };
  } catch (e) {
    await client.query('ROLLBACK').catch(() => {});
    if (e.code === '23505') {
      const againResult = await pool.query('SELECT id FROM conversations WHERE type = $1 AND peer_ids = $2', ['direct', peerIds]);
      const again = againResult.rows[0] ?? null;
      if (again) return { conversationId: again.id };
    }
    throw e;
  } finally {
    client.release();
  }
}

/** 创建群聊：member_uids 为要拉入的成员 uid 数组（不含自己），title 可选；仅按 users.uid 解析 */
async function createGroupConversation(userId, { title, member_uids }) {
  const pool = getDb();
  const uids = Array.isArray(member_uids) ? member_uids : [];
  if (uids.length === 0) return { error: '请至少选择一名成员', status: 400 };

  const creatorId = Number(userId);
  const memberIds = new Set([creatorId]);

  for (const uid of uids) {
    const uidStr = uid != null ? String(uid).trim() : '';
    if (!uidStr) continue;
    const r = await pool.query('SELECT id FROM users WHERE uid = $1 AND deleted_at IS NULL', [uidStr]);
    const row = r.rows[0] ?? null;
    if (row) memberIds.add(row.id);
  }

  memberIds.delete(creatorId);
  if (memberIds.size === 0) return { error: '请至少选择一名有效成员', status: 400 };

  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const insertResult = await client.query(
      `INSERT INTO conversations (type, title, peer_ids, creator_id, updated_at)
       VALUES ($1, $2, NULL, $3, CURRENT_TIMESTAMP) RETURNING id`,
      ['group', (title && String(title).trim()) || '群聊', creatorId]
    );
    const convId = insertResult.rows[0].id;
    await client.query(
      'INSERT INTO participants (conversation_id, user_id, role) VALUES ($1, $2, $3)',
      [convId, creatorId, 'owner']
    );
    for (const uid of memberIds) {
      await client.query(
        'INSERT INTO participants (conversation_id, user_id, role) VALUES ($1, $2, $3)',
        [convId, uid, 'member']
      );
    }
    await client.query('COMMIT');
    return { conversationId: convId };
  } catch (e) {
    await client.query('ROLLBACK').catch(() => {});
    throw e;
  } finally {
    client.release();
  }
}

async function ensureParticipant(userId, conversationId) {
  const pool = getDb();
  const result = await pool.query(
    'SELECT 1 FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, userId]
  );
  return (result.rows && result.rows.length > 0);
}

/** 标记已读：更新或插入 user_conversation_status.last_read_msg_id；仅成员可调 */
async function markConversationRead(conversationId, userId, lastReadMsgId) {
  const ok = await ensureParticipant(userId, conversationId);
  if (!ok) return { error: '无权限访问该会话', status: 403 };
  const pool = getDb();
  const msgId = lastReadMsgId != null ? Number(lastReadMsgId) : null;
  await pool.query(
    `INSERT INTO user_conversation_status (user_id, conversation_id, last_read_msg_id, updated_at)
     VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
     ON CONFLICT (user_id, conversation_id) DO UPDATE SET last_read_msg_id = $3, updated_at = CURRENT_TIMESTAMP`,
    [userId, conversationId, msgId]
  );
  return { read: true };
}

/** 退群：非成员 403；群主 400 要求先转让或解散；否则删 participants + user_conversation_status，幂等返回 200 */
async function leaveConversation(conversationId, userId) {
  const pool = getDb();
  const partResult = await pool.query(
    'SELECT role FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, userId]
  );
  const part = partResult.rows[0] ?? null;
  if (!part) return { error: '你不是该群成员', status: 403 };
  if (part.role === 'owner') return { error: '请先转让群主或解散群', status: 400 };
  await pool.query('DELETE FROM participants WHERE conversation_id = $1 AND user_id = $2', [conversationId, userId]);
  await pool.query('DELETE FROM user_conversation_status WHERE conversation_id = $1 AND user_id = $2', [conversationId, userId]);
  return { left: true };
}

/** 解散群：仅群主可调，否则 403；已解散 403；软删 conversations.dismissed_at */
async function dismissConversation(conversationId, userId) {
  const pool = getDb();
  const convResult = await pool.query('SELECT id, dismissed_at FROM conversations WHERE id = $1', [conversationId]);
  const conv = convResult.rows[0] ?? null;
  if (!conv) return { error: '会话不存在', status: 404 };
  if (conv.dismissed_at) return { error: '群已解散', status: 403 };
  const partResult = await pool.query(
    'SELECT role FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, userId]
  );
  const part = partResult.rows[0] ?? null;
  if (!part) return { error: '你不是该群成员', status: 403 };
  if (part.role !== 'owner') return { error: '仅群主可解散群', status: 403 };
  await pool.query('UPDATE conversations SET dismissed_at = CURRENT_TIMESTAMP WHERE id = $1', [conversationId]);
  return { dismissed: true };
}

/** 会话成员列表：仅成员可调；单聊返回 2 人，群聊返回所有成员；limit 1～100 默认 20 */
async function getParticipants(conversationId, userId, opts = {}) {
  const ok = await ensureParticipant(userId, conversationId);
  if (!ok) return { error: '无权限访问该会话', status: 403 };
  const pool = getDb();
  const limit = Math.min(Math.max(Number(opts.limit) || 20, 1), 100);
  const offset = Math.max(Number(opts.offset) || 0, 0);
  const result = await pool.query(
    `SELECT p.user_id, p.role, p.joined_at, p.muted_until, u.name, u.uid
     FROM participants p
     JOIN users u ON u.id = p.user_id AND u.deleted_at IS NULL
     WHERE p.conversation_id = $1
     ORDER BY CASE p.role WHEN 'owner' THEN 1 WHEN 'admin' THEN 2 ELSE 3 END, p.joined_at ASC
     LIMIT $2 OFFSET $3`,
    [conversationId, limit, offset]
  );
  const rows = result.rows || [];
  return rows.map((r) => ({
    user_id: r.user_id,
    role: r.role,
    joined_at: r.joined_at,
    muted_until: r.muted_until,
    name: r.name,
    uid: r.uid != null ? String(r.uid) : null,
  }));
}

/** 加人：仅群主/管理员；群聊且未解散；部分成功（已存在则跳过）；新成员 last_read_msg_id 设为当前最新 */
async function addParticipants(conversationId, userId, { member_uids }) {
  const pool = getDb();
  const convResult = await pool.query('SELECT id, type, dismissed_at FROM conversations WHERE id = $1', [conversationId]);
  const conv = convResult.rows[0] ?? null;
  if (!conv) return { error: '会话不存在', status: 404 };
  if (conv.dismissed_at) return { error: '群已解散', status: 403 };
  if (conv.type !== 'group') return { error: '仅群聊可添加成员', status: 400 };
  const partResult = await pool.query(
    'SELECT role FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, userId]
  );
  const part = partResult.rows[0] ?? null;
  if (!part) return { error: '你不是该群成员', status: 403 };
  if (part.role !== 'owner' && part.role !== 'admin') return { error: '仅群主或管理员可操作', status: 403 };
  const uids = Array.isArray(member_uids) ? member_uids : [];
  if (uids.length === 0) return { error: '请提供 member_uids 数组且至少一名成员', status: 400 };

  const toAdd = [];
  for (const uid of uids) {
    const uidStr = uid != null ? String(uid).trim() : '';
    if (!uidStr) continue;
    const r = await pool.query('SELECT id FROM users WHERE uid = $1 AND deleted_at IS NULL', [uidStr]);
    const row = r.rows[0] ?? null;
    if (row) toAdd.push(row.id);
  }
  if (toAdd.length === 0) return { error: '请至少选择一名有效成员', status: 400 };

  const existingResult = await pool.query('SELECT user_id FROM participants WHERE conversation_id = $1', [conversationId]);
  const existingIds = new Set((existingResult.rows || []).map((r) => r.user_id));

  const latestResult = await pool.query(
    'SELECT COALESCE(MAX(id), 0) AS latest FROM messages WHERE conversation_id = $1 AND is_deleted = 0',
    [conversationId]
  );
  const latestMsgId = latestResult.rows[0]?.latest != null ? Number(latestResult.rows[0].latest) : null;

  const added = [];
  for (const uid of toAdd) {
    if (existingIds.has(uid)) continue;
    try {
      await pool.query(
        'INSERT INTO participants (conversation_id, user_id, role) VALUES ($1, $2, $3)',
        [conversationId, uid, 'member']
      );
      existingIds.add(uid);
      added.push(uid);
      await pool.query(
        `INSERT INTO user_conversation_status (user_id, conversation_id, last_read_msg_id, updated_at)
         VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
         ON CONFLICT (user_id, conversation_id) DO UPDATE SET last_read_msg_id = $3, updated_at = CURRENT_TIMESTAMP`,
        [uid, conversationId, latestMsgId]
      );
    } catch (e) {
      if (e.code === '23505') existingIds.add(uid);
    }
  }
  return { added };
}

/** 踢人：仅群主/管理员；删除 participants 并置 user_conversation_status.deleted_at */
async function removeParticipant(conversationId, userId, targetUserId) {
  const pool = getDb();
  const convResult = await pool.query('SELECT id, type, dismissed_at FROM conversations WHERE id = $1', [conversationId]);
  const conv = convResult.rows[0] ?? null;
  if (!conv) return { error: '会话不存在', status: 404 };
  if (conv.dismissed_at) return { error: '群已解散', status: 403 };
  if (conv.type !== 'group') return { error: '仅群聊可移除成员', status: 400 };
  const partResult = await pool.query(
    'SELECT role FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, userId]
  );
  const part = partResult.rows[0] ?? null;
  if (!part) return { error: '你不是该群成员', status: 403 };
  if (part.role !== 'owner' && part.role !== 'admin') return { error: '仅群主或管理员可操作', status: 403 };
  const targetId = Number(targetUserId);
  if (!targetId) return { error: '无效的成员', status: 400 };
  const targetPart = await pool.query(
    'SELECT 1 FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, targetId]
  );
  if (!targetPart.rows || targetPart.rows.length === 0) return { error: '该用户不是群成员', status: 404 };
  await pool.query('DELETE FROM participants WHERE conversation_id = $1 AND user_id = $2', [conversationId, targetId]);
  await pool.query(
    'UPDATE user_conversation_status SET deleted_at = CURRENT_TIMESTAMP WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, targetId]
  );
  return { removed: true };
}

const TITLE_MAX = 100;

/** 更新群信息（群名/头像/公告）：仅群主/管理员；仅 type=group；title 最长 TITLE_MAX */
async function updateConversation(conversationId, userId, { title, avatar_url, announcement }) {
  const pool = getDb();
  const convResult = await pool.query(
    'SELECT id, type, dismissed_at FROM conversations WHERE id = $1',
    [conversationId]
  );
  const conv = convResult.rows[0] ?? null;
  if (!conv) return { error: '会话不存在', status: 404 };
  if (conv.dismissed_at) return { error: '群已解散', status: 403 };
  if (conv.type !== 'group') return { error: '仅群聊可修改信息', status: 400 };
  const partResult = await pool.query(
    'SELECT role FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, userId]
  );
  const part = partResult.rows[0] ?? null;
  if (!part) return { error: '你不是该群成员', status: 403 };
  if (part.role !== 'owner' && part.role !== 'admin') return { error: '仅群主或管理员可操作', status: 403 };

  const updates = [];
  const values = [];
  let idx = 1;
  if (title !== undefined) {
    const t = typeof title === 'string' ? title.trim() : '';
    if (t.length > TITLE_MAX) return { error: '群名称过长', status: 400 };
    updates.push(`title = $${idx++}`);
    values.push(t || null);
  }
  if (avatar_url !== undefined) {
    updates.push(`avatar_url = $${idx++}`);
    values.push(typeof avatar_url === 'string' ? avatar_url : null);
  }
  if (announcement !== undefined) {
    updates.push(`announcement = $${idx++}`);
    values.push(typeof announcement === 'string' ? announcement : null);
    updates.push('announcement_updated_at = CURRENT_TIMESTAMP');
  }
  if (updates.length === 0) return { updated: true };
  updates.push('updated_at = CURRENT_TIMESTAMP');
  values.push(conversationId);
  await pool.query(
    `UPDATE conversations SET ${updates.join(', ')} WHERE id = $${idx}`,
    values
  );
  return { updated: true };
}

/** 更新成员角色或禁言：仅群主可转让/设管理员；群主/管理员可禁言；muted_until 过去或 null 为取消禁言 */
async function updateParticipant(conversationId, userId, targetUserId, { role, muted_until }) {
  const pool = getDb();
  const convResult = await pool.query(
    'SELECT id, type, dismissed_at FROM conversations WHERE id = $1',
    [conversationId]
  );
  const conv = convResult.rows[0] ?? null;
  if (!conv) return { error: '会话不存在', status: 404 };
  if (conv.dismissed_at) return { error: '群已解散', status: 403 };
  if (conv.type !== 'group') return { error: '仅群聊可操作', status: 400 };
  const partResult = await pool.query(
    'SELECT role FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, userId]
  );
  const part = partResult.rows[0] ?? null;
  if (!part) return { error: '你不是该群成员', status: 403 };
  const targetId = Number(targetUserId);
  if (!targetId) return { error: '无效的成员', status: 400 };
  const targetPartResult = await pool.query(
    'SELECT role FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, targetId]
  );
  const targetPart = targetPartResult.rows[0] ?? null;
  if (!targetPart) return { error: '目标用户须为当前群成员', status: 400 };

  if (role !== undefined) {
    if (part.role !== 'owner') return { error: '仅群主可转让或设置管理员', status: 403 };
    const r = String(role).toLowerCase();
    if (r === 'owner') {
      await pool.query(
        'UPDATE participants SET role = $1 WHERE conversation_id = $2 AND user_id = $3',
        ['member', conversationId, userId]
      );
      await pool.query(
        'UPDATE participants SET role = $1 WHERE conversation_id = $2 AND user_id = $3',
        ['owner', conversationId, targetId]
      );
    } else if (r === 'admin' || r === 'member') {
      if (targetPart.role === 'owner') return { error: '不能修改群主角色', status: 400 };
      await pool.query(
        'UPDATE participants SET role = $1 WHERE conversation_id = $2 AND user_id = $3',
        [r, conversationId, targetId]
      );
    } else {
      return { error: '无效的 role', status: 400 };
    }
  }
  if (muted_until !== undefined) {
    if (part.role !== 'owner' && part.role !== 'admin') return { error: '仅群主或管理员可操作', status: 403 };
    if (targetPart.role === 'owner') return { error: '不能禁言群主', status: 400 };
    const m = muted_until == null ? null : new Date(muted_until);
    if (m !== null && isNaN(m.getTime())) return { error: '无效的 muted_until', status: 400 };
    const muteVal = m == null || m.getTime() <= Date.now() ? null : m;
    await pool.query(
      'UPDATE participants SET muted_until = $1 WHERE conversation_id = $2 AND user_id = $3',
      [muteVal, conversationId, targetId]
    );
  }
  return { updated: true };
}

async function getMessages(conversationId, userId, opts = {}) {
  const ok = await ensureParticipant(userId, conversationId);
  if (!ok) return { error: '无权限访问该会话', status: 403 };
  const pool = getDb();
  const limit = Math.min(Number(opts.limit) || 20, 100);
  const after = opts.after != null ? Number(opts.after) : null;
  const before = opts.before != null ? String(opts.before) : null;

  if (after != null && !Number.isNaN(after)) {
    const result = await pool.query(
      `SELECT id, conversation_id, sender_id, content, status, created_at, updated_at, is_deleted, image_url
       FROM messages WHERE conversation_id = $1 AND is_deleted = 0 AND id > $2
       ORDER BY created_at ASC LIMIT $3`,
      [conversationId, after, limit]
    );
    const rows = result.rows || [];
    const latestResult = await pool.query(
      'SELECT COALESCE(MAX(id), 0) AS latest FROM messages WHERE conversation_id = $1 AND is_deleted = 0',
      [conversationId]
    );
    const latest_msg_id = latestResult.rows[0]?.latest != null ? Number(latestResult.rows[0].latest) : null;
    return { items: rows.map(toMessageItem), next_cursor: null, has_more: rows.length === limit, latest_msg_id };
  }

  let rows;
  if (before) {
    const parsed = parseCursor(before);
    if (parsed) {
      const result = await pool.query(
        `SELECT id, conversation_id, sender_id, content, status, created_at, updated_at, is_deleted, image_url
         FROM messages WHERE conversation_id = $1 AND is_deleted = 0
         AND (created_at < $2 OR (created_at = $3 AND id < $4))
         ORDER BY created_at DESC LIMIT $5`,
        [conversationId, parsed.created_at, parsed.created_at, parsed.id, limit]
      );
      rows = result.rows || [];
    } else {
      const result = await pool.query(
        `SELECT id, conversation_id, sender_id, content, status, created_at, updated_at, is_deleted, image_url
         FROM messages WHERE conversation_id = $1 AND is_deleted = 0
         ORDER BY created_at DESC LIMIT $2`,
        [conversationId, limit]
      );
      rows = result.rows || [];
    }
  } else {
    const result = await pool.query(
      `SELECT id, conversation_id, sender_id, content, status, created_at, updated_at, is_deleted, image_url
       FROM messages WHERE conversation_id = $1 AND is_deleted = 0
       ORDER BY created_at DESC LIMIT $2`,
      [conversationId, limit]
    );
    rows = result.rows || [];
  }

  const items = rows.reverse().map(toMessageItem);
  let next_cursor = null;
  if (rows.length === limit && rows.length > 0) {
    const oldest = rows[0];
    next_cursor = encodeCursor(oldest.id, oldest.created_at);
  }
  const latestResult = await pool.query(
    'SELECT COALESCE(MAX(id), 0) AS latest FROM messages WHERE conversation_id = $1 AND is_deleted = 0',
    [conversationId]
  );
  const latest_msg_id = latestResult.rows[0]?.latest != null ? Number(latestResult.rows[0].latest) : null;
  return { items, next_cursor, has_more: !!next_cursor, latest_msg_id };
}

function toMessageItem(r) {
  return {
    id: r.id,
    conversation_id: r.conversation_id,
    sender_id: r.sender_id,
    content: r.content,
    status: r.status,
    created_at: r.created_at,
    updated_at: r.updated_at,
    mention_user_ids: r.mention_user_ids != null ? r.mention_user_ids : null,
    image_url: r.image_url != null ? r.image_url : null,
  };
}

function encodeCursor(id, created_at) {
  return Buffer.from(JSON.stringify({ last_msg_id: id, last_created_at: created_at })).toString('base64url');
}

function parseCursor(cursor) {
  try {
    const s = Buffer.from(cursor, 'base64url').toString('utf8');
    const o = JSON.parse(s);
    if (o.last_msg_id != null && o.last_created_at != null) return o;
  } catch {}
  return null;
}

async function sendMessage(conversationId, userId, content, mentionUserIds = null, imageUrl = null) {
  const ok = await ensureParticipant(userId, conversationId);
  if (!ok) return { error: '无权限', status: 403 };
  const pool = getDb();
  const muteResult = await pool.query(
    'SELECT muted_until FROM participants WHERE conversation_id = $1 AND user_id = $2',
    [conversationId, userId]
  );
  const muteRow = muteResult.rows[0] ?? null;
  if (muteRow && muteRow.muted_until) {
    const until = new Date(muteRow.muted_until).getTime();
    if (until > Date.now()) return { error: '你已被禁言', code: 'MUTED', status: 403 };
  }
  const trimmed = typeof content === 'string' ? content.trim() : '';
  const hasImage = typeof imageUrl === 'string' && imageUrl.trim().length > 0;
  if (!trimmed && !hasImage) return { error: '消息内容不能为空', status: 400 };
  if (trimmed.length > MSG_MAX) return { error: '内容超长', code: 'CONTENT_TOO_LONG', status: 400 };
  const contentToSave = trimmed || (hasImage ? '[图片]' : '');

  const convRow = (await pool.query('SELECT joytrunk_conversation FROM conversations WHERE id = $1', [conversationId])).rows[0];
  const userSyncRow = (await pool.query('SELECT sync_joytrunk_chat FROM users WHERE id = $1 AND deleted_at IS NULL', [userId])).rows[0];
  const isJoytrunkNoSync = convRow?.joytrunk_conversation && userSyncRow && userSyncRow.sync_joytrunk_chat === false;

  let finalMentionIds = Array.isArray(mentionUserIds) ? [...mentionUserIds] : [];
  if (contentToSave.includes('@所有人')) {
    const partResult = await pool.query(
      'SELECT user_id FROM participants WHERE conversation_id = $1',
      [conversationId]
    );
    const allIds = (partResult.rows || []).map((r) => r.user_id);
    const set = new Set(finalMentionIds);
    allIds.forEach((id) => set.add(id));
    finalMentionIds = Array.from(set);
  }

  let row;
  if (isJoytrunkNoSync) {
    await pool.query('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = $1', [conversationId]);
    row = {
      id: null,
      conversation_id: Number(conversationId),
      sender_id: userId,
      content: contentToSave,
      status: 'sent',
      created_at: new Date(),
      updated_at: new Date(),
      mention_user_ids: finalMentionIds.length ? finalMentionIds : null,
      image_url: hasImage ? imageUrl.trim() : null,
    };
  } else {
    const insertResult = await pool.query(
      `INSERT INTO messages (conversation_id, sender_id, content, status, mention_user_ids, image_url) VALUES ($1, $2, $3, 'sent', $4, $5) RETURNING id, conversation_id, sender_id, content, status, created_at, updated_at, mention_user_ids, image_url`,
      [conversationId, userId, contentToSave, finalMentionIds.length ? finalMentionIds : null, hasImage ? imageUrl.trim() : null]
    );
    row = insertResult.rows[0];
    await pool.query('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = $1', [conversationId]);
  }

  if (convRow && convRow.joytrunk_conversation) {
    const pendingCliTasks = require('./pendingCliTasks');
    const crypto = require('crypto');
    const taskId = crypto.randomBytes(16).toString('hex');
    const payload = {
      owner_id: userId,
      employee_id: '',
      content: contentToSave,
      session_key: 'owner',
      conversation_id: String(conversationId),
    };
    pendingCliTasks.pushOrEnqueueTask(userId, taskId, payload).catch((e) => console.error('pushOrEnqueueTask', e));
  }

  return { message: toMessageItem(row) };
}

/** 当 sync_joytrunk_chat 为 true 时，将会话中的 JoyTrunk 回复写入 messages 表（供 task_result 回调） */
async function insertJoytrunkReply(userId, conversationId, content) {
  const pool = getDb();
  const userRow = (await pool.query('SELECT sync_joytrunk_chat FROM users WHERE id = $1 AND deleted_at IS NULL', [Number(userId)])).rows[0];
  if (!userRow || userRow.sync_joytrunk_chat === false) return;
  const botRow = (await pool.query('SELECT id FROM users WHERE uid = 0')).rows[0];
  if (!botRow) return;
  await pool.query(
    'INSERT INTO messages (conversation_id, sender_id, content, status) VALUES ($1, $2, $3, $4)',
    [Number(conversationId), botRow.id, String(content || '').trim() || '(无内容)', 'sent']
  );
  await pool.query('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = $1', [conversationId]);
}

module.exports = {
  getConversationsForUser,
  findOrCreateDirectConversation,
  createGroupConversation,
  ensureParticipant,
  getParticipants,
  addParticipants,
  removeParticipant,
  updateConversation,
  updateParticipant,
  markConversationRead,
  leaveConversation,
  dismissConversation,
  getMessages,
  sendMessage,
  insertJoytrunkReply,
};
