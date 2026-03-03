/**
 * 认证控制层：解析请求、调用认证服务、写响应（计划 5.7）
 */
const authService = require('../services/auth');

async function sendCode(req, res, next) {
  try {
    const { phone } = req.body || {};
    const result = await authService.sendCode(phone);
    if (result.error) return res.status(result.status).json({ error: result.error });
    const body = { ok: result.ok, message: result.message };
    if (result.sent !== undefined) body.sent = result.sent;
    res.json(body);
  } catch (e) {
    next(e);
  }
}

async function sendEmailCode(req, res, next) {
  try {
    const { email } = req.body || {};
    const result = await authService.sendEmailCode(email);
    if (result.error) return res.status(result.status).json({ error: result.error });
    const body = { ok: result.ok, message: result.message };
    if (result.sent !== undefined) body.sent = result.sent;
    res.json(body);
  } catch (e) {
    next(e);
  }
}

async function loginByCode(req, res, next) {
  try {
    const { phone, code } = req.body || {};
    const result = await authService.loginByCode(phone, code);
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json({ token: result.token, user: result.user });
  } catch (e) {
    next(e);
  }
}

async function loginByEmailCode(req, res, next) {
  try {
    const { email, code } = req.body || {};
    const result = await authService.loginByEmailCode(email, code);
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json({ token: result.token, user: result.user });
  } catch (e) {
    next(e);
  }
}

async function loginByPassword(req, res, next) {
  try {
    const { account, password } = req.body || {};
    const result = await authService.loginByPassword(account, password);
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json({ token: result.token, user: result.user });
  } catch (e) {
    next(e);
  }
}

module.exports = {
  sendCode,
  sendEmailCode,
  loginByCode,
  loginByEmailCode,
  loginByPassword,
};
