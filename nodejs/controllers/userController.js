/**
 * 用户控制层：解析请求、调用用户服务、写响应（计划 5.7）
 */
const userService = require('../services/user');
const authService = require('../services/auth');

async function getMe(req, res, next) {
  try {
    const result = await userService.getMe(req.ownerId);
    if (result.error) {
      return res.status(result.status).json({ error: result.error });
    }
    res.json(result);
  } catch (e) {
    next(e);
  }
}

async function updatePassword(req, res, next) {
  try {
    const { old_password, password } = req.body || {};
    const result =
      old_password !== undefined && old_password !== ''
        ? await authService.changePassword(req.ownerId, old_password, password)
        : await authService.setPassword(req.ownerId, password);
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json({ ok: true });
  } catch (e) {
    next(e);
  }
}

async function deactivate(req, res, next) {
  try {
    const result = await authService.deactivate(req.ownerId);
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json({ ok: true });
  } catch (e) {
    next(e);
  }
}

async function updateMe(req, res, next) {
  try {
    const { name, avatar_url, sync_joytrunk_chat } = req.body || {};
    const result = await userService.updateMe(req.ownerId, { name, avatar_url, sync_joytrunk_chat });
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json(result);
  } catch (e) {
    next(e);
  }
}

async function generateApiKey(req, res, next) {
  try {
    const result = await userService.generateApiKey(req.ownerId);
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json(result);
  } catch (e) {
    next(e);
  }
}

async function getUsage(req, res, next) {
  try {
    const result = await userService.getUsage(req.ownerId);
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.json(result);
  } catch (e) {
    next(e);
  }
}

module.exports = { getMe, updatePassword, deactivate, updateMe, generateApiKey, getUsage };
