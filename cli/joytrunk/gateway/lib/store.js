/**
 * 本地 JSON 存储：负责人、员工。MVP 单机单用户，数据落盘 ~/.joytrunk/data/store.json
 */

const fs = require('fs');
const path = require('path');
const { getJoytrunkRoot } = require('./paths');

const DATA_DIR = () => path.join(getJoytrunkRoot(), 'data');
const STORE_FILE = () => path.join(DATA_DIR(), 'store.json');

function ensureDataDir() {
  const dir = DATA_DIR();
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}

function load() {
  ensureDataDir();
  const file = STORE_FILE();
  if (!fs.existsSync(file)) {
    return { owners: [], employees: [] };
  }
  const raw = fs.readFileSync(file, 'utf8');
  try {
    return JSON.parse(raw);
  } catch {
    return { owners: [], employees: [] };
  }
}

function save(data) {
  ensureDataDir();
  fs.writeFileSync(STORE_FILE(), JSON.stringify(data, null, 2), 'utf8');
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
  const data = load();
  const id = require('uuid').v4();
  const owner = {
    id,
    name: payload.name || '负责人',
    email: payload.email || null,
    createdAt: new Date().toISOString(),
  };
  data.owners.push(owner);
  save(data);
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
