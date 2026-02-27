/**
 * 员工与负责人数据：从 config.json 读写，与 CLI config_store 共用同一文件，不再使用 store.json。
 */

const config = require('./config');
const { getJoytrunkRoot } = require('./paths');

function load() {
  const c = config.loadConfig();
  const owners = c.ownerId
    ? [{ id: c.ownerId, name: '本地负责人', email: null }]
    : [];
  const employees = Array.isArray(c.employees) ? c.employees : [];
  return { owners, employees };
}

function save(data) {
  const c = config.loadConfig();
  if (data.owners && data.owners.length > 0) {
    c.ownerId = data.owners[0].id;
  }
  if (Array.isArray(data.employees)) {
    c.employees = data.employees;
  }
  config.saveConfig(c);
}

function getOwners() {
  return load().owners;
}

function getEmployees() {
  return load().employees;
}

function findOwnerById(id) {
  return getOwners().find((o) => o.id === id);
}

function findEmployeeById(id) {
  return getEmployees().find((e) => e.id === id);
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
  const data = load();
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
  };
  data.employees.push(employee);
  save(data);
  return employee;
}

function updateEmployee(employeeId, ownerId, payload) {
  const data = load();
  const idx = data.employees.findIndex((e) => e.id === employeeId && e.ownerId === ownerId);
  if (idx === -1) return null;
  const allowed = ['name', 'persona', 'role', 'specialty', 'businessModule', 'focus', 'status'];
  allowed.forEach((k) => {
    if (payload[k] !== undefined) data.employees[idx][k] = payload[k];
  });
  save(data);
  return data.employees[idx];
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
