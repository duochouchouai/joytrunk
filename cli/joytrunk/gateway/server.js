/**
 * JoyTrunk 本地管理后端（cli 内）：监听 32890，提供负责人/员工/团队 CRUD、config/workspace、agent 与 API。
 * 由 joytrunk gateway 启动；静态资源来自同目录下 static/（由 cli/joytrunk/ui 构建产出）。
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { getEmployeeDir } = require('./lib/paths');
const store = require('./lib/store');
const config = require('./lib/config');
const agent = require('./lib/agent');
const { copyTemplatesToEmployee } = require('./lib/employeeWorkspace');
const employeeConfig = require('./lib/employeeConfig');

const app = express();
const cfg = config.loadConfig();
const PORT = Number(process.env.PORT) || (cfg.gateway && cfg.gateway.port) || 32890;
const HOST = (cfg.gateway && cfg.gateway.host) || 'localhost';

app.use(cors());
app.use(express.json());

/** 当前负责人 ID：无 header 时使用本地默认负责人（自动创建若不存在），用户默认即可用、无需登录；登录仅用于即时通讯绑定。 */
function getOwnerId(req) {
  const headerId = req.headers['x-owner-id'] || req.headers['authorization'] || null;
  if (headerId) return headerId;
  const c = config.loadConfig();
  if (c.ownerId) return c.ownerId;
  const owners = store.getOwners();
  if (owners.length === 0) {
    const owner = store.createOwner({ name: '本地负责人', email: null });
    config.setOwnerInConfig(owner.id);
    return owner.id;
  }
  return owners[0].id;
}

// ---------- 健康检查 ----------
app.get('/api/health', (req, res) => {
  res.json({
    ok: true,
    service: 'joytrunk-gateway',
    port: PORT,
  });
});

// ---------- 认证（MVP：注册即创建负责人，登录即返回 ownerId）----------
app.post('/api/auth/register', (req, res) => {
  const { name, email } = req.body || {};
  const owners = store.getOwners();
  if (owners.length > 0) {
    return res.status(400).json({ error: '本地已存在负责人，请直接使用 X-Owner-Id 头或登录' });
  }
  const owner = store.createOwner({ name, email });
  config.setOwnerInConfig(owner.id);
  res.status(201).json({ owner, token: owner.id });
});

app.post('/api/auth/login', (req, res) => {
  const owners = store.getOwners();
  if (owners.length === 0) {
    return res.status(404).json({ error: '尚未注册负责人，请先 POST /api/auth/register' });
  }
  const owner = owners[0];
  res.json({ owner, token: owner.id });
});

// ---------- 当前负责人 ----------
app.get('/api/owners/me', (req, res) => {
  const ownerId = getOwnerId(req);
  const owner = store.findOwnerById(ownerId);
  if (!owner) return res.status(404).json({ error: '负责人不存在' });
  res.json(owner);
});

// ---------- 员工 CRUD（仅当前负责人的员工）----------
app.get('/api/employees', (req, res) => {
  const ownerId = getOwnerId(req);
  const list = store.getEmployeesByOwnerId(ownerId);
  res.json(list);
});

app.post('/api/employees', (req, res) => {
  const ownerId = getOwnerId(req);
  const employee = store.createEmployee(ownerId, req.body || {});
  const dir = getEmployeeDir(employee.id);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(path.join(dir, 'memory'), { recursive: true });
    fs.mkdirSync(path.join(dir, 'skills'), { recursive: true });
  }
  copyTemplatesToEmployee(employee.id);
  employeeConfig.ensureEmployeeConfigExists(employee.id);
  res.status(201).json(employee);
});

app.get('/api/employees/:id', (req, res) => {
  const ownerId = getOwnerId(req);
  const emp = store.findEmployeeById(req.params.id);
  if (!emp || emp.ownerId !== ownerId) return res.status(404).json({ error: '员工不存在' });
  res.json(emp);
});

app.patch('/api/employees/:id', (req, res) => {
  const ownerId = getOwnerId(req);
  const updated = store.updateEmployee(req.params.id, ownerId, req.body || {});
  if (!updated) return res.status(404).json({ error: '员工不存在' });
  res.json(updated);
});

// ---------- 员工级 config（覆盖主 config，仅 agents / providers）----------
app.get('/api/employees/:id/config', (req, res) => {
  const ownerId = getOwnerId(req);
  const emp = store.findEmployeeById(req.params.id);
  if (!emp || emp.ownerId !== ownerId) return res.status(404).json({ error: '员工不存在' });
  const data = employeeConfig.loadEmployeeConfig(req.params.id) || {};
  const out = { ...data };
  if (out.providers && out.providers.custom && out.providers.custom.apiKey) {
    out.providers = { ...out.providers, custom: { ...out.providers.custom, apiKey: '***' } };
  }
  res.json(out);
});

app.patch('/api/employees/:id/config', (req, res) => {
  const ownerId = getOwnerId(req);
  const emp = store.findEmployeeById(req.params.id);
  if (!emp || emp.ownerId !== ownerId) return res.status(404).json({ error: '员工不存在' });
  employeeConfig.saveEmployeeConfig(req.params.id, req.body || {});
  const data = employeeConfig.loadEmployeeConfig(req.params.id) || {};
  const out = { ...data };
  if (out.providers && out.providers.custom && out.providers.custom.apiKey) {
    out.providers = { ...out.providers, custom: { ...out.providers.custom, apiKey: '***' } };
  }
  res.json(out);
});

// ---------- 单通道消息：与员工对话（agent 调度 + 员工生存法则）----------
app.post('/api/employees/:id/chat', async (req, res) => {
  const ownerId = getOwnerId(req);
  const emp = store.findEmployeeById(req.params.id);
  if (!emp || emp.ownerId !== ownerId) return res.status(404).json({ error: '员工不存在' });
  const content = (req.body && req.body.content) || '';
  try {
    const result = await agent.reply(emp, ownerId, content, () => config.loadConfig());
    res.json({ reply: result.reply, usage: result.usage || null });
  } catch (e) {
    res.status(500).json({ error: e.message || '对话失败' });
  }
});

// ---------- JoyTrunk Router 代理（未配置自有 LLM 时 CLI/前端通过此端点调用大模型）----------
app.post('/api/llm/chat/completions', async (req, res) => {
  const routerUrl = process.env.JOYTRUNK_ROUTER_URL || (config.loadConfig().providers && config.loadConfig().providers.joytrunk && config.loadConfig().providers.joytrunk.apiBase);
  if (!routerUrl || typeof routerUrl !== 'string' || !routerUrl.trim()) {
    return res.status(503).json({
      error: 'JoyTrunk Router 未配置。请设置环境变量 JOYTRUNK_ROUTER_URL 或在配置中设置 providers.joytrunk.apiBase，或使用自有 LLM。',
    });
  }
  const ownerId = req.headers['x-owner-id'] || req.headers['authorization'] || config.loadConfig().ownerId;
  const url = routerUrl.replace(/\/$/, '') + '/chat/completions';
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(ownerId ? { 'X-Owner-Id': ownerId } : {}),
      },
      body: JSON.stringify(req.body || {}),
    });
    const text = await resp.text();
    if (!resp.ok) {
      return res.status(resp.status).json({ error: text || 'Router 请求失败' });
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return res.status(502).json({ error: 'Router 返回非 JSON' });
    }
    res.json(data);
  } catch (e) {
    res.status(502).json({ error: e.message || '转发 JoyTrunk Router 失败' });
  }
});

// ---------- 团队（负责人 + 全体员工）----------
app.get('/api/teams/current', (req, res) => {
  const ownerId = getOwnerId(req);
  const owner = store.findOwnerById(ownerId);
  if (!owner) return res.status(404).json({ error: '负责人不存在' });
  const employees = store.getEmployeesByOwnerId(ownerId);
  res.json({ owner, employees });
});

// ---------- 配置（只读，新 schema；对前端兼容提供 customLLM = providers.custom 脱敏）----------
app.get('/api/config', (req, res) => {
  const c = config.loadConfig();
  const out = { ...c };
  if (out.providers && out.providers.custom && out.providers.custom.apiKey) {
    out.providers = { ...out.providers, custom: { ...out.providers.custom, apiKey: '***' } };
  }
  if (out.customLLM && out.customLLM.apiKey) out.customLLM = { ...out.customLLM, apiKey: '***' };
  out.customLLM = (out.providers && out.providers.custom) ? { ...out.providers.custom, apiKey: out.providers.custom.apiKey === '***' ? '***' : (out.providers.custom.apiKey ? '***' : ''), baseUrl: out.providers.custom.apiBase || out.providers.custom.baseUrl || '' } : null;
  res.json(out);
});

// ---------- 自有 LLM 配置（需负责人鉴权）----------
app.patch('/api/config/custom-llm', (req, res) => {
  const ownerId = getOwnerId(req);
  const updated = config.setCustomLLM(ownerId, req.body || {});
  if (!updated) return res.status(403).json({ error: '无权修改配置' });
  const out = { ...updated };
  if (out.providers && out.providers.custom && out.providers.custom.apiKey) {
    out.providers = { ...out.providers, custom: { ...out.providers.custom, apiKey: '***' } };
  }
  out.customLLM = (out.providers && out.providers.custom) ? { ...out.providers.custom, apiKey: '***' } : null;
  res.json(out);
});

app.delete('/api/config/custom-llm', (req, res) => {
  const ownerId = getOwnerId(req);
  const updated = config.clearCustomLLM(ownerId);
  if (!updated) return res.status(403).json({ error: '无权修改配置' });
  res.json(updated);
});

// ---------- 用量占位（仅 Router 计费；自有 LLM 不计费）----------
app.get('/api/usage', (req, res) => {
  const ownerId = getOwnerId(req);
  res.json({ usage: [{ source: 'router', tokens: 0 }, { source: 'custom', tokens: 0 }] });
});

// ---------- 静态与 SPA（本地 UI 来自 cli/joytrunk/ui 构建到 gateway/static）----------
const UI_DIR = path.join(__dirname, '..', 'ui');
const STATIC_DIR = path.join(__dirname, 'static');

function ensureStatic() {
  const indexPath = path.join(STATIC_DIR, 'index.html');
  if (fs.existsSync(indexPath)) return;
  if (!fs.existsSync(path.join(UI_DIR, 'package.json'))) return;
  console.log('JoyTrunk: Building local UI (first run)...');
  try {
    execSync('npm install', { cwd: UI_DIR, stdio: 'inherit' });
    execSync('npm run build', { cwd: UI_DIR, stdio: 'inherit' });
  } catch (e) {
    console.error('JoyTrunk: UI build failed.', e.message);
  }
}

ensureStatic();

if (fs.existsSync(path.join(STATIC_DIR, 'index.html'))) {
  app.use(express.static(STATIC_DIR, { index: false }));
  app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api')) return next();
    res.sendFile(path.join(STATIC_DIR, 'index.html'));
  });
} else {
  app.get('/', (req, res) => {
    res.send(`
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>JoyTrunk 喜象 Agent</title></head>
<body>
  <h1>JoyTrunk（喜象 Agent）</h1>
  <p>本地管理页占位。端口: ${PORT}</p>
  <p>请先构建本地 UI：<code>cd joytrunk/ui && npm install && npm run build</code></p>
  <p><a href="/api/health">API 健康检查</a> | <a href="/api/teams/current">当前团队</a></p>
</body>
</html>
  `);
  });
}

app.listen(PORT, HOST, () => {
  console.log(`JoyTrunk gateway listening on http://${HOST}:${PORT}`);
});
