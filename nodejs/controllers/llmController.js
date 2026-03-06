/**
 * LLM Router 控制层：POST /chat/completions，鉴权后调 llmRouter.routeChatCompletions，统一错误 JSON。
 */
const llmRouter = require('../services/llmRouter');

async function chatCompletions(req, res, next) {
  const requestId = req.headers['x-request-id'] || `req-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  const userId = req.ownerId;
  const body = req.body || {};
  try {
    const result = await llmRouter.routeChatCompletions(userId, body, requestId);
    if (result.error) {
      const status = result.status || 502;
      const payload = { error: result.error };
      if (result.code) payload.code = result.code;
      return res.status(status).json(payload);
    }
    return res.json(result.data);
  } catch (e) {
    next(e);
  }
}

module.exports = {
  chatCompletions,
};
