/**
 * LLM Router 服务层：鉴权后的 userId、请求体 → 校验、解析模型、调上游、写 llm_usage、返回 OpenAI 兼容 JSON。
 * 配置优先级：ROUTER_UPSTREAM_* 优先于 MINIMAX_*。
 */
const config = require('../config/default');
const { getDb } = require('../db/pg');

const MESSAGES_MAX_LENGTH = 100;
const SINGLE_CONTENT_MAX_CHARS = 65536;
const BODY_MAX_BYTES = 1024 * 1024; // 1MB

function getUpstreamConfig() {
  const base = config.ROUTER_UPSTREAM_URL || config.MINIMAX_API_BASE;
  const key = config.ROUTER_UPSTREAM_KEY || config.MINIMAX_API_KEY;
  return { base: base ? String(base).trim() : null, key: key ? String(key).trim() : '' };
}

function resolveModel(bodyModel) {
  const defaultModel = config.ROUTER_DEFAULT_MODEL || 'MINIMAX-M2.1';
  const allowed = config.ROUTER_ALLOWED_MODELS;
  const useModel =
    bodyModel && typeof bodyModel === 'string' && allowed && Array.isArray(allowed) && allowed.includes(bodyModel.trim())
      ? bodyModel.trim()
      : defaultModel;
  const map = config.ROUTER_MODEL_MAP;
  if (map && typeof map === 'object' && map[useModel]) {
    return map[useModel];
  }
  return useModel;
}

function validateBody(body) {
  if (!body || typeof body !== 'object') {
    return { error: '请求体无效', status: 400 };
  }
  const messages = body.messages;
  if (!Array.isArray(messages)) {
    return { error: 'messages 必须为数组', status: 400 };
  }
  if (messages.length > MESSAGES_MAX_LENGTH) {
    return { error: `messages 长度不能超过 ${MESSAGES_MAX_LENGTH}`, status: 400 };
  }
  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i];
    if (msg && typeof msg === 'object' && msg.content != null) {
      const content = typeof msg.content === 'string' ? msg.content : String(msg.content);
      if (content.length > SINGLE_CONTENT_MAX_CHARS) {
        return { error: `messages[${i}].content 长度不能超过 ${SINGLE_CONTENT_MAX_CHARS} 字符`, status: 400 };
      }
    }
  }
  return null;
}

async function getUidByUserId(userId) {
  if (userId == null) return null;
  try {
    const pool = getDb();
    const result = await pool.query('SELECT uid FROM users WHERE id = $1 AND deleted_at IS NULL', [Number(userId)]);
    const row = result.rows[0];
    return row && row.uid != null ? row.uid : null;
  } catch (e) {
    console.warn('[llmRouter] getUidByUserId failed', userId, e?.message);
    return null;
  }
}

async function insertLlmUsage(uid, source, model, promptTokens, completionTokens) {
  if (uid == null) return;
  try {
    const pool = getDb();
    await pool.query(
      'INSERT INTO llm_usage (uid, source, model, prompt_tokens, completion_tokens) VALUES ($1, $2, $3, $4, $5)',
      [Number(uid), source || 'router', model || null, Math.max(0, parseInt(promptTokens, 10) || 0), Math.max(0, parseInt(completionTokens, 10) || 0)]
    );
  } catch (e) {
    console.warn('[llmRouter] insertLlmUsage failed', 'uid=', uid, e?.message);
  }
}

const UPSTREAM_TIMEOUT_MS = config.ROUTER_UPSTREAM_TIMEOUT_MS || 60000;
const RETRY_DELAY_MS = 2000;

async function callUpstream(url, apiKey, body, requestId) {
  const controller = new AbortController();
  const to = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS);
  const headers = {
    'Content-Type': 'application/json',
    ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
  };
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(to);
    const text = await res.text();
    if (res.status === 401) {
      return { error: '上游鉴权失败', code: 'UPSTREAM_AUTH', status: 502 };
    }
    if (res.status === 429) {
      return { error: '上游限流', code: 'UPSTREAM_RATE_LIMIT', status: 503 };
    }
    if (!res.ok) {
      return { error: text || '上游服务异常', code: 'UPSTREAM_ERROR', status: 502 };
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return { error: '上游返回非 JSON', code: 'UPSTREAM_INVALID', status: 502 };
    }
    return { data };
  } catch (e) {
    clearTimeout(to);
    if (e.name === 'AbortError') {
      return { error: '上游请求超时', code: 'UPSTREAM_TIMEOUT', status: 502 };
    }
    return { error: e.message || '上游服务异常', code: 'UPSTREAM_ERROR', status: 502 };
  }
}

async function routeChatCompletions(userId, body, requestId) {
  const validation = validateBody(body);
  if (validation) return validation;

  const { base, key } = getUpstreamConfig();
  if (!base || !base.startsWith('http')) {
    return { error: 'Router 上游未配置，请设置 ROUTER_UPSTREAM_URL 或 MINIMAX_API_BASE', status: 503 };
  }

  const model = resolveModel(body.model);
  const requestBody = { ...body, model };

  const url = base.replace(/\/$/, '') + '/chat/completions';

  let result = await callUpstream(url, key, requestBody, requestId);
  if (result.status === 502 || result.status === 503) {
    const isRetryable = result.status === 502 && result.code !== 'UPSTREAM_AUTH' && result.code !== 'UPSTREAM_INVALID';
    if (isRetryable) {
      await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
      result = await callUpstream(url, key, requestBody, requestId);
    }
  }

  if (result.error) {
    return { error: result.error, code: result.code, status: result.status };
  }

  const { data } = result;
  const usage = data && data.usage;
  const promptTokens = usage && usage.prompt_tokens != null ? usage.prompt_tokens : 0;
  const completionTokens = usage && usage.completion_tokens != null ? usage.completion_tokens : 0;

  getUidByUserId(userId).then((uid) => {
    if (uid != null) {
      setImmediate(() => {
        insertLlmUsage(uid, 'router', model, promptTokens, completionTokens).catch((e) => {
          console.warn('[llmRouter] async insertLlmUsage', e?.message);
        });
      });
    } else {
      console.warn('[llmRouter] uid missing for userId=', userId);
    }
  });

  return { data };
}

module.exports = {
  routeChatCompletions,
  validateBody,
  getUpstreamConfig,
  resolveModel,
  getUidByUserId,
  insertLlmUsage,
  MESSAGES_MAX_LENGTH,
  SINGLE_CONTENT_MAX_CHARS,
  BODY_MAX_BYTES,
};
