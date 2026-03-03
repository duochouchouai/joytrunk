/**
 * 用户路由层：仅绑定路径与用户控制层（计划 5.7）
 * 需 auth 中间件注入 req.ownerId。
 */
const express = require('express');
const userController = require('../controllers/userController');

const router = express.Router();

router.get('/me', userController.getMe);
router.patch('/me/password', userController.updatePassword);
router.post('/me/deactivate', userController.deactivate);

module.exports = router;
