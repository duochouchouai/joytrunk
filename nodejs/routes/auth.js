/**
 * 认证路由层：仅绑定路径与认证控制层（计划 5.7、5.3）
 */
const express = require('express');
const authController = require('../controllers/authController');

const router = express.Router();

router.post('/send-code', authController.sendCode);
router.post('/send-email-code', authController.sendEmailCode);
router.post('/login-by-code', authController.loginByCode);
router.post('/login-by-email-code', authController.loginByEmailCode);
router.post('/login-by-password', authController.loginByPassword);

module.exports = router;
