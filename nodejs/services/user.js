/**
 * 用户服务层：当前用户信息、脱敏（计划 5.7、10.57）
 * 纯业务逻辑，不依赖 req/res。
 */
const { getDb } = require('../db/pg');

/**
 * 获取当前用户信息（计划 10.57）
 * 返回 id、name、avatar_url、balance（单位分）、phone（脱敏）、email（脱敏）；
 * 不返回 wechat_open_id 等敏感字段。
 */
async function getMe(userId) {
  if (userId == null) return { error: '未登录', status: 401 };
  const pool = getDb();
  const result = await pool.query(
    'SELECT id, name, avatar_url, balance, phone, email, uid FROM users WHERE id = $1 AND deleted_at IS NULL',
    [Number(userId)]
  );
  const u = result.rows[0] ?? null;
  if (!u) return { error: '用户不存在', status: 404 };
  const phone = u.phone ? u.phone.replace(/(\d{3})\d+(\d{4})/, '$1****$2') : null;
  const email = u.email ? (u.email.replace ? u.email.replace(/(.).*(@.*)/, '$1***$2') : null) : null;
  return {
    id: u.id,
    name: u.name,
    avatar_url: u.avatar_url,
    balance: u.balance,
    phone,
    email,
    uid: u.uid != null ? String(u.uid) : undefined,
  };
}

module.exports = { getMe };
