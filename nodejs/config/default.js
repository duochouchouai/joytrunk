/**
 * 后端可配置参数（计划 10.56、10.57）；环境变量覆盖。
 * 登录与余额相关配置均集中在此，按环境可拆分为 production.js 等。
 */
module.exports = {
  // --- 服务与数据库 ---
  // PostgreSQL：.env 中配置 DATABASE_URL 或 PG_HOST/PG_PORT/PG_USER/PG_PASSWORD/PG_DATABASE
  DATABASE_URL: process.env.DATABASE_URL || undefined,
  PG_HOST: process.env.PG_HOST || 'localhost',
  PG_PORT: Number(process.env.PG_PORT) || 5432,
  PG_USER: process.env.PG_USER || 'postgres',
  PG_PASSWORD: process.env.PG_PASSWORD || '',
  PG_DATABASE: process.env.PG_DATABASE || 'joytrunk',
  PG_SSL: process.env.PG_SSL === 'true' || process.env.PG_SSL === true,
  PG_POOL_MAX: process.env.PG_POOL_MAX != null ? Number(process.env.PG_POOL_MAX) : 10,
  PG_POOL_IDLE_TIMEOUT_MILLIS: process.env.PG_POOL_IDLE_TIMEOUT_MILLIS != null ? Number(process.env.PG_POOL_IDLE_TIMEOUT_MILLIS) : 10000,
  PG_POOL_CONNECTION_TIMEOUT_MILLIS: process.env.PG_POOL_CONNECTION_TIMEOUT_MILLIS != null ? Number(process.env.PG_POOL_CONNECTION_TIMEOUT_MILLIS) : 5000,
  PORT: Number(process.env.PORT) || 32891,
  HOST: process.env.HOST || 'localhost',
  NODE_ENV: process.env.NODE_ENV || 'development',

  // --- JWT 鉴权 ---
  JWT_SECRET: process.env.JWT_SECRET || 'dev-secret-change-in-production',
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '2h',
  JWT_ALGORITHM: 'HS256',

  // --- IM 业务 ---
  MSG_MAX_LENGTH: Number(process.env.MSG_MAX_LENGTH) || 4096,
  ALLOW_X_OWNER_ID_FALLBACK:
    process.env.ALLOW_X_OWNER_ID_FALLBACK === 'true' || process.env.NODE_ENV !== 'production',
  CLEANUP_DELETED_CONVERSATIONS_AFTER_DAYS:
    process.env.CLEANUP_DELETED_CONVERSATIONS_AFTER_DAYS != null ? Number(process.env.CLEANUP_DELETED_CONVERSATIONS_AFTER_DAYS) : 90,
  CLEANUP_READ_MESSAGES_AFTER_DAYS:
    process.env.CLEANUP_READ_MESSAGES_AFTER_DAYS != null ? Number(process.env.CLEANUP_READ_MESSAGES_AFTER_DAYS) : 180,

  // --- 登录接口配置（10.57）---
  // 微信登录：小程序或公众号 appid/secret，用于用 code 换 open_id/union_id
  WECHAT_APP_ID: process.env.WECHAT_APP_ID,
  WECHAT_APP_SECRET: process.env.WECHAT_APP_SECRET,

  // 手机验证码：阿里云短信（计划：账号系统验证码与登录具体实现）
  SMS_PROVIDER: process.env.SMS_PROVIDER,
  SMS_ACCESS_KEY_ID: process.env.SMS_ACCESS_KEY_ID || process.env.SMS_ACCESS_KEY,
  SMS_ACCESS_KEY_SECRET: process.env.SMS_ACCESS_KEY_SECRET || process.env.SMS_SECRET,
  SMS_SIGN_NAME: process.env.SMS_SIGN_NAME,
  SMS_TEMPLATE_CODE: process.env.SMS_TEMPLATE_CODE,
  SMS_REGION_ID: process.env.SMS_REGION_ID || 'cn-hangzhou',
  SMS_ENDPOINT: process.env.SMS_ENDPOINT || 'dysmsapi.aliyuncs.com',

  // 验证码 Redis 与节流
  CODE_EXPIRE_SECONDS: process.env.CODE_EXPIRE_SECONDS != null ? Number(process.env.CODE_EXPIRE_SECONDS) : 300,
  CODE_THROTTLE_SECONDS: process.env.CODE_THROTTLE_SECONDS != null ? Number(process.env.CODE_THROTTLE_SECONDS) : 60,

  // Redis（验证码存储）
  REDIS_URL: process.env.REDIS_URL || undefined,
  REDIS_HOST: process.env.REDIS_HOST,
  REDIS_PORT: process.env.REDIS_PORT != null ? Number(process.env.REDIS_PORT) : 6379,
  REDIS_PASSWORD: process.env.REDIS_PASSWORD || '',

  // 邮箱验证码：对接邮件服务或开发环境占位
  MAIL_FROM: process.env.MAIL_FROM,
  MAIL_HOST: process.env.MAIL_HOST,
  MAIL_PORT: process.env.MAIL_PORT,
  MAIL_USER: process.env.MAIL_USER,
  MAIL_PASS: process.env.MAIL_PASS,
  MAIL_DEV_ACCEPT_ALL: process.env.MAIL_DEV_ACCEPT_ALL === 'true', // 开发占位：任意验证码通过

  // --- 自动注册默认 name（10.57）---
  // 微信：取微信昵称或 DEFAULT_NAME_WECHAT；手机：用户 + 手机后4位；邮箱：邮箱前缀或 DEFAULT_NAME_EMAIL
  DEFAULT_NAME_WECHAT: process.env.DEFAULT_NAME_WECHAT || '微信用户',
  DEFAULT_NAME_EMAIL: process.env.DEFAULT_NAME_EMAIL || '邮箱用户',

  // --- 雪花算法 uid（多实例部署时每实例配置不同 WORKER_ID）---
  SNOWFLAKE_WORKER_ID: process.env.SNOWFLAKE_WORKER_ID != null ? Number(process.env.SNOWFLAKE_WORKER_ID) : 0,
  SNOWFLAKE_DATACENTER_ID: process.env.SNOWFLAKE_DATACENTER_ID != null ? Number(process.env.SNOWFLAKE_DATACENTER_ID) : 0,
};
