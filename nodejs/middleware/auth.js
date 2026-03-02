/**
 * 鉴权中间件：JWT 校验，sub/userId 兼容，X-Owner-Id 仅开发环境（计划 5.3、10.12、10.35）
 * 已注销用户（deleted_at 非空）视为无效，返回 401。
 */
const jwt = require('jsonwebtoken');
const config = require('../config/default');
const { getDb } = require('../db/pg');

function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization;
  let token = null;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    token = authHeader.slice(7);
  }
  if (token) {
    try {
      const decoded = jwt.verify(token, config.JWT_SECRET, { algorithms: [config.JWT_ALGORITHM] });
      const userId = decoded.sub != null ? decoded.sub : decoded.userId;
      if (userId != null) {
        req.ownerId = Number(userId) || userId;
        req.isAgent = decoded.type === 'agent';
        return checkNotDeactivated(req, res, next).catch(next);
      }
    } catch {
      return res.status(401).json({ error: '凭证无效或已过期', code: 'TOKEN_INVALID' });
    }
  }
  if (config.ALLOW_X_OWNER_ID_FALLBACK && req.headers['x-owner-id']) {
    const id = req.headers['x-owner-id'];
    if (/^\d+$/.test(id)) {
      req.ownerId = Number(id);
      req.isAgent = false;
      return checkNotDeactivated(req, res, next).catch(next);
    }
  }
  return res.status(401).json({ error: '未提供凭证', code: 'UNAUTHORIZED' });
}

async function checkNotDeactivated(req, res, next) {
  try {
    const pool = getDb();
    const result = await pool.query('SELECT deleted_at FROM users WHERE id = $1', [req.ownerId]);
    const row = result.rows[0] ?? null;
    if (row && row.deleted_at != null) {
      return res.status(401).json({ error: '账号已注销', code: 'ACCOUNT_DEACTIVATED' });
    }
  } catch {
    // 忽略 DB 异常，由后续路由处理
  }
  next();
}

module.exports = { authMiddleware };
