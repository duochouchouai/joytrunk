/**
 * Gateway 单元测试：paths 与 store（与 nodejs 原 tests 一致，现归属 cli 内 gateway）
 */

const { describe, it } = require('node:test');
const assert = require('node:assert');
const path = require('path');
const os = require('os');

describe('paths', () => {
  const { getJoytrunkRoot, getConfigPath, getEmployeeDir, getEmployeeConfigPath, getSharedMemoryDir, getSharedSkillsDir } = require('../lib/paths');

  it('getJoytrunkRoot returns path under home', () => {
    const root = getJoytrunkRoot();
    assert.ok(root.includes('.joytrunk'));
    assert.ok(path.isAbsolute(root));
  });

  it('getConfigPath joins root and config.json', () => {
    const p = getConfigPath();
    assert.ok(p.endsWith('config.json') || p.includes('config.json'));
  });

  it('getEmployeeDir joins employees and id', () => {
    const p = getEmployeeDir('emp-1');
    assert.ok(p.includes('employees'));
    assert.ok(p.includes('emp-1'));
  });

  it('getEmployeeConfigPath is under employee dir and is config.json', () => {
    const p = getEmployeeConfigPath('emp-2');
    assert.ok(p.includes('employees'));
    assert.ok(p.includes('emp-2'));
    assert.ok(p.endsWith('config.json') || p.includes(path.sep + 'config.json'));
  });

  it('getSharedMemoryDir is under workspace and is memory', () => {
    const p = getSharedMemoryDir();
    assert.ok(p.includes('workspace'));
    assert.ok(p.endsWith('memory') || p.includes(path.sep + 'memory'));
  });

  it('getSharedSkillsDir is under workspace and is skills', () => {
    const p = getSharedSkillsDir();
    assert.ok(p.includes('workspace'));
    assert.ok(p.endsWith('skills') || p.includes(path.sep + 'skills'));
  });
});

describe('store', () => {
  const tmpDir = path.join(os.tmpdir(), 'joytrunk-gateway-test-' + Date.now() + '-' + Math.random().toString(36).slice(2));
  const origEnv = process.env.JOYTRUNK_ROOT;

  it('load returns default when file missing', () => {
    process.env.JOYTRUNK_ROOT = tmpDir;
    delete require.cache[require.resolve('../lib/store')];
    const store = require('../lib/store');
    const data = store.load();
    assert.ok(Array.isArray(data.owners));
    assert.ok(Array.isArray(data.employees));
    if (origEnv !== undefined) process.env.JOYTRUNK_ROOT = origEnv;
    else delete process.env.JOYTRUNK_ROOT;
  });

  it('createOwner adds owner and save', () => {
    const dir2 = path.join(os.tmpdir(), 'joytrunk-gateway-test-' + Date.now() + '-' + Math.random().toString(36).slice(2));
    process.env.JOYTRUNK_ROOT = dir2;
    delete require.cache[require.resolve('../lib/store')];
    const store = require('../lib/store');
    const owner = store.createOwner({ name: 'Test Owner' });
    assert.ok(owner.id);
    assert.strictEqual(owner.name, 'Test Owner');
    const data = store.load();
    assert.strictEqual(data.owners.length, 1);
    assert.strictEqual(data.owners[0].id, owner.id);
    if (origEnv !== undefined) process.env.JOYTRUNK_ROOT = origEnv;
    else delete process.env.JOYTRUNK_ROOT;
  });
});
