/**
 * 读写 ~/.joytrunk/config.json，结构仿 nanobot（server / agents / channels / providers）
 * 与 cli config_schema 约定一致；加载时自动迁移旧版。
 */

const fs = require('fs');
const { getConfigPath, getJoytrunkRoot } = require('./paths');
const { DEFAULT_CONFIG, migrateFromLegacy } = require('./configSchema');

function loadConfig() {
  const p = getConfigPath();
  if (!fs.existsSync(p)) return migrateFromLegacy(null);
  try {
    const raw = JSON.parse(fs.readFileSync(p, 'utf8'));
    return migrateFromLegacy(raw);
  } catch {
    return migrateFromLegacy(null);
  }
}

function saveConfig(config) {
  const root = getJoytrunkRoot();
  if (!fs.existsSync(root)) fs.mkdirSync(root, { recursive: true });
  const out = migrateFromLegacy(config);
  fs.writeFileSync(getConfigPath(), JSON.stringify(out, null, 2), 'utf8');
}

function setOwnerInConfig(ownerId) {
  const c = loadConfig();
  c.joytrunkRoot = c.joytrunkRoot || getJoytrunkRoot();
  c.ownerId = ownerId;
  saveConfig(c);
  return c;
}

function setDefaultEmployeeInConfig(employeeId) {
  const c = loadConfig();
  if (!c.agents) c.agents = { defaults: {} };
  if (!c.agents.defaults) c.agents.defaults = {};
  c.agents.defaults.defaultEmployeeId = employeeId;
  saveConfig(c);
  return c;
}

/** 获取当前「自有 LLM」配置（providers.custom），兼容旧 customLLM */
function getCustomLLM(config) {
  const c = config || loadConfig();
  return c.providers?.custom ?? c.customLLM ?? null;
}

/** 设置 providers.custom（自有 LLM）；payload 同 API：apiKey / baseUrl 或 apiBase / model */
function setCustomLLM(ownerId, payload) {
  const c = loadConfig();
  if (c.ownerId !== ownerId) return null;
  if (!c.providers) c.providers = { joytrunk: {}, custom: { apiKey: '', apiBase: null, model: 'gpt-3.5-turbo' } };
  if (!c.providers.custom) c.providers.custom = { apiKey: '', apiBase: null, model: 'gpt-3.5-turbo' };
  const hasAny = (payload.apiKey != null && payload.apiKey !== '') || (payload.baseUrl != null && payload.baseUrl !== '') || (payload.apiBase != null && payload.apiBase !== '') || (payload.model != null && payload.model !== '');
  const cur = c.providers.custom;
  if (!hasAny && !(cur.apiKey || cur.apiBase || cur.model)) {
    c.providers.custom = { apiKey: '', apiBase: null, model: 'gpt-3.5-turbo' };
  } else {
    c.providers.custom = {
      apiKey: payload.apiKey != null ? payload.apiKey : cur.apiKey,
      apiBase: (payload.apiBase ?? payload.baseUrl) != null ? (payload.apiBase ?? payload.baseUrl) : cur.apiBase,
      model: payload.model != null ? payload.model : cur.model,
    };
  }
  saveConfig(c);
  return c;
}

function clearCustomLLM(ownerId) {
  const c = loadConfig();
  if (c.ownerId !== ownerId) return null;
  if (c.providers && c.providers.custom) {
    c.providers.custom = { apiKey: '', apiBase: null, model: 'gpt-3.5-turbo' };
  }
  saveConfig(c);
  return c;
}

module.exports = { loadConfig, saveConfig, setOwnerInConfig, setDefaultEmployeeInConfig, getCustomLLM, setCustomLLM, clearCustomLLM };
