/**
 * CLI 绑定会话：生成 code、Redis 存储、轮询与确认（joytrunk bind 流程）
 * 依赖 Redis；未配置时 start/poll 返回 503。
 */
const crypto = require('crypto');
const { getRedis, isRedisAvailable } = require('../db/redis');
const userService = require('./user');

const BIND_EXPIRE_SECONDS = Number(process.env.CLI_BIND_EXPIRE_SECONDS) || 600; // 10 min
const BIND_CODE_LENGTH = 8;

function generateBindCode() {
  return crypto.randomBytes(Math.ceil(BIND_CODE_LENGTH / 2)).toString('hex').slice(0, BIND_CODE_LENGTH);
}

function getBindKey(code) {
  return `cli_bind:${code}`;
}

/**
 * 前端绑定页 base URL，用于生成 bind_url（后端托管前端时与后端同源，默认 32891）
 */
function getFrontendBindBaseUrl() {
  const base = process.env.OFFICIAL_FRONTEND_URL || process.env.CLI_BIND_FRONTEND_URL || 'http://localhost:32891';
  return base.replace(/\/$/, '');
}

/**
 * 创建绑定会话，返回 bind_code、bind_url、expires_in_seconds
 * @param {{ device_name?: string }} body
 */
async function startBind(body = {}) {
  if (!isRedisAvailable()) {
    return { error: '绑定服务暂不可用（需 Redis）', status: 503, code: 'REDIS_UNAVAILABLE' };
  }
  const code = generateBindCode();
  const redis = getRedis();
  const payload = {
    status: 'pending',
    device_name: body.device_name || null,
    created_at: Date.now(),
  };
  await redis.setex(getBindKey(code), BIND_EXPIRE_SECONDS, JSON.stringify(payload));
  const frontendBase = getFrontendBindBaseUrl();
  const bind_url = `${frontendBase}/bind?code=${code}`;
  return {
    bind_code: code,
    bind_url,
    expires_in_seconds: BIND_EXPIRE_SECONDS,
  };
}

/**
 * 轮询绑定状态；若已授权返回 status: 'authorized', api_key
 */
async function pollBind(code) {
  if (!isRedisAvailable()) {
    return { error: '绑定服务暂不可用', status: 503, code: 'REDIS_UNAVAILABLE' };
  }
  if (!code || typeof code !== 'string' || !code.trim()) {
    return { error: '缺少 code', status: 400 };
  }
  const redis = getRedis();
  const key = getBindKey(code.trim());
  const raw = await redis.get(key);
  if (!raw) {
    return { status: 'pending' }; // 过期或不存在
  }
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return { status: 'pending' };
  }
  if (data.status !== 'authorized' || !data.api_key) {
    return { status: 'pending' };
  }
  // 一次性：取走后删除，避免重复 poll 拿到 key
  await redis.del(key).catch(() => {});
  return { status: 'authorized', api_key: data.api_key };
}

/**
 * 确认绑定（需登录）：校验 code，将当前用户与 code 关联，生成或复用 api_key，标记 authorized
 */
async function confirmBind(userId, code) {
  if (!isRedisAvailable()) {
    return { error: '绑定服务暂不可用', status: 503, code: 'REDIS_UNAVAILABLE' };
  }
  if (!code || typeof code !== 'string' || !code.trim()) {
    return { error: '缺少 code', status: 400 };
  }
  const redis = getRedis();
  const key = getBindKey(code.trim());
  const raw = await redis.get(key);
  if (!raw) {
    return { error: '绑定码已过期或无效', status: 404, code: 'BIND_EXPIRED' };
  }
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return { error: '绑定码无效', status: 400 };
  }
  if (data.status === 'authorized') {
    return { error: '该绑定码已使用', status: 400, code: 'BIND_ALREADY_USED' };
  }
  const userResult = await userService.getMe(userId);
  if (userResult.error) {
    return { error: userResult.error, status: userResult.status };
  }
  let api_key;
  const { getDb } = require('../db/pg');
  const pool = getDb();
  const row = (await pool.query('SELECT joytrunk_api_key FROM users WHERE id = $1 AND deleted_at IS NULL', [Number(userId)])).rows[0];
  if (!row || !row.joytrunk_api_key) {
    const gen = await userService.generateApiKey(userId);
    if (gen.error) return { error: gen.error, status: gen.status };
    api_key = gen.api_key;
  } else {
    api_key = row.joytrunk_api_key;
  }
  data.status = 'authorized';
  data.user_id = userId;
  data.api_key = api_key;
  await redis.setex(key, Math.max(60, BIND_EXPIRE_SECONDS), JSON.stringify(data)); // 留 1 分钟给 poll 取
  return { ok: true };
}

module.exports = { startBind, pollBind, confirmBind, getFrontendBindBaseUrl };
