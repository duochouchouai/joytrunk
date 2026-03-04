/**
 * CLI 绑定路由：/api/cli/bind/start、poll、confirm（joytrunk bind 流程）
 * start、poll 无需登录；confirm 需 authMiddleware。
 */
const express = require('express');
const cliBindController = require('../controllers/cliBindController');
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

module.exports = router;
