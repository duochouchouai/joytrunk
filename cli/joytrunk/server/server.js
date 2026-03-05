/**
 * JoyTrunk 本地管理后端（cli 内）：监听 32890，提供负责人/员工/团队 CRUD、config/workspace、agent 与 API。
 * 由 joytrunk server 启动；静态资源来自同目录下 static/（由 cli/joytrunk/ui 构建产出）。
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');
const { getEmployeeDir, getAgentLogPath, getJoytrunkRoot } = require('./lib/paths');
const store = require('./lib/store');
const config = require('./lib/config');
const agent = require('./lib/agent');
const { copyTemplatesToEmployee } = require('./lib/employeeWorkspace');
const employeeConfig = require('./lib/employeeConfig');

const app = express();
const cfg = config.loadConfig();
const PORT = Number(process.env.PORT) || (cfg.server && cfg.server.port) || 32890;
const HOST = (cfg.server && cfg.server.host) || '127.0.0.1';

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
    service: 'joytrunk-server',
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

// ---------- 员工运行时日志（结构化 JSONL，供前端 debug）----------
app.get('/api/employees/:id/logs', (req, res) => {
  const ownerId = getOwnerId(req);
  const emp = store.findEmployeeById(req.params.id);
  if (!emp || emp.ownerId !== ownerId) return res.status(404).json({ error: '员工不存在' });
  const logPath = getAgentLogPath(req.params.id);
  let entries = [];
  try {
    if (fs.existsSync(logPath)) {
      const raw = fs.readFileSync(logPath, 'utf-8');
      const lines = raw.split('\n').filter((line) => line.trim());
      entries = lines.map((line) => {
        try {
          return JSON.parse(line);
        } catch {
          return null;
        }
      }).filter(Boolean);
      // 最新在前
      entries.reverse();
    }
  } catch (e) {
    return res.status(500).json({ error: e.message || '读取日志失败' });
  }
  res.json({ entries });
});

// ---------- 员工 memory.db 内容（供前端展示）----------
// 仅当前负责人可访问其员工的 memory；若 store 中无该员工则 404
app.get('/api/employees/:id/memory', (req, res) => {
  const ownerId = getOwnerId(req);
  const employeeId = req.params.id;
  const emp = store.findEmployeeById(employeeId);
  if (!emp || emp.ownerId !== ownerId) {
    return res.status(404).json({ error: '员工不存在或无权访问' });
  }
  const joytrunkRoot = path.resolve(getJoytrunkRoot());
  const employeeDir = path.join(joytrunkRoot, 'workspace', 'employees', employeeId);
  const memoryDbPath = path.join(employeeDir, 'memory.db');

  if (!fs.existsSync(memoryDbPath)) {
    return res.status(404).json({ error: '该员工暂无记忆库' });
  }
  const cliRoot = path.join(__dirname, '..', '..');
  const env = { ...process.env, JOYTRUNK_ROOT: joytrunkRoot };
  env.PYTHONPATH = path.join(cliRoot, '..');
  if (process.platform === 'win32') env.PYTHONIOENCODING = 'utf-8';
  try {
    const stdout = execSync(`python -m joytrunk.scripts.dump_memory ${employeeId}`, {
      encoding: 'utf-8',
      cwd: cliRoot,
      env,
      maxBuffer: 2 * 1024 * 1024,
    });
    const data = JSON.parse(stdout.trim());
    if (data.error) {
      return res.status(500).json({ error: data.error });
    }
    res.json(data);
  } catch (e) {
    let msg = e.message || '读取 memory 失败';
    if (e.stdout && typeof e.stdout === 'string' && e.stdout.trim()) {
      try {
        const parsed = JSON.parse(e.stdout.trim());
        if (parsed.error) msg = parsed.error;
      } catch (_) {}
    } else if (e.stderr && typeof e.stderr === 'string') {
      msg = e.stderr.trim() || msg;
    }
    return res.status(500).json({ error: msg });
  }
});

/** 与负责人的聊天记录（仅 owner session，供聊天记录页展示） */
app.get('/api/employees/:id/chat-history', (req, res) => {
  const ownerId = getOwnerId(req);
  const employeeId = req.params.id;
  const emp = store.findEmployeeById(employeeId);
  if (!emp || emp.ownerId !== ownerId) {
    return res.status(404).json({ error: '员工不存在或无权访问' });
  }
  const joytrunkRoot = path.resolve(getJoytrunkRoot());
  const memoryDbPath = path.join(joytrunkRoot, 'workspace', 'employees', employeeId, 'memory.db');
  if (!fs.existsSync(memoryDbPath)) {
    return res.json({ messages: [] });
  }
  const cliRoot = path.join(__dirname, '..', '..');
  const env = { ...process.env, JOYTRUNK_ROOT: joytrunkRoot };
  env.PYTHONPATH = path.join(cliRoot, '..');
  if (process.platform === 'win32') env.PYTHONIOENCODING = 'utf-8';
  try {
    const stdout = execSync(`python -m joytrunk.scripts.dump_memory ${employeeId}`, {
      encoding: 'utf-8',
      cwd: cliRoot,
      env,
      maxBuffer: 2 * 1024 * 1024,
    });
    const data = JSON.parse(stdout.trim());
    if (data.error) {
      return res.status(500).json({ error: data.error });
    }
    const all = (data.chat_messages || []).filter((m) => m.session_key === 'owner');
    const messages = all.slice(-300);
    res.json({ messages });
  } catch (e) {
    let msg = e.message || '读取聊天记录失败';
    if (e.stdout && typeof e.stdout === 'string' && e.stdout.trim()) {
      try {
        const parsed = JSON.parse(e.stdout.trim());
        if (parsed.error) msg = parsed.error;
      } catch (_) {}
    } else if (e.stderr && typeof e.stderr === 'string') {
      msg = e.stderr.trim() || msg;
    }
    return res.status(500).json({ error: msg });
  }
});

/** 检查当前用户有权访问该员工的记忆库；返回 { employeeId, cliRoot, env } 或 null（已 send 4xx） */
function ensureMemoryAccess(req, res) {
  const ownerId = getOwnerId(req);
  const employeeId = req.params.id;
  const emp = store.findEmployeeById(employeeId);
  if (!emp || emp.ownerId !== ownerId) {
    res.status(404).json({ error: '员工不存在或无权访问' });
    return null;
  }
  const joytrunkRoot = path.resolve(getJoytrunkRoot());
  const memoryDbPath = path.join(joytrunkRoot, 'workspace', 'employees', employeeId, 'memory.db');
  if (!fs.existsSync(memoryDbPath)) {
    res.status(404).json({ error: '该员工暂无记忆库' });
    return null;
  }
  const cliRoot = path.join(__dirname, '..', '..');
  const env = { ...process.env, JOYTRUNK_ROOT: joytrunkRoot };
  env.PYTHONPATH = path.join(cliRoot, '..');
  if (process.platform === 'win32') env.PYTHONIOENCODING = 'utf-8';
  return { employeeId, cliRoot, env };
}

// ---------- 员工 SYSTEM_PROMPT 模板（供记忆页右侧展示）----------
app.get('/api/employees/:id/system-prompt-template', (req, res) => {
  const ownerId = getOwnerId(req);
  const employeeId = req.params.id;
  const emp = store.findEmployeeById(employeeId);
  if (!emp || emp.ownerId !== ownerId) {
    return res.status(404).json({ error: '员工不存在或无权访问' });
  }
  const employeeTpl = path.join(getEmployeeDir(employeeId), 'SYSTEM_PROMPT.md');
  const bundledTpl = path.join(__dirname, '..', 'templates', 'SYSTEM_PROMPT.md');
  const tplPath = fs.existsSync(employeeTpl) ? employeeTpl : bundledTpl;
  try {
    const content = fs.readFileSync(tplPath, 'utf-8');
    res.type('text/markdown').send(content);
  } catch (e) {
    res.status(500).json({ error: e.message || '读取模板失败' });
  }
});

/** 返回员工的 cliRoot 与 env（不要求 memory.db 存在），用于调用 Python 脚本 */
function getEmployeeCliEnv(employeeId) {
  const joytrunkRoot = path.resolve(getJoytrunkRoot());
  const cliRoot = path.join(__dirname, '..', '..');
  const env = { ...process.env, JOYTRUNK_ROOT: joytrunkRoot };
  env.PYTHONPATH = path.join(cliRoot, '..');
  if (process.platform === 'win32') env.PYTHONIOENCODING = 'utf-8';
  return { cliRoot, env };
}

/** 合并后的系统提示词（模板 + memory.db 占位符替换结果），供记忆页右侧展示 */
app.get('/api/employees/:id/system-prompt-merged', (req, res) => {
  const ownerId = getOwnerId(req);
  const employeeId = req.params.id;
  const emp = store.findEmployeeById(employeeId);
  if (!emp || emp.ownerId !== ownerId) {
    return res.status(404).json({ error: '员工不存在或无权访问' });
  }
  const { cliRoot, env } = getEmployeeCliEnv(employeeId);
  try {
    const r = spawnSync('python', ['-m', 'joytrunk.scripts.preview_system_prompt', employeeId], {
      encoding: 'utf-8',
      cwd: cliRoot,
      env,
      maxBuffer: 2 * 1024 * 1024,
    });
    if (r.status !== 0) {
      const err = (r.stderr || r.stdout || '').trim() || `exit ${r.status}`;
      return res.status(500).type('text/plain').send(err);
    }
    const content = (r.stdout || '').trim();
    res.type('text/markdown').send(content);
  } catch (e) {
    res.status(500).type('text/plain').send(e.message || '生成合并提示词失败');
  }
});

/** 调用 memory_mutate 脚本，stdin 传入 JSON；返回 { success, data, error } */
function runMemoryMutate(employeeId, operation, id, payload, cliRoot, env) {
  const input = JSON.stringify({ employee_id: employeeId, operation, id: id || undefined, payload: payload || {} }) + '\n';
  const r = spawnSync('python', ['-m', 'joytrunk.scripts.memory_mutate'], {
    input,
    encoding: 'utf-8',
    cwd: cliRoot,
    env,
    maxBuffer: 2 * 1024 * 1024,
  });
  const out = (r.stdout || '').trim();
  const err = (r.stderr || '').trim();
  if (r.status !== 0) {
    try {
      const parsed = JSON.parse(out);
      if (parsed.error) return { success: false, error: parsed.error };
    } catch (_) {}
    return { success: false, error: err || r.status.toString() };
  }
  try {
    const data = JSON.parse(out);
    if (data.error) return { success: false, error: data.error };
    return { success: true, data };
  } catch (_) {
    return { success: false, error: out || 'invalid output' };
  }
}

// ---------- 记忆库 CRUD：分类 ----------
app.post('/api/employees/:id/memory/categories', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'create_category', null, req.body || {}, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.status(201).json(result.data);
});

app.patch('/api/employees/:id/memory/categories/:cid', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'update_category', req.params.cid, req.body || {}, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.json(result.data);
});

app.delete('/api/employees/:id/memory/categories/:cid', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'delete_category', req.params.cid, null, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.json({ ok: true });
});

// ---------- 记忆库 CRUD：条目 ----------
app.post('/api/employees/:id/memory/items', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'create_item', null, req.body || {}, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.status(201).json(result.data);
});

app.patch('/api/employees/:id/memory/items/:iid', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'update_item', req.params.iid, req.body || {}, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.json(result.data);
});

app.delete('/api/employees/:id/memory/items/:iid', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'delete_item', req.params.iid, null, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.json({ ok: true });
});

// ---------- 记忆库 CRUD：资源 ----------
app.post('/api/employees/:id/memory/resources', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'create_resource', null, req.body || {}, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.status(201).json(result.data);
});

app.patch('/api/employees/:id/memory/resources/:rid', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'update_resource', req.params.rid, req.body || {}, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.json(result.data);
});

app.delete('/api/employees/:id/memory/resources/:rid', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'delete_resource', req.params.rid, null, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.json({ ok: true });
});

// ---------- 记忆库 CRUD：分类-条目关联 ----------
app.post('/api/employees/:id/memory/relations', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'create_relation', null, req.body || {}, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.status(201).json(result.data);
});

app.delete('/api/employees/:id/memory/relations/:relId', (req, res) => {
  const ctx = ensureMemoryAccess(req, res);
  if (!ctx) return;
  const { employeeId, cliRoot, env } = ctx;
  const result = runMemoryMutate(employeeId, 'delete_relation', req.params.relId, null, cliRoot, env);
  if (!result.success) return res.status(400).json({ error: result.error });
  res.json({ ok: true });
});

// ---------- 单通道消息：与员工对话（agent 调度 + 员工生存法则）----------
// 若配置了 gateway（a2a_backend_url 或 a2a_port），则转发到 Python A2A，按 10.29 转回 { reply, usage }；未配置则 503（方案 10.12）
function getA2aBaseUrl() {
  const c = config.loadConfig();
  const gw = c.gateway;
  if (!gw || (gw.a2a_backend_url == null && (gw.a2a_port == null || gw.a2a_port === ''))) return null;
  if (gw.a2a_backend_url && typeof gw.a2a_backend_url === 'string') {
    return gw.a2a_backend_url.replace(/\/$/, '');
  }
  const host = (c.server && c.server.host) || '127.0.0.1';
  const port = Number(gw.a2a_port) || 32900;
  return `http://${host}:${port}`;
}

app.post('/api/employees/:id/chat', async (req, res) => {
  const ownerId = getOwnerId(req);
  const emp = store.findEmployeeById(req.params.id);
  if (!emp || emp.ownerId !== ownerId) return res.status(404).json({ error: '员工不存在' });
  const content = (req.body && req.body.content) || '';
  const contextId = req.body && req.body.contextId;

  const baseUrl = getA2aBaseUrl();
  if (baseUrl) {
    // 与 gateway / joytrunk chat 共用同一聊天组件：仅通过 A2A 由 gateway 执行 run_employee_loop，不在此进程实现聊天逻辑
    const timeoutMs = (config.loadConfig().gateway && config.loadConfig().gateway.blocking_timeout_seconds) || 300;
    const sendUrl = `${baseUrl}/a2a/v1/tenants/${encodeURIComponent(ownerId)}/employees/${encodeURIComponent(emp.id)}/message:send`;
    const body = {
      message: {
        role: 'user',
        parts: [{ type: 'text', text: content }],
        ...(contextId != null ? { contextId } : {}),
      },
      configuration: { blocking: true },
      metadata: {},
    };
    try {
      const controller = new AbortController();
      const t = setTimeout(() => controller.abort(), timeoutMs * 1000);
      const resp = await fetch(sendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'A2A-Version': '1.0' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      clearTimeout(t);
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        return res.status(resp.status).json({ error: data.error || data.message || 'A2A 请求失败' });
      }
      let reply = '';
      let usage = null;
      if (data.history && Array.isArray(data.history)) {
        for (let i = data.history.length - 1; i >= 0; i--) {
          if (data.history[i].role === 'agent' && data.history[i].parts) {
            reply = (data.history[i].parts || []).map((p) => (p.type === 'text' ? p.text : '')).join('');
            break;
          }
        }
      }
      if (data.metadata && data.metadata.usage) {
        const u = data.metadata.usage;
        usage = { input_tokens: u.prompt_tokens ?? 0, output_tokens: u.completion_tokens ?? 0 };
      }
      return res.json({ reply: reply || '', usage });
    } catch (e) {
      if (e.name === 'AbortError') {
        return res.status(504).json({ error: 'A2A 请求超时' });
      }
      const isConnectionError = /fetch failed|ECONNREFUSED|ECONNRESET|ENOTFOUND|ETIMEDOUT/i.test(e.message || '');
      return res.status(503).json({
        error: isConnectionError
          ? 'A2A Gateway 未启动或不可达，请先在另一终端运行：joytrunk gateway'
          : (e.message || 'A2A Gateway 不可用，请先运行 joytrunk gateway'),
      });
    }
  }

  return res.status(503).json({
    error: '未配置 A2A Gateway。请配置 gateway.a2a_backend_url 或 gateway.a2a_port 并先运行 joytrunk gateway。',
  });
});

// ---------- JoyTrunk Router 代理（未配置自有 LLM 时 CLI/前端通过此端点调用大模型）----------
app.post('/api/llm/chat/completions', async (req, res) => {
  const c = config.loadConfig();
  const routerUrl = process.env.JOYTRUNK_ROUTER_URL || (c.providers && c.providers.joytrunk && c.providers.joytrunk.apiBase);
  const routerUrlTrimmed = (routerUrl && typeof routerUrl === 'string' && routerUrl.trim()) ? routerUrl.trim() : null;

  // 优先使用 JoyTrunk Router
  if (routerUrlTrimmed) {
    const ownerId = req.headers['x-owner-id'] || req.headers['authorization'] || c.ownerId;
    const url = routerUrlTrimmed.replace(/\/$/, '') + '/chat/completions';
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
      return res.json(data);
    } catch (e) {
      return res.status(502).json({ error: e.message || '转发 JoyTrunk Router 失败' });
    }
  }

  // 未配置 Router 时复用自有 LLM（providers.custom）对话逻辑，与 CLI/网页测试过的路径一致
  const custom = c.providers && c.providers.custom ? c.providers.custom : c.customLLM || null;
  const baseUrl = (custom && (custom.apiBase || custom.baseUrl)) ? String(custom.apiBase || custom.baseUrl).trim() : null;
  if (!baseUrl) {
    return res.status(503).json({
      error: 'JoyTrunk Router 未配置。请设置环境变量 JOYTRUNK_ROUTER_URL 或在配置中设置 providers.joytrunk.apiBase；或配置自有 LLM（providers.custom.apiBase + apiKey）后使用。',
    });
  }
  const apiKey = (custom && custom.apiKey) ? String(custom.apiKey) : '';
  const url = baseUrl.replace(/\/$/, '') + '/chat/completions';
  if (!url.startsWith('http')) {
    return res.status(503).json({ error: 'providers.custom.apiBase 需为完整 URL（如 https://api.openai.com/v1）' });
  }
  const body = { ...(req.body || {}) };
  if (custom && custom.model && String(custom.model).trim()) {
    body.model = String(custom.model).trim();
  }
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      },
      body: JSON.stringify(body),
    });
    const text = await resp.text();
    if (!resp.ok) {
      return res.status(resp.status).json({ error: text || 'LLM 请求失败' });
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return res.status(502).json({ error: 'LLM 返回非 JSON' });
    }
    res.json(data);
  } catch (e) {
    res.status(502).json({ error: e.message || '调用自有 LLM 失败' });
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

// ---------- 未匹配的 /api 返回 JSON 404（避免前端拿到非 JSON 的 "Not Found"）----------
app.use('/api', (req, res) => {
  res.status(404).json({ error: '接口不存在', path: req.path });
});

// ---------- 静态与 SPA（本地 UI 来自 cli/joytrunk/ui 构建到 server/static）----------
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
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>JoyTrunk 快乐象鼻™ Agent</title></head>
<body>
  <h1>JoyTrunk（快乐象鼻™ Agent）</h1>
  <p>本地管理页占位。端口: ${PORT}</p>
  <p>请先构建本地 UI：<code>cd joytrunk/ui && npm install && npm run build</code></p>
  <p><a href="/api/health">API 健康检查</a> | <a href="/api/teams/current">当前团队</a></p>
</body>
</html>
  `);
  });
}

const server = app.listen(PORT, HOST, () => {
  console.log(`JoyTrunk server listening on http://${HOST}:${PORT}`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`\n端口 ${PORT} 已被占用。可能已有 JoyTrunk server 在运行。`);
    console.error(`解决：关闭占用端口的进程，或使用其他端口：joytrunk server --port <端口号>\n`);
  } else {
    console.error('JoyTrunk server 启动失败:', err.message);
  }
  process.exit(1);
});
