/**
 * 认证服务层：发送验证码、手机/邮箱验证码登录、账号密码登录、设置密码（计划 5.3、10.57）
 * 自动注册默认 name：手机取「用户」+ 手机后4位；邮箱取前缀或 DEFAULT_NAME_EMAIL。
 * 验证码存 Redis，节流与写码原子化；短信走阿里云，邮件走 SMTP。
 */
const crypto = require('crypto');
const { getDb } = require('../db/pg');
const { trySetThrottleAndCode, getCode, delCode } = require('../db/redis');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const config = require('../config/default');
const { generateUid } = require('../utils/snowflake');

const SALT_ROUNDS = 10;

/** 手机号简单校验：11 位 1 开头 */
const PHONE_REG = /^1\d{10}$/;

function generateCode() {
  return String(crypto.randomInt(100000, 999999));
}

async function sendCode(phone) {
  const p = typeof phone === 'string' ? phone.trim() : '';
  if (!p) return { error: '请提供手机号', status: 400 };
  if (!PHONE_REG.test(p)) return { error: '手机号格式无效', status: 400 };

  const code = generateCode();
  const throttleSec = config.CODE_THROTTLE_SECONDS ?? 60;
  const expireSec = config.CODE_EXPIRE_SECONDS ?? 300;
  const written = await trySetThrottleAndCode('phone', p, code, throttleSec, expireSec);
  if (!written) return { error: '请稍后再试', status: 429 };

  let sent = false;
  try {
    const sms = require('./sms');
    const result = await sms.sendVerificationSms(p, code);
    sent = result === true;
  } catch (e) {
    if (config.NODE_ENV !== 'production') console.log('SMS code (dev):', code);
  }
  if (!sent && config.NODE_ENV !== 'production') console.log('SMS code (dev):', code);
  return { ok: true, message: '验证码已发送', sent };
}

async function sendEmailCode(email) {
  const e = typeof email === 'string' ? email.trim().toLowerCase() : '';
  if (!e) return { error: '请提供邮箱', status: 400 };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) return { error: '邮箱格式无效', status: 400 };

  const code = generateCode();
  const throttleSec = config.CODE_THROTTLE_SECONDS ?? 60;
  const expireSec = config.CODE_EXPIRE_SECONDS ?? 300;
  const written = await trySetThrottleAndCode('email', e, code, throttleSec, expireSec);
  if (!written) return { error: '请稍后再试', status: 429 };

  let sent = false;
  try {
    const mail = require('./mail');
    const result = await mail.sendVerificationEmail(e, code);
    sent = result === true;
  } catch (err) {
    if (config.NODE_ENV !== 'production') console.log('Email code (dev):', code);
  }
  if (!sent && config.NODE_ENV !== 'production') console.log('Email code (dev):', code);
  return { ok: true, message: '验证码已发送', sent };
}

async function loginByCode(phone, code) {
  const p = typeof phone === 'string' ? phone.trim() : '';
  const c = typeof code === 'string' ? code.trim() : '';
  if (!p || !c) return { error: '请提供手机号和验证码', status: 400 };
  if (!PHONE_REG.test(p)) return { error: '手机号格式无效', status: 400 };

  const stored = await getCode('phone', p);
  if (stored == null || stored !== c) return { error: '验证码错误或已过期', status: 401 };
  await delCode('phone', p).catch((err) => {
    console.error('Redis delCode phone failed:', err?.code || err?.message);
  });

  const pool = getDb();
  let result = await pool.query('SELECT id, name, deleted_at, uid FROM users WHERE phone = $1', [p]);
  let user = result.rows[0] ?? null;
  if (!user) {
    const name = `用户${p.slice(-4)}`;
    const uid = generateUid();
    await pool.query('INSERT INTO users (type, name, phone, uid) VALUES ($1, $2, $3, $4)', ['user', name, p, uid]);
    result = await pool.query('SELECT id, name, deleted_at, uid FROM users WHERE phone = $1', [p]);
    user = result.rows[0] ?? null;
  }
  if (!user) return { error: '用户创建失败', status: 500 };
  if (user.deleted_at != null) return { error: '账号已注销', status: 403 };

  const token = signToken(user.id);
  return { token, user: { id: user.id, name: user.name, uid: user.uid != null ? String(user.uid) : undefined } };
}

async function loginByEmailCode(email, code) {
  const e = typeof email === 'string' ? email.trim().toLowerCase() : '';
  const c = typeof code === 'string' ? code.trim() : '';
  if (!e || !c) return { error: '请提供邮箱和验证码', status: 400 };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) return { error: '邮箱格式无效', status: 400 };

  const devAcceptAll = config.MAIL_DEV_ACCEPT_ALL && !config.MAIL_HOST;
  if (!devAcceptAll) {
    const stored = await getCode('email', e);
    if (stored == null || stored !== c) return { error: '验证码错误或已过期', status: 401 };
    await delCode('email', e).catch((err) => {
      console.error('Redis delCode email failed:', err?.code || err?.message);
    });
  }

  const pool = getDb();
  let result = await pool.query('SELECT id, name, deleted_at, uid FROM users WHERE email = $1', [e]);
  let user = result.rows[0] ?? null;
  if (!user) {
    const name = config.DEFAULT_NAME_EMAIL && config.DEFAULT_NAME_EMAIL !== '邮箱用户'
      ? config.DEFAULT_NAME_EMAIL
      : e.split('@')[0] || '邮箱用户';
    const uid = generateUid();
    await pool.query('INSERT INTO users (type, name, email, uid) VALUES ($1, $2, $3, $4)', ['user', name, e, uid]);
    result = await pool.query('SELECT id, name, deleted_at, uid FROM users WHERE email = $1', [e]);
    user = result.rows[0] ?? null;
  }
  if (!user) return { error: '用户创建失败', status: 500 };
  if (user.deleted_at != null) return { error: '账号已注销', status: 403 };

  const token = signToken(user.id);
  return { token, user: { id: user.id, name: user.name, uid: user.uid != null ? String(user.uid) : undefined } };
}

async function loginByPassword(account, password) {
  const a = typeof account === 'string' ? account.trim() : '';
  const pwd = typeof password === 'string' ? password : '';
  if (!a || !pwd) return { error: '请提供账号和密码', status: 400 };

  const pool = getDb();
  const email = a.includes('@') ? a.toLowerCase() : null;
  const result = email
    ? await pool.query('SELECT id, name, password_hash, deleted_at, uid FROM users WHERE email = $1', [email])
    : await pool.query('SELECT id, name, password_hash, deleted_at, uid FROM users WHERE phone = $1', [a]);
  const user = result.rows[0] ?? null;

  if (!user) return { error: '账号不存在或密码错误', status: 401 };
  if (user.deleted_at != null) return { error: '账号已注销', status: 403 };
  if (!user.password_hash) return { error: '该账号未设置密码，请使用验证码登录', status: 401 };

  const ok = bcrypt.compareSync(pwd, user.password_hash);
  if (!ok) return { error: '账号不存在或密码错误', status: 401 };

  const token = signToken(user.id);
  return { token, user: { id: user.id, name: user.name, uid: user.uid != null ? String(user.uid) : undefined } };
}

async function setPassword(userId, newPassword) {
  if (userId == null) return { error: '未登录', status: 401 };
  const pwd = typeof newPassword === 'string' ? newPassword : '';
  if (pwd.length < 6) return { error: '密码至少 6 位', status: 400 };

  const pool = getDb();
  const result = await pool.query('SELECT id, deleted_at FROM users WHERE id = $1', [Number(userId)]);
  const user = result.rows[0] ?? null;
  if (!user) return { error: '用户不存在', status: 404 };
  if (user.deleted_at != null) return { error: '账号已注销', status: 403 };

  const hash = bcrypt.hashSync(pwd, SALT_ROUNDS);
  await pool.query('UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2', [hash, userId]);
  return { ok: true };
}

async function changePassword(userId, oldPassword, newPassword) {
  if (userId == null) return { error: '未登录', status: 401 };
  const newPwd = typeof newPassword === 'string' ? newPassword : '';
  if (newPwd.length < 6) return { error: '新密码至少 6 位', status: 400 };

  const pool = getDb();
  const result = await pool.query('SELECT id, password_hash, deleted_at FROM users WHERE id = $1', [Number(userId)]);
  const user = result.rows[0] ?? null;
  if (!user) return { error: '用户不存在', status: 404 };
  if (user.deleted_at != null) return { error: '账号已注销', status: 403 };
  if (!user.password_hash) return { error: '账号未设置密码，请使用设置密码接口', status: 400 };

  const oldPwd = typeof oldPassword === 'string' ? oldPassword : '';
  if (!oldPwd) return { error: '请提供原密码', status: 400 };
  if (!bcrypt.compareSync(oldPwd, user.password_hash)) return { error: '原密码错误', status: 401 };

  const hash = bcrypt.hashSync(newPwd, SALT_ROUNDS);
  await pool.query('UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2', [hash, userId]);
  return { ok: true };
}

async function deactivate(userId) {
  if (userId == null) return { error: '未登录', status: 401 };
  const pool = getDb();
  const result = await pool.query('SELECT id, deleted_at FROM users WHERE id = $1', [Number(userId)]);
  const user = result.rows[0] ?? null;
  if (!user) return { error: '用户不存在', status: 404 };
  if (user.deleted_at != null) return { error: '账号已注销', status: 400 };
  await pool.query('UPDATE users SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = $1', [userId]);
  return { ok: true };
}

function signToken(userId) {
  return jwt.sign(
    { sub: userId, iat: Math.floor(Date.now() / 1000) },
    config.JWT_SECRET,
    { algorithm: config.JWT_ALGORITHM, expiresIn: config.JWT_EXPIRES_IN }
  );
}

module.exports = {
  sendCode,
  sendEmailCode,
  loginByCode,
  loginByEmailCode,
  loginByPassword,
  setPassword,
  changePassword,
  deactivate,
};
