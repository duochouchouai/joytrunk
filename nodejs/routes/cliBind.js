/**
 * CLI 绑定路由：/api/cli/bind/start、poll、confirm（joytrunk bind 流程）
 * start、poll 无需登录；confirm 需 authMiddleware。
 */
const express = require('express');
const cliBindController = require('../controllers/cliBindController');
const { authMiddleware } = require('../middleware/auth');

const router = express.Router();

router.post('/bind/start', cliBindController.start);
router.get('/bind/poll', cliBindController.poll);
router.post('/bind/confirm', authMiddleware, cliBindController.confirm);

module.exports = router;
