/**
 * JoyTrunk 路径约定：与 cli §4.2 一致。
 * Windows: %USERPROFILE%\.joytrunk，Linux/macOS: ~/.joytrunk
 */

const path = require('path');
const os = require('os');

function getJoytrunkRoot() {
  if (process.env.JOYTRUNK_ROOT) {
    return path.resolve(process.env.JOYTRUNK_ROOT);
  }
  return path.join(os.homedir(), '.joytrunk');
}

function getConfigPath() {
  return path.join(getJoytrunkRoot(), 'config.json');
}

function getWorkspaceRoot() {
  return path.join(getJoytrunkRoot(), 'workspace');
}

function getEmployeeDir(employeeId) {
  return path.join(getWorkspaceRoot(), 'employees', employeeId);
}

/** 员工级 config.json 路径（可覆盖主 config）；无则继承主配置 */
function getEmployeeConfigPath(employeeId) {
  return path.join(getEmployeeDir(employeeId), 'config.json');
}

/** 负责人级共享记忆目录：workspace/memory/，所有员工可见 */
function getSharedMemoryDir() {
  return path.join(getWorkspaceRoot(), 'memory');
}

/** 负责人级共享技能目录：workspace/skills/，所有员工默认可见 */
function getSharedSkillsDir() {
  return path.join(getWorkspaceRoot(), 'skills');
}

module.exports = {
  getJoytrunkRoot,
  getConfigPath,
  getWorkspaceRoot,
  getEmployeeDir,
  getEmployeeConfigPath,
  getSharedMemoryDir,
  getSharedSkillsDir,
};
