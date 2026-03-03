/**
 * Node 内置 test runner：官方后端占位健康检查
 * 不依赖数据库；若需带 DB 的测试见 im.test.js。
 */
require('dotenv').config();
if (!process.env.NODE_ENV) process.env.NODE_ENV = 'development';

const { describe, it } = require('node:test');
const assert = require('node:assert');
const http = require('http');

describe('official backend', () => {
  it('GET /api/health returns ok and service name', (t, done) => {
    const { app } = require('../server');
    const srv = app.listen(0, '127.0.0.1', () => {
      const port = srv.address().port;
      http.get(`http://127.0.0.1:${port}/api/health`, (res) => {
        let data = '';
        res.on('data', (ch) => { data += ch; });
        res.on('end', () => {
          srv.close();
          try {
            const body = JSON.parse(data);
            assert.strictEqual(body.ok, true);
            assert.ok(body.service);
            done();
          } catch (e) {
            done(e);
          }
        });
      }).on('error', done);
    });
  });
});
