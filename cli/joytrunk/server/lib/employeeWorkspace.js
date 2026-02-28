/**
 * 为员工初始化 workspace：从 JoyTrunk 捆绑模板复制 SYSTEM_PROMPT.md、HEARTBEAT.md、memory/、skills/。
 * 不再复制 SOUL.md、USER.md、AGENTS.md、TOOLS.md（14 类 category 仅存于 memory.db，由 Python 端 get_store 时创建）。
 */

const fs = require('fs');
const path = require('path');
const { getEmployeeDir } = require('./paths');

/** 捆绑模板目录：server 在 joytrunk/server/，模板在 joytrunk/templates/ */
const BUNDLED_TEMPLATES_DIR = path.join(__dirname, '..', '..', 'templates');

const TEMPLATE_FILES = ['SYSTEM_PROMPT.md', 'HEARTBEAT.md'];

function copyTemplatesToEmployee(employeeId) {
  const empDir = getEmployeeDir(employeeId);
  const tplDir = BUNDLED_TEMPLATES_DIR;
  if (!fs.existsSync(tplDir)) return;
  if (!fs.existsSync(empDir)) fs.mkdirSync(empDir, { recursive: true });

  for (const name of TEMPLATE_FILES) {
    const src = path.join(tplDir, name);
    const dest = path.join(empDir, name);
    if (fs.existsSync(src) && fs.statSync(src).isFile() && !fs.existsSync(dest)) {
      fs.copyFileSync(src, dest);
    }
  }

  const memSrc = path.join(tplDir, 'memory');
  if (fs.existsSync(memSrc) && fs.statSync(memSrc).isDirectory()) {
    const memDest = path.join(empDir, 'memory');
    if (!fs.existsSync(memDest)) fs.mkdirSync(memDest, { recursive: true });
    const subItems = fs.readdirSync(memSrc, { withFileTypes: true });
    for (const sub of subItems) {
      if (sub.isFile()) {
        const subDest = path.join(memDest, sub.name);
        if (!fs.existsSync(subDest)) fs.copyFileSync(path.join(memSrc, sub.name), subDest);
      }
    }
  }

  const skillsDir = path.join(empDir, 'skills');
  if (!fs.existsSync(skillsDir)) fs.mkdirSync(skillsDir, { recursive: true });
}

module.exports = { copyTemplatesToEmployee };
