/**
 * 为员工初始化 workspace：从 JoyTrunk 捆绑模板（cli 包内 joytrunk/templates）复制到员工目录（仿 nanobot）。
 * 模板仅存在于 joytrunk 包内，workspace 下不设 templates。
 * 包含 SOUL.md、USER.md、AGENTS.md、TOOLS.md、HEARTBEAT.md、memory/MEMORY.md、skills/
 */

const fs = require('fs');
const path = require('path');
const { getEmployeeDir } = require('./paths');

/** 捆绑模板目录：server 在 joytrunk/server/，模板在 joytrunk/templates/ */
const BUNDLED_TEMPLATES_DIR = path.join(__dirname, '..', '..', 'templates');

function copyTemplatesToEmployee(employeeId) {
  const empDir = getEmployeeDir(employeeId);
  const tplDir = BUNDLED_TEMPLATES_DIR;
  if (!fs.existsSync(tplDir)) return;
  if (!fs.existsSync(empDir)) fs.mkdirSync(empDir, { recursive: true });

  const items = fs.readdirSync(tplDir, { withFileTypes: true });
  for (const item of items) {
    if (item.name.startsWith('.')) continue;
    const src = path.join(tplDir, item.name);
    const dest = path.join(empDir, item.name);
    if (item.isFile() && path.extname(item.name) === '.md') {
      if (!fs.existsSync(dest)) fs.copyFileSync(src, dest);
    } else if (item.isDirectory() && item.name === 'memory') {
      const memDest = path.join(empDir, 'memory');
      if (!fs.existsSync(memDest)) fs.mkdirSync(memDest, { recursive: true });
      const subItems = fs.readdirSync(src, { withFileTypes: true });
      for (const sub of subItems) {
        if (sub.isFile()) {
          const subDest = path.join(memDest, sub.name);
          if (!fs.existsSync(subDest)) fs.copyFileSync(path.join(src, sub.name), subDest);
        }
      }
    }
  }
  const skillsDir = path.join(empDir, 'skills');
  if (!fs.existsSync(skillsDir)) fs.mkdirSync(skillsDir, { recursive: true });
}

module.exports = { copyTemplatesToEmployee };
