/**
 * IM 控制层：解析请求、调用 IM 服务、写响应（计划 5.4、5.7）
 */
const imService = require('../services/im');

async function listConversations(req, res, next) {
  try {
    const list = await imService.getConversationsForUser(req.ownerId);
    res.json(list);
  } catch (e) {
    console.error('IM list conversations', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function createConversation(req, res, next) {
  const { type, peer_uid, title, member_uids, employee_id } = req.body || {};
  if (type === 'direct') {
    if (peer_uid == null || (typeof peer_uid === 'string' && !peer_uid.trim())) {
      return res.status(400).json({ error: '单聊需提供 peer_uid' });
    }
    try {
      const result = await imService.findOrCreateDirectConversation(req.ownerId, peer_uid, { employee_id });
      if (result.error) return res.status(result.status).json({ error: result.error });
      return res.status(201).json({ id: result.conversationId });
    } catch (e) {
      console.error('IM create conversation', e);
      return res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
    }
  }
  if (type === 'group') {
    if (!Array.isArray(member_uids) || member_uids.length === 0) {
      return res.status(400).json({ error: '群聊需提供 member_uids 数组且至少一名成员' });
    }
    try {
      const result = await imService.createGroupConversation(req.ownerId, { title, member_uids });
      if (result.error) return res.status(result.status).json({ error: result.error });
      return res.status(201).json({ id: result.conversationId });
    } catch (e) {
      console.error('IM create group conversation', e);
      return res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
    }
  }
  return res.status(400).json({ error: 'type 需为 direct 或 group' });
}

async function getMessages(req, res, next) {
  const id = Number(req.params.id);
  if (!id) return res.status(400).json({ error: '无效的会话 id' });
  const { limit, before, after } = req.query || {};
  try {
    const result = await imService.getMessages(id, req.ownerId, { limit, before, after });
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json(result);
  } catch (e) {
    console.error('IM get messages', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function getParticipants(req, res, next) {
  const id = Number(req.params.id);
  if (!id) return res.status(400).json({ error: '无效的会话 id' });
  const { limit, offset } = req.query || {};
  try {
    const result = await imService.getParticipants(id, req.ownerId, { limit, offset });
    if (result && result.error) return res.status(result.status).json({ error: result.error });
    res.json(result);
  } catch (e) {
    console.error('IM get participants', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function leaveConversation(req, res, next) {
  const id = Number(req.params.id);
  if (!id) return res.status(400).json({ error: '无效的会话 id' });
  try {
    const result = await imService.leaveConversation(id, req.ownerId);
    if (result && result.error) return res.status(result.status).json({ error: result.error });
    res.status(200).json(result);
  } catch (e) {
    console.error('IM leave', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function markConversationRead(req, res, next) {
  const id = Number(req.params.id);
  if (!id) return res.status(400).json({ error: '无效的会话 id' });
  const { last_read_msg_id } = req.body || {};
  try {
    const result = await imService.markConversationRead(id, req.ownerId, last_read_msg_id);
    if (result && result.error) return res.status(result.status).json({ error: result.error });
    res.status(200).json(result);
  } catch (e) {
    console.error('IM mark read', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function dismissConversation(req, res, next) {
  const id = Number(req.params.id);
  if (!id) return res.status(400).json({ error: '无效的会话 id' });
  try {
    const result = await imService.dismissConversation(id, req.ownerId);
    if (result && result.error) return res.status(result.status).json({ error: result.error });
    res.status(200).json(result);
  } catch (e) {
    console.error('IM dismiss', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function addParticipants(req, res, next) {
  const id = Number(req.params.id);
  if (!id) return res.status(400).json({ error: '无效的会话 id' });
  const { member_uids } = req.body || {};
  try {
    const result = await imService.addParticipants(id, req.ownerId, { member_uids });
    if (result && result.error) return res.status(result.status).json({ error: result.error });
    res.status(200).json(result);
  } catch (e) {
    console.error('IM add participants', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function removeParticipant(req, res, next) {
  const id = Number(req.params.id);
  const userId = Number(req.params.userId);
  if (!id || !userId) return res.status(400).json({ error: '无效的会话 id 或成员' });
  try {
    const result = await imService.removeParticipant(id, req.ownerId, userId);
    if (result && result.error) return res.status(result.status).json({ error: result.error });
    res.status(200).json(result);
  } catch (e) {
    console.error('IM remove participant', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function updateConversation(req, res, next) {
  const id = Number(req.params.id);
  if (!id) return res.status(400).json({ error: '无效的会话 id' });
  const { title, avatar_url, announcement } = req.body || {};
  try {
    const result = await imService.updateConversation(id, req.ownerId, { title, avatar_url, announcement });
    if (result && result.error) return res.status(result.status).json({ error: result.error });
    res.status(200).json(result);
  } catch (e) {
    console.error('IM update conversation', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function updateParticipant(req, res, next) {
  const id = Number(req.params.id);
  const userId = Number(req.params.userId);
  if (!id || !userId) return res.status(400).json({ error: '无效的会话 id 或成员' });
  const { role, muted_until } = req.body || {};
  try {
    const result = await imService.updateParticipant(id, req.ownerId, userId, { role, muted_until });
    if (result && result.error) return res.status(result.status).json({ error: result.error });
    res.status(200).json(result);
  } catch (e) {
    console.error('IM update participant', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

async function sendMessage(req, res, next) {
  const id = Number(req.params.id);
  if (!id) return res.status(400).json({ error: '无效的会话 id' });
  const { content, mention_user_ids: mentionUserIds, image_url: imageUrl } = req.body || {};
  try {
    const result = await imService.sendMessage(id, req.ownerId, content, mentionUserIds, imageUrl);
    if (result.error) {
      return res.status(result.status || 400).json({ error: result.error, code: result.code });
    }
    res.status(201).json(result.message);
  } catch (e) {
    console.error('IM send message', e);
    res.status(500).json({ error: '服务器错误', code: 'DB_ERROR' });
  }
}

module.exports = {
  listConversations,
  createConversation,
  getMessages,
  getParticipants,
  leaveConversation,
  markConversationRead,
  dismissConversation,
  addParticipants,
  removeParticipant,
  updateConversation,
  updateParticipant,
  sendMessage,
};
