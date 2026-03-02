/**
 * IM 与认证接口测试（Phase 1 实现）
 * 使用 PostgreSQL 测试库 joytrunk_test，beforeEach 按外键顺序 TRUNCATE 清表。
 * 优先加载 .env，再设置测试用 DATABASE_URL：若已设 TEST_DATABASE_URL 则用其，否则由 DATABASE_URL 改为 joytrunk_test 库（同账号），否则默认 postgres:postgres@localhost/joytrunk_test。
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
// 测试环境允许邮箱验证码任意通过（未配置 MAIL_HOST 时），便于 login-by-email-code 用例
if (process.env.MAIL_DEV_ACCEPT_ALL === undefined) process.env.MAIL_DEV_ACCEPT_ALL = 'true';

const { describe, it, after, before, beforeEach } = require('node:test');
const assert = require('node:assert');
const http = require('http');
const { initDb, getDb } = require('../db/pg');
const { initRedis, getCode } = require('../db/redis');

const TRUNCATE_SQL = `
  TRUNCATE TABLE messages, user_conversation_status, participants, conversations, users
  RESTART IDENTITY CASCADE
`;

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

describe('IM & auth API', () => {
  const { app, seedIfEmpty } = require('../server');
  let srv;
  let port;
  let user2Uid;
  const req = (method, path, body, headers = {}) => request(port, method, path, body, headers);

  before(async () => {
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

  beforeEach(async () => {
    try {
      const pool = getDb();
      await pool.query(TRUNCATE_SQL);
      await seedIfEmpty();
      const uidRes = await pool.query('SELECT uid FROM users WHERE id = 2');
      user2Uid = uidRes.rows[0]?.uid ?? '';
    } catch (e) {
      console.error('beforeEach TRUNCATE/seed failed', e.message);
    }
  });

  describe('GET /api/health', () => {
    it('returns 200 with ok and service name', async () => {
      const res = await req('GET', '/api/health');
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.ok, true);
      assert.ok(res.body.service);
    });
  });

  describe('POST /api/auth/send-code', () => {
    it('returns 400 when phone missing', async () => {
      const res = await req('POST', '/api/auth/send-code', {});
      assert.strictEqual(res.status, 400);
      assert.ok(res.body.error);
    });
    it('returns 200 when phone provided', async () => {
      const res = await req('POST', '/api/auth/send-code', { phone: '13800138000' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.ok, true);
    });
    it('returns 429 when throttle (same phone within 60s)', async () => {
      await req('POST', '/api/auth/send-code', { phone: '13800138002' });
      const res = await req('POST', '/api/auth/send-code', { phone: '13800138002' });
      assert.strictEqual(res.status, 429);
      assert.ok(res.body.error);
    });
  });

  describe('POST /api/auth/login-by-code', () => {
    it('returns 400 when phone or code missing', async () => {
      const r1 = await req('POST', '/api/auth/login-by-code', {});
      assert.strictEqual(r1.status, 400);
      const r2 = await req('POST', '/api/auth/login-by-code', { phone: '13800138000' });
      assert.strictEqual(r2.status, 400);
    });
    it('returns 401 when code wrong or expired', async () => {
      const res = await req('POST', '/api/auth/login-by-code', { phone: '13800138999', code: '000000' });
      assert.strictEqual(res.status, 401);
      assert.ok(res.body.error);
    });
    it('returns 200 with token when phone and valid code', async () => {
      const phone = '13800138000';
      await req('POST', '/api/auth/send-code', { phone });
      const code = await getCode('phone', phone);
      assert.ok(code, 'Redis should have code after send-code');
      const res = await req('POST', '/api/auth/login-by-code', { phone, code });
      assert.strictEqual(res.status, 200);
      assert.ok(res.body.token);
      assert.ok(res.body.user);
      assert.strictEqual(typeof res.body.user.uid, 'string');
      assert.ok(res.body.user.uid.length > 0);
    });
  });

  describe('POST /api/auth/send-email-code', () => {
    it('returns 400 when email missing or invalid', async () => {
      const r1 = await req('POST', '/api/auth/send-email-code', {});
      assert.strictEqual(r1.status, 400);
      const r2 = await req('POST', '/api/auth/send-email-code', { email: 'not-an-email' });
      assert.strictEqual(r2.status, 400);
    });
    it('returns 200 when email provided', async () => {
      const res = await req('POST', '/api/auth/send-email-code', { email: 'a@b.com' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.ok, true);
    });
  });

  describe('POST /api/auth/login-by-email-code', () => {
    it('returns 400 when email or code missing', async () => {
      const r1 = await req('POST', '/api/auth/login-by-email-code', {});
      assert.strictEqual(r1.status, 400);
      const r2 = await req('POST', '/api/auth/login-by-email-code', { email: 'a@b.com' });
      assert.strictEqual(r2.status, 400);
    });
    it('returns 200 with token when email and code provided (auto register)', async () => {
      const res = await req('POST', '/api/auth/login-by-email-code', { email: 'new@test.com', code: '123456' });
      assert.strictEqual(res.status, 200);
      assert.ok(res.body.token);
      assert.ok(res.body.user);
      assert.strictEqual(typeof res.body.user.uid, 'string');
      assert.ok(res.body.user.uid.length > 0);
    });
  });

  describe('POST /api/auth/login-by-password', () => {
    it('returns 400 when account or password missing', async () => {
      const r1 = await req('POST', '/api/auth/login-by-password', {});
      assert.strictEqual(r1.status, 400);
      const r2 = await req('POST', '/api/auth/login-by-password', { account: '13800000001' });
      assert.strictEqual(r2.status, 400);
    });
    it('returns 401 when account has no password set', async () => {
      const res = await req('POST', '/api/auth/login-by-password', { account: '13800000001', password: 'abc123' });
      assert.strictEqual(res.status, 401);
    });
    it('returns 200 after set password and login by password', async () => {
      await req('PATCH', '/api/users/me/password', { password: 'pass1234' }, { 'X-Owner-Id': '1' });
      const res = await req('POST', '/api/auth/login-by-password', { account: '13800000001', password: 'pass1234' });
      assert.strictEqual(res.status, 200);
      assert.ok(res.body.token);
      assert.ok(res.body.user);
      assert.strictEqual(typeof res.body.user.uid, 'string');
      assert.ok(res.body.user.uid.length > 0);
    });
  });

  describe('PATCH /api/users/me/password', () => {
    it('returns 401 without auth', async () => {
      const res = await req('PATCH', '/api/users/me/password', { password: 'newpass123' });
      assert.strictEqual(res.status, 401);
    });
    it('returns 400 when password too short', async () => {
      const res = await req('PATCH', '/api/users/me/password', { password: '12345' }, { 'X-Owner-Id': '2' });
      assert.strictEqual(res.status, 400);
    });
    it('returns 200 when auth and password >= 6 (set password)', async () => {
      const res = await req('PATCH', '/api/users/me/password', { password: 'pass9999' }, { 'X-Owner-Id': '2' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.ok, true);
    });
    it('returns 401 when change password with wrong old_password', async () => {
      await req('PATCH', '/api/users/me/password', { password: 'pass1234' }, { 'X-Owner-Id': '1' });
      const res = await req('PATCH', '/api/users/me/password', { old_password: 'wrong', password: 'newpass66' }, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 401);
    });
    it('returns 200 when change password with correct old_password', async () => {
      await req('PATCH', '/api/users/me/password', { password: 'pass1234' }, { 'X-Owner-Id': '1' });
      const res = await req('PATCH', '/api/users/me/password', { old_password: 'pass1234', password: 'newpass66' }, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.ok, true);
    });
  });

  describe('POST /api/users/me/deactivate', () => {
    it('returns 401 without auth', async () => {
      const res = await req('POST', '/api/users/me/deactivate', {});
      assert.strictEqual(res.status, 401);
    });
    it('returns 200 and then 401 for deactivated user', async () => {
      const res = await req('POST', '/api/users/me/deactivate', {}, { 'X-Owner-Id': '2' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.ok, true);
      const meRes = await req('GET', '/api/users/me', null, { 'X-Owner-Id': '2' });
      assert.strictEqual(meRes.status, 401);
      assert.strictEqual(meRes.body.code, 'ACCOUNT_DEACTIVATED');
    });
  });

  describe('GET /api/im/conversations', () => {
    it('returns 401 without auth', async () => {
      const res = await req('GET', '/api/im/conversations');
      assert.strictEqual(res.status, 401);
    });
    it('returns 200 and array with X-Owner-Id', async () => {
      const res = await req('GET', '/api/im/conversations', null, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 200);
      assert.ok(Array.isArray(res.body));
    });
  });

  describe('POST /api/im/conversations', () => {
    it('returns 400 when type or peer_uid missing', async () => {
      const r1 = await req('POST', '/api/im/conversations', {}, { 'X-Owner-Id': '1' });
      assert.strictEqual(r1.status, 400);
      const r2 = await req('POST', '/api/im/conversations', { type: 'direct' }, { 'X-Owner-Id': '1' });
      assert.strictEqual(r2.status, 400);
    });
    it('returns 404 when peer_uid not found', async () => {
      const res = await req('POST', '/api/im/conversations', { type: 'direct', peer_uid: '1' }, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 404);
      assert.ok(res.body.error);
    });
    it('creates 1:1 and returns 201 with id', async () => {
      const res = await req('POST', '/api/im/conversations', { type: 'direct', peer_uid: user2Uid }, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 201);
      assert.ok(res.body.id);
    });
    it('B sees conversation and messages after A creates and sends', async () => {
      const createRes = await req('POST', '/api/im/conversations', { type: 'direct', peer_uid: user2Uid }, { 'X-Owner-Id': '1' });
      assert.strictEqual(createRes.status, 201, 'A creates conv with B');
      const convId = createRes.body.id;
      const sendRes = await req('POST', `/api/im/conversations/${convId}/messages`, { content: 'hello from A' }, { 'X-Owner-Id': '1' });
      assert.strictEqual(sendRes.status, 201, 'A sends message');
      const listRes = await req('GET', '/api/im/conversations', null, { 'X-Owner-Id': '2' });
      assert.strictEqual(listRes.status, 200, 'B lists conversations');
      assert.ok(Array.isArray(listRes.body), 'response is array');
      assert.strictEqual(listRes.body.length, 1, 'B sees exactly one conversation');
      assert.strictEqual(listRes.body[0].id, convId, 'B sees the same conversation');
      assert.ok(listRes.body[0].last_message, 'B sees last message preview');
      assert.strictEqual(listRes.body[0].last_message.content, 'hello from A', 'last message content');
      const msgRes = await req('GET', `/api/im/conversations/${convId}/messages`, null, { 'X-Owner-Id': '2' });
      assert.strictEqual(msgRes.status, 200, 'B can get messages');
      assert.strictEqual(msgRes.body.items.length, 1, 'B sees one message');
      assert.strictEqual(msgRes.body.items[0].content, 'hello from A', 'message content');
    });
  });

  describe('GET /api/im/conversations/:id/messages', () => {
    it('returns 200 with items, next_cursor, has_more, latest_msg_id', async () => {
      const createRes = await req('POST', '/api/im/conversations', { type: 'direct', peer_uid: user2Uid }, { 'X-Owner-Id': '1' });
      assert.strictEqual(createRes.status, 201);
      const convId = createRes.body.id;
      const res = await req('GET', `/api/im/conversations/${convId}/messages`, null, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 200);
      assert.ok(Array.isArray(res.body.items));
      assert.ok('next_cursor' in res.body);
      assert.strictEqual(typeof res.body.has_more, 'boolean', 'has_more is boolean');
      assert.ok(typeof res.body.latest_msg_id === 'number' || res.body.latest_msg_id === null, 'latest_msg_id is number or null');
    });
    it('returns has_more and latest_msg_id after sending message', async () => {
      const createRes = await req('POST', '/api/im/conversations', { type: 'direct', peer_uid: user2Uid }, { 'X-Owner-Id': '1' });
      const convId = createRes.body.id;
      await req('POST', `/api/im/conversations/${convId}/messages`, { content: 'msg1' }, { 'X-Owner-Id': '1' });
      const res = await req('GET', `/api/im/conversations/${convId}/messages`, null, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.items.length, 1);
      assert.strictEqual(res.body.latest_msg_id, res.body.items[0].id, 'latest_msg_id equals only message id');
      assert.strictEqual(res.body.has_more, false, 'one message so no more');
    });
  });

  describe('POST /api/im/conversations/:id/messages', () => {
    it('returns 201 with id and content', async () => {
      const createRes = await req('POST', '/api/im/conversations', { type: 'direct', peer_uid: user2Uid }, { 'X-Owner-Id': '1' });
      assert.strictEqual(createRes.status, 201);
      const convId = createRes.body.id;
      const res = await req('POST', `/api/im/conversations/${convId}/messages`, { content: 'hello' }, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 201);
      assert.ok(res.body.id);
      assert.strictEqual(res.body.content, 'hello');
    });
    it('returns 400 for empty content', async () => {
      const createRes = await req('POST', '/api/im/conversations', { type: 'direct', peer_uid: user2Uid }, { 'X-Owner-Id': '1' });
      const convId = createRes.body.id;
      const res = await req('POST', `/api/im/conversations/${convId}/messages`, {}, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 400);
    });
  });

  describe('GET /api/users/me', () => {
    it('returns 401 without auth', async () => {
      const res = await req('GET', '/api/users/me');
      assert.strictEqual(res.status, 401);
    });
    it('returns 200 with user when X-Owner-Id', async () => {
      const res = await req('GET', '/api/users/me', null, { 'X-Owner-Id': '1' });
      assert.strictEqual(res.status, 200);
      assert.strictEqual(res.body.id, 1);
      assert.ok(res.body.name);
      assert.strictEqual(typeof res.body.uid, 'string');
      assert.ok(res.body.uid.length > 0);
    });
  });
});
