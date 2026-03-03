/**
 * IM 路由层：仅绑定路径与 IM 控制层（计划 5.2、5.7）
 * 需 auth 中间件注入 req.ownerId。
 */
const express = require('express');
const imController = require('../controllers/imController');

const router = express.Router();

router.get('/conversations', imController.listConversations);
router.post('/conversations', imController.createConversation);
router.get('/conversations/:id/participants', imController.getParticipants);
router.post('/conversations/:id/participants', imController.addParticipants);
router.delete('/conversations/:id/participants/:userId', imController.removeParticipant);
router.patch('/conversations/:id/participants/:userId', imController.updateParticipant);
router.patch('/conversations/:id', imController.updateConversation);
router.post('/conversations/:id/leave', imController.leaveConversation);
router.patch('/conversations/:id/read', imController.markConversationRead);
router.post('/conversations/:id/dismiss', imController.dismissConversation);
router.get('/conversations/:id/messages', imController.getMessages);
router.post('/conversations/:id/messages', imController.sendMessage);

module.exports = router;
