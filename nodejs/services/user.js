/**
 * 用户服务层：当前用户信息、脱敏（计划 5.7、10.57）
 * 纯业务逻辑，不依赖 req/res。
 */
const { getDb } = require('../db/pg');

/**
 * 获取当前用户信息（计划 10.57）
 * 返回 id、name、avatar_url、balance（单位分）、api_key_masked、phone（脱敏）、email（脱敏）；
 * 不返回 joytrunk_api_key 明文，仅返回脱敏展示用 api_key_masked。
 */
async function getMe(userId) {
  if (userId == null) return { error: '未登录', status: 401 };
  const pool = getDb();
  const result = await pool.query(
    'SELECT id, name, avatar_url, balance, joytrunk_api_key, phone, email, uid FROM users WHERE id = $1 AND deleted_at IS NULL',
    [Number(userId)]
  );
  const u = result.rows[0] ?? null;
  if (!u) return { error: '用户不存在', status: 404 };
  const phone = u.phone ? u.phone.replace(/(\d{3})\d+(\d{4})/, '$1****$2') : null;
  const email = u.email ? (u.email.replace ? u.email.replace(/(.).*(@.*)/, '$1***$2') : null) : null;
  const api_key_masked = u.joytrunk_api_key
    ? `jt_****${String(u.joytrunk_api_key).slice(-4)}`
    : null;
  return {
    id: u.id,
    name: u.name,
    avatar_url: u.avatar_url,
    balance: u.balance,
    api_key_masked,
    phone,
    email,
    uid: u.uid != null ? String(u.uid) : undefined,
  };
}

/**
 * 更新当前用户资料（name、avatar_url）
 */
async function updateMe(userId, { name, avatar_url }) {
  if (userId == null) return { error: '未登录', status: 401 };
  const pool = getDb();
  const updates = [];
  const values = [];
  let idx = 1;
  if (name !== undefined) {
    const n = typeof name === 'string' ? name.trim() : '';
    if (n.length > 100) return { error: '昵称过长', status: 400 };
    updates.push(`name = $${idx++}`);
    values.push(n || null);
  }
  if (avatar_url !== undefined) {
    const url = typeof avatar_url === 'string' ? avatar_url.trim() : null;
    if (url !== null && url.length > 500) return { error: '头像 URL 过长', status: 400 };
    updates.push(`avatar_url = $${idx++}`);
    values.push(url || null);
  }
  if (updates.length === 0) return getMe(userId);
  values.push(Number(userId));
  await pool.query(
    `UPDATE users SET ${updates.join(', ')}, updated_at = CURRENT_TIMESTAMP WHERE id = $${idx} AND deleted_at IS NULL`,
    values
  );
  return getMe(userId);
}

/** 生成随机 JoyTrunk API Key（jt_ + 32 位 hex），写入用户并仅此一次返回明文 */
function randomApiKey() {
  const hex = '0123456789abcdef';
  let s = 'jt_';
  for (let i = 0; i < 32; i++) s += hex[Math.floor(Math.random() * 16)];
  return s;
}

async function generateApiKey(userId) {
  if (userId == null) return { error: '未登录', status: 401 };
  const pool = getDb();
  const api_key = randomApiKey();
  await pool.query(
    'UPDATE users SET joytrunk_api_key = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 AND deleted_at IS NULL',
    [api_key, Number(userId)]
  );
  return { api_key };
}

/**
 * 获取当前用户的 Token 用量与额度（可用于 LLM Router）
 * balance 来自 users.balance；quota 为可用额度（mock）；usage 为 router/custom 用量（mock）。
 */
async function getUsage(userId) {
  if (userId == null) return { error: '未登录', status: 401 };
  const me = await getMe(userId);
  if (me.error) return me;
  const balance = me.balance != null ? Number(me.balance) : 0;
  const quota = 10000;
  const usage = [
    { source: 'router', tokens: 0 },
    { source: 'custom', tokens: 0 },
  ];
  return { balance, quota, usage };
}

module.exports = { getMe, updateMe, generateApiKey, getUsage };
