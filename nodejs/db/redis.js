/**
 * Redis 连接与验证码键：getRedis、initRedis、trySetThrottleAndCode（原子化节流+写码）
 * 未配置或连接失败时 getRedis 抛 err.code = 'REDIS_UNAVAILABLE'；不实现内存降级。
 */
const Redis = require('ioredis');
const config = require('../config/default');

const RETRY_COUNT = 3;
const RETRY_DELAY_MS = 1500;

let client = null;
let available = false;

function getRedisUrl() {
  if (config.REDIS_URL) return config.REDIS_URL;
  const host = config.REDIS_HOST || 'localhost';
  const port = config.REDIS_PORT || 6379;
  const password = config.REDIS_PASSWORD || '';
  if (password) return `redis://:${encodeURIComponent(password)}@${host}:${port}`;
  return `redis://${host}:${port}`;
}

function isRedisConfigured() {
  return !!(config.REDIS_URL || config.REDIS_HOST);
}

/**
 * 初始化 Redis 连接；失败时重试 2～3 次，仍失败则置为不可用并打日志。
 */
async function initRedis() {
  if (client) return;
  if (!isRedisConfigured()) {
    console.warn('Redis: REDIS_URL or REDIS_HOST not set, verification code features will be unavailable.');
    return;
  }
  let lastErr;
  for (let i = 0; i < RETRY_COUNT; i++) {
    try {
      const url = getRedisUrl();
      client = new Redis(url, {
        maxRetriesPerRequest: null,
        retryStrategy(times) {
          if (times <= 3) return Math.min(times * 500, 2000);
          return null;
        },
      });
      await client.ping();
      available = true;
      return;
    } catch (e) {
      lastErr = e;
      if (i < RETRY_COUNT - 1) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
      }
    }
  }
  console.error('Redis initRedis failed after retries:', lastErr?.code || '', lastErr?.message || '');
  available = false;
}

function isRedisAvailable() {
  return available && client;
}

function getRedis() {
  if (!client || !available) {
    const err = new Error('Redis 不可用');
    err.code = 'REDIS_UNAVAILABLE';
    throw err;
  }
  return client;
}

/**
 * 原子化：节流 SET NX + 写入验证码。返回 true 表示未节流且已写入，false 表示处于节流期。
 * @param {string} channel - 'phone' | 'email'
 * @param {string} target - 手机号或邮箱
 * @param {string} code - 6 位验证码
 * @param {number} throttleSec - 节流秒数
 * @param {number} expireSec - 验证码过期秒数
 */
async function trySetThrottleAndCode(channel, target, code, throttleSec, expireSec) {
  const redis = getRedis();
  const throttleKey = `vc:throttle:${channel}:${target}`;
  const codeKey = `vc:${channel}:${target}`;
  // Lua: 若节流键不存在则 SET 节流键 EX throttleSec，并 SET 验证码键 EX expireSec，返回 1；否则返回 0
  const script = `
    if redis.call('SET', KEYS[1], '1', 'NX', 'EX', ARGV[1]) then
      redis.call('SET', KEYS[2], ARGV[2], 'EX', ARGV[3])
      return 1
    end
    return 0
  `;
  const result = await redis.eval(script, 2, throttleKey, codeKey, throttleSec, code, expireSec);
  return result === 1;
}

/**
 * 获取验证码（不删除）。用于登录校验前读取。
 */
async function getCode(channel, target) {
  const redis = getRedis();
  const codeKey = `vc:${channel}:${target}`;
  return redis.get(codeKey);
}

/**
 * 删除验证码键。校验通过后调用，实现一次性使用。
 */
async function delCode(channel, target) {
  const redis = getRedis();
  const codeKey = `vc:${channel}:${target}`;
  await redis.del(codeKey).catch(() => {});
}

module.exports = {
  initRedis,
  getRedis,
  isRedisAvailable,
  isRedisConfigured,
  trySetThrottleAndCode,
  getCode,
  delCode,
};
