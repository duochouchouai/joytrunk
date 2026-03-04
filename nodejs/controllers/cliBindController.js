/**
 * CLI 绑定控制层：start、poll、confirm（joytrunk bind）
 */
const cliBindService = require('../services/cliBind');

async function start(req, res, next) {
  try {
    const body = req.body || {};
    const result = await cliBindService.startBind(body);
    if (result.error) {
      return res.status(result.status || 500).json({ error: result.error, code: result.code });
    }
    res.status(201).json(result);
  } catch (e) {
    next(e);
  }
}

async function poll(req, res, next) {
  try {
    const code = req.query.code;
    const result = await cliBindService.pollBind(code);
    if (result.error) {
      return res.status(result.status || 500).json({ error: result.error, code: result.code });
    }
    res.json(result);
  } catch (e) {
    next(e);
  }
}

async function confirm(req, res, next) {
  try {
    const { code } = req.body || {};
    const result = await cliBindService.confirmBind(req.ownerId, code);
    if (result.error) {
      return res.status(result.status || 500).json({ error: result.error, code: result.code });
    }
    res.json(result);
  } catch (e) {
    next(e);
  }
}

module.exports = { start, poll, confirm };
