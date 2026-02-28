/**
 * JoyTrunk 官方后端占位：全平台注册用户、JoyTrunk 即时通讯后端、LLM Router、计费与用量。
 * 本地管理后端（32890、负责人/员工/团队 CRUD、config/workspace）已迁移至 cli 包内 gateway，由 joytrunk server 启动。
 * 本服务为独立进程，端口由 PORT 或配置指定，与本地 32890 解耦。
 */

const express = require('express');
const cors = require('cors');

const app = express();
const PORT = Number(process.env.PORT) || 32891;
const HOST = process.env.HOST || 'localhost';

app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({
    ok: true,
    service: 'joytrunk-official',
    message: 'JoyTrunk 官方后端（注册用户、IM、LLM Router）开发中',
    port: PORT,
  });
});

app.get('/', (req, res) => {
  res.json({
    service: 'JoyTrunk 官方后端',
    docs: '本地管理请使用 joytrunk server 启动 cli 内 server，访问 http://localhost:32890',
  });
});

// 官网登录：手机验证码（占位实现，正式需对接短信与用户存储）
app.post('/api/auth/send-code', (req, res) => {
  const { phone } = req.body || {};
  if (!phone) return res.status(400).json({ error: '请提供手机号' });
  // 占位：不真实发短信，仅返回成功
  res.json({ ok: true, message: '验证码已发送（开发环境占位）' });
});

app.post('/api/auth/login-by-code', (req, res) => {
  const { phone, code } = req.body || {};
  if (!phone || !code) return res.status(400).json({ error: '请提供手机号和验证码' });
  // 占位：任意 6 位验证码即可通过，返回 mock token
  res.json({ token: `official-${phone}-${Date.now()}` });
});

// 云端 IM 会话与消息（占位实现）
app.get('/api/im/conversations', (req, res) => {
  // 占位：返回空列表，正式需按当前用户返回会话列表
  res.json([]);
});

app.get('/api/im/conversations/:id/messages', (req, res) => {
  res.json([]);
});

app.post('/api/im/conversations/:id/messages', (req, res) => {
  const { content } = req.body || {};
  const id = req.params.id;
  res.status(201).json({ id: String(Date.now()), role: 'user', content: content || '' });
});

if (require.main === module) {
  app.listen(PORT, HOST, () => {
    console.log(`JoyTrunk official backend (placeholder) on http://${HOST}:${PORT}`);
  });
}

module.exports = { app, PORT, HOST };
