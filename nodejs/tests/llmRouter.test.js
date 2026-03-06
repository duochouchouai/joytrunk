/**
 * LLM Router 集成测试：鉴权、请求体验证、无上游 503、mock 上游 200 与 usage 写入/聚合。
 * 使用与 im.test.js 相同的 TEST DB/Redis；通过清 require 缓存 + 设置 env 控制上游配置。
 */
require('dotenv').config();
if (process.env.TEST_DATABASE_URL) {
  process.env.DATABASE_URL = process.env.TEST_DATABASE_URL;
} else if (process.env.DATABASE_URL) {
  const u = process.env.DATABASE_URL;
  process.env.DATABASE_URL = u.replace(/\/([^/?]+)(\?.*)?$/, (_, _db, q) => '/joytrunk_test' + (q || ''));
} else {
  process.env.DATABASE_URL = 'postgres://postgres:postgres@localhost:5432/joytrunk_test';
}
if (!process.env.REDIS_URL && !process.env.REDIS_HOST) {
  const pw = process.env.REDIS_PASSWORD || '';
  process.env.REDIS_URL = pw ? `redis://:${encodeURIComponent(pw)}@localhost:6379` : 'redis://localhost:6379';
}
if (!process.env.NODE_ENV) process.env.NODE_ENV = 'development';

const { describe, it, before, after } = require('node:test');
const assert = require('node:assert');
const http = require('http');
const { initDb, getDb } = require('../db/pg');
const { initRedis } = require('../db/redis');

function request(port, method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: '127.0.0.1',
      port,
      path,
      method,
      headers: { 'Content-Type': 'application/json', ...headers },
    };
    const req = http.request(opts, (res) => {
      let data = '';
      res.on('data', (ch) => { data += ch; });
      res.on('end', () => {
        try {
          const json = data ? JSON.parse(data) : {};
          resolve({ status: res.statusCode, headers: res.headers, body: json });
        } catch {
          resolve({ status: res.statusCode, headers: res.headers, body: data });
        }
      });
    });
    req.on('error', reject);
    if (body != null) req.write(typeof body === 'string' ? body : JSON.stringify(body));
    req.end();
  });
}

function clearRouterCache() {
  delete require.cache[require.resolve('../server')];
  delete require.cache[require.resolve('../config/default.js')];
  delete require.cache[require.resolve('../services/llmRouter.js')];
  delete require.cache[require.resolve('../controllers/llmController.js')];
  delete require.cache[require.resolve('../routes/llm.js')];
}

describe('LLM Router (no upstream)', () => {
  let srv;
  let port;
  const req = (method, path, body, headers = {}) => request(port, method, path, body, headers);

  before(async () => {
    delete process.env.ROUTER_UPSTREAM_URL;
    delete process.env.MINIMAX_API_BASE;
    clearRouterCache();
    const { app, seedIfEmpty } = require('../server');
    await initDb();
    await initRedis();
    await seedIfEmpty();
    srv = app.listen(0, '127.0.0.1');
    await new Promise((r) => srv.once('listening', r));
    port = srv.address().port;
  });

  after(() => {
    if (srv) srv.close();
  });

  it('POST /v1/chat/completions returns 401 without auth', async () => {
    const res = await req('POST', '/v1/chat/completions', { messages: [{ role: 'user', content: 'hi' }] });
    assert.strictEqual(res.status, 401);
    assert.ok(res.body.error);
    assert.strictEqual(res.body.code, 'UNAUTHORIZED');
  });

  it('POST /v1/chat/completions returns 400 when messages missing', async () => {
    const res = await req('POST', '/v1/chat/completions', {}, { 'X-Owner-Id': '1' });
    assert.strictEqual(res.status, 400);
    assert.ok(res.body.error);
  });

  it('POST /v1/chat/completions returns 400 when messages not array', async () => {
    const res = await req('POST', '/v1/chat/completions', { messages: 'not-array' }, { 'X-Owner-Id': '1' });
    assert.strictEqual(res.status, 400);
    assert.ok(res.body.error);
  });

  it('POST /v1/chat/completions returns 503 when upstream not configured', async () => {
    const res = await req('POST', '/v1/chat/completions', { messages: [{ role: 'user', content: 'hi' }] }, { 'X-Owner-Id': '1' });
    assert.strictEqual(res.status, 503);
    assert.ok(res.body.error);
  });
});

describe('LLM Router (mock upstream)', () => {
  let appSrv;
  let mockSrv;
  let port;
  const req = (method, path, body, headers = {}) => request(port, method, path, body, headers);

  before(async () => {
    mockSrv = http.createServer((req, res) => {
      let body = '';
      req.on('data', (ch) => { body += ch; });
      req.on('end', () => {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            id: 'mock-id',
            choices: [{ message: { role: 'assistant', content: 'ok' }, finish_reason: 'stop' }],
            usage: { prompt_tokens: 2, completion_tokens: 3 },
          })
        );
      });
    });
    await new Promise((r) => {
      mockSrv.listen(0, '127.0.0.1', r);
    });
    const mockPort = mockSrv.address().port;
    process.env.ROUTER_UPSTREAM_URL = `http://127.0.0.1:${mockPort}`;
    clearRouterCache();
    const { app, seedIfEmpty } = require('../server');
    await initDb();
    await initRedis();
    await seedIfEmpty();
    const pool = getDb();
    await pool.query('DELETE FROM llm_usage');
    appSrv = app.listen(0, '127.0.0.1');
    await new Promise((r) => appSrv.once('listening', r));
    port = appSrv.address().port;
  });

  after(() => {
    if (appSrv) appSrv.close();
    if (mockSrv) mockSrv.close();
  });

  it('POST /v1/chat/completions returns 200 with choices and usage', async () => {
    const res = await req(
      'POST',
      '/v1/chat/completions',
      { messages: [{ role: 'user', content: 'hi' }] },
      { 'X-Owner-Id': '1' }
    );
    assert.strictEqual(res.status, 200);
    assert.ok(Array.isArray(res.body.choices));
    assert.ok(res.body.choices.length > 0);
    assert.ok(res.body.usage);
    assert.strictEqual(res.body.usage.prompt_tokens, 2);
    assert.strictEqual(res.body.usage.completion_tokens, 3);
  });

  it('getUsage aggregates router tokens after chat', async () => {
    await req(
      'POST',
      '/v1/chat/completions',
      { messages: [{ role: 'user', content: 'again' }] },
      { 'X-Owner-Id': '1' }
    );
    await new Promise((r) => setImmediate(r));
    await new Promise((r) => setTimeout(r, 80));
    const usageRes = await req('GET', '/api/users/me/usage', null, { 'X-Owner-Id': '1' });
    assert.strictEqual(usageRes.status, 200);
    assert.ok(Array.isArray(usageRes.body.usage));
    const router = usageRes.body.usage.find((u) => u.source === 'router');
    assert.ok(router);
    assert.ok(typeof router.tokens === 'number');
    assert.ok(router.tokens >= 5);
  });
});
