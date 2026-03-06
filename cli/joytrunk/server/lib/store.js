/**
 * 全局 config 仅保留 owner；员工数据来自各员工目录的 config.json。
 * 每位员工作为独立 agent，使用 workspace/employees/<id>/config.json。
 */

const fs = require('fs');
const config = require('./config');
const { getWorkspaceRoot, getEmployeeDir, getEmployeeConfigPath } = require('./paths');
const { copyTemplatesToEmployee } = require('./employeeWorkspace');

function load() {
  const c = config.loadConfig();
  const owners = c.ownerId
    ? [{ id: c.ownerId, name: '本地负责人', email: null }]
    : [];
  const employees = getEmployees();
  return { owners, employees };
}

function save(data) {
  const c = config.loadConfig();
  if (data.owners && data.owners.length > 0) {
    c.ownerId = data.owners[0].id;
  }
  config.saveConfig(c);
}

function getOwners() {
  return load().owners;
}

function getEmployees() {
  const empRoot = require('path').join(getWorkspaceRoot(), 'employees');
  if (!fs.existsSync(empRoot)) return [];
  const dirs = fs.readdirSync(empRoot);
  const employees = [];
  for (const id of dirs) {
    const cfgPath = getEmployeeConfigPath(id);
    if (!fs.existsSync(cfgPath)) continue;
    try {
      const data = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
      employees.push({ id: data.id || id, ...data });
    } catch (e) {
      // skip invalid config
    }
  }
  return employees;
}

function findOwnerById(id) {
  return getOwners().find((o) => o.id === id);
}

function findEmployeeById(id) {
  const cfgPath = getEmployeeConfigPath(id);
  if (!fs.existsSync(cfgPath)) return null;
  try {
    return JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  } catch (e) {
    return null;
  }
}

function createOwner(payload) {
  const id = require('uuid').v4();
  const owner = {
    id,
    name: payload.name || '负责人',
    email: payload.email || null,
    createdAt: new Date().toISOString(),
  };
  config.setOwnerInConfig(owner.id);
  return owner;
}

function createEmployee(ownerId, payload) {
  const id = require('uuid').v4();
  const employee = {
    id,
    ownerId,
    name: payload.name || '员工',
    persona: payload.persona || null,
    role: payload.role || null,
    specialty: payload.specialty || null,
    businessModule: payload.businessModule || null,
    focus: payload.focus || null,
    status: 'active',
    createdAt: new Date().toISOString(),
    agents: {},
    providers: {},
  };
  const empDir = getEmployeeDir(id);
  if (!fs.existsSync(empDir)) fs.mkdirSync(empDir, { recursive: true });
  fs.writeFileSync(getEmployeeConfigPath(id), JSON.stringify(employee, null, 2), 'utf8');
  copyTemplatesToEmployee(id);
  return employee;
}

function updateEmployee(employeeId, ownerId, payload) {
  const cfgPath = getEmployeeConfigPath(employeeId);
  if (!fs.existsSync(cfgPath)) return null;
  let data;
  try {
    data = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  } catch (e) {
    return null;
  }
  if (data.ownerId !== ownerId) return null;
  const allowed = ['name', 'persona', 'role', 'specialty', 'businessModule', 'focus', 'status', 'agents', 'providers'];
  allowed.forEach((k) => {
    if (payload[k] !== undefined) data[k] = payload[k];
  });
  fs.writeFileSync(cfgPath, JSON.stringify(data, null, 2), 'utf8');
  return data;
}

function getEmployeesByOwnerId(ownerId) {
  return getEmployees().filter((e) => e.ownerId === ownerId);
}

module.exports = {
  load,
  save,
  getOwners,
  getEmployees,
  findOwnerById,
  findEmployeeById,
  createOwner,
  createEmployee,
  updateEmployee,
  getEmployeesByOwnerId,
};
