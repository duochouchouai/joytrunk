/**
 * CLI 绑定路由：/api/cli/bind/start、poll、confirm（joytrunk bind 流程）
 * start、poll 无需登录；confirm 需 authMiddleware。
 */
const express = require('express');
const cliBindController = require('../controllers/cliBindController');
const cliEmployees = require('../services/cliEmployees');
const { authMiddleware } = require('../middleware/auth');

const router = express.Router();

// 浏览器 GET /bind/start 时返回 405，提示用 joytrunk bind（POST）
router.get('/bind/start', (req, res) => {
  res.set('Allow', 'POST');
  res.status(405).json({
    error: '此接口仅接受 POST',
    hint: '请在终端执行 joytrunk bind，不要直接在浏览器打开此地址。',
  });
});
router.post('/bind/start', cliBindController.start);
router.get('/bind/poll', cliBindController.poll);
router.post('/bind/confirm', authMiddleware, cliBindController.confirm);

/** 当前用户已同步的 CLI 员工列表（IM 用于选择员工下发任务） */
router.get('/employees', authMiddleware, async (req, res) => {
  try {
    const list = await cliEmployees.getCliEmployees(req.ownerId);
    res.json({ employees: list });
  } catch (e) {
    console.error('GET /api/cli/employees', e);
    res.status(500).json({ error: '服务器错误' });
  }
});

module.exports = router;
