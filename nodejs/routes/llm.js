/**
 * LLM Router 路由：POST /chat/completions，需鉴权；挂载在 /v1 下故完整 path 为 /v1/chat/completions。
 */
const express = require('express');
const llmController = require('../controllers/llmController');
const { authMiddleware } = require('../middleware/auth');

const router = express.Router({ mergeParams: true });

router.post('/chat/completions', authMiddleware, llmController.chatCompletions);

module.exports = router;
