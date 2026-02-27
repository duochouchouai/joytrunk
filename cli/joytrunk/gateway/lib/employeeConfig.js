/**
 * 员工级 config.json：workspace/employees/<id>/config.json
 * 可覆盖主 config 的 agents.defaults（model、maxTokens、temperature）与 providers.custom（该员工专用自有 LLM）。
 * 合并规则：主配置打底，员工配置中出现的键覆盖主配置。
 */

const fs = require('fs');
const { getEmployeeConfigPath, getEmployeeDir } = require('./paths');

function loadEmployeeConfig(employeeId) {
  const p = getEmployeeConfigPath(employeeId);
  if (!fs.existsSync(p)) return null;
  try {
    const raw = JSON.parse(fs.readFileSync(p, 'utf8'));
    return raw && typeof raw === 'object' ? raw : null;
  } catch {
    return null;
  }
}

/**
 * 深合并：target 上叠加 source，仅处理 source 中存在的键；只合并对象，其余覆盖。
 */
function deepMerge(target, source) {
  if (!source || typeof source !== 'object') return target;
  const out = { ...target };
  for (const key of Object.keys(source)) {
    if (source[key] != null && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      out[key] = deepMerge(out[key] || {}, source[key]);
    } else {
      out[key] = source[key];
    }
  }
  return out;
}

/**
 * 返回该员工合并后的配置（主 config + 员工 config 覆盖）
 * getMainConfig 应返回已迁移后的主配置（如 config.loadConfig()）
 */
function getMergedConfigForEmployee(employeeId, getMainConfig) {
  const main = getMainConfig && getMainConfig();
  if (!main) return null;
  const emp = loadEmployeeConfig(employeeId);
  if (!emp || typeof emp !== 'object') return main;
  const filtered = {};
  if (emp.agents && typeof emp.agents === 'object') filtered.agents = emp.agents;
  if (emp.providers && typeof emp.providers === 'object') filtered.providers = emp.providers;
  if (Object.keys(filtered).length === 0) return main;
  return deepMerge(JSON.parse(JSON.stringify(main)), filtered);
}

/**
 * 保存员工 config：只写入允许的键（agents、providers）
 */
function saveEmployeeConfig(employeeId, data) {
  if (!data || typeof data !== 'object') return;
  const dir = getEmployeeDir(employeeId);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  const out = {};
  if (data.agents && typeof data.agents === 'object') out.agents = data.agents;
  if (data.providers && typeof data.providers === 'object') out.providers = data.providers;
  fs.writeFileSync(getEmployeeConfigPath(employeeId), JSON.stringify(out, null, 2), 'utf8');
}

/** 写入空员工 config（创建员工时调用） */
function ensureEmployeeConfigExists(employeeId) {
  const p = getEmployeeConfigPath(employeeId);
  if (fs.existsSync(p)) return;
  const dir = getEmployeeDir(employeeId);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(p, '{}\n', 'utf8');
}

module.exports = {
  loadEmployeeConfig,
  getMergedConfigForEmployee,
  saveEmployeeConfig,
  ensureEmployeeConfigExists,
  deepMerge,
};
