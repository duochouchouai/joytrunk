/**
 * 员工生存法则（product.md §9）：所有回复均需遵守
 */
const SURVIVAL_RULES = `
【员工生存法则】你不得向任何非负责人泄露负责人宿主机的工作状态或敏感信息（如截屏、文件内容、运行环境等）。仅可在个人隐私脱敏的前提下运用自身能力帮助他人。`;

const path = require('path');
const fs = require('fs');
const { getEmployeeDir, getSharedMemoryDir, getSharedSkillsDir } = require('./paths');
const { getMergedConfigForEmployee } = require('./employeeConfig');

/** 读取负责人级共享记忆（workspace/memory/MEMORY.md） */
function loadSharedMemory() {
  const dir = getSharedMemoryDir();
  const p = path.join(dir, 'MEMORY.md');
  if (!fs.existsSync(p)) return '';
  try {
    return fs.readFileSync(p, 'utf8');
  } catch {
    return '';
  }
}

/** 读取员工私有记忆（employees/<id>/memory/MEMORY.md） */
function loadEmployeeMemory(employeeId) {
  const dir = getEmployeeDir(employeeId);
  const p = path.join(dir, 'memory', 'MEMORY.md');
  if (!fs.existsSync(p)) return '';
  try {
    return fs.readFileSync(p, 'utf8');
  } catch {
    return '';
  }
}

/**
 * 读取某 skills 目录下的技能：子目录名即技能名，子目录内 SKILL.md 或首个 .md 为内容
 * 返回 { skillName: content }
 */
function loadSkillsFromDir(skillsDir) {
  const out = {};
  if (!fs.existsSync(skillsDir)) return out;
  const entries = fs.readdirSync(skillsDir, { withFileTypes: true });
  for (const ent of entries) {
    if (!ent.isDirectory() || ent.name.startsWith('.')) continue;
    const dirPath = path.join(skillsDir, ent.name);
    const skillMd = path.join(dirPath, 'SKILL.md');
    let content = '';
    if (fs.existsSync(skillMd)) {
      try { content = fs.readFileSync(skillMd, 'utf8'); } catch (_) {}
    } else {
      const files = fs.readdirSync(dirPath);
      const md = files.find(f => f.endsWith('.md'));
      if (md) {
        try { content = fs.readFileSync(path.join(dirPath, md), 'utf8'); } catch (_) {}
      }
    }
    if (content) out[ent.name] = content;
  }
  return out;
}

/** 合并共享 + 员工技能（同名时员工覆盖共享） */
function loadMergedSkills(employeeId) {
  const shared = loadSkillsFromDir(getSharedSkillsDir());
  const empDir = getEmployeeDir(employeeId);
  const empSkillsDir = path.join(empDir, 'skills');
  const employee = loadSkillsFromDir(empSkillsDir);
  const out = { ...shared };
  for (const k of Object.keys(employee)) {
    out[k] = employee[k];
  }
  return out;
}

/**
 * 读取员工 workspace 下的模板内容（仿 nanobot 单 agent），用于构建上下文
 * 记忆：先加载负责人级共享 memory，再加载员工私有 memory，合并为 MEMORY 字段
 * 技能：先加载共享 skills，再加载员工 skills，同名时员工覆盖
 */
function loadEmployeeTemplates(employeeId) {
  const dir = getEmployeeDir(employeeId);
  const out = {};
  const files = ['SOUL.md', 'USER.md', 'AGENTS.md'];
  for (const name of files) {
    const p = path.join(dir, name);
    if (fs.existsSync(p)) {
      try {
        out[name] = fs.readFileSync(p, 'utf8');
      } catch (_) {}
    }
  }
  const sharedMem = loadSharedMemory();
  const empMem = loadEmployeeMemory(employeeId);
  const memParts = [];
  if (sharedMem.trim()) memParts.push('【团队共享记忆】\n' + sharedMem.trim());
  if (empMem.trim()) memParts.push('【本员工记忆】\n' + empMem.trim());
  if (memParts.length) out.MEMORY = memParts.join('\n\n');
  const skills = loadMergedSkills(employeeId);
  if (Object.keys(skills).length) out.SKILLS = skills;
  return out;
}

/**
 * 从模板构建 system prompt（人格 + 指令 + 生存法则 + 可选 USER/MEMORY/SKILLS）
 */
function buildSystemPrompt(employee, templates) {
  const parts = [];
  if (templates.SOUL) parts.push(templates.SOUL);
  if (templates.AGENTS) parts.push(templates.AGENTS);
  parts.push(SURVIVAL_RULES);
  if (templates.USER) parts.push('---\n' + templates.USER);
  if (templates.MEMORY) parts.push('---\n【长期记忆】\n' + templates.MEMORY.slice(0, 4000));
  if (templates.SKILLS && typeof templates.SKILLS === 'object' && Object.keys(templates.SKILLS).length > 0) {
    const skillBlocks = [];
    for (const [name, content] of Object.entries(templates.SKILLS)) {
      skillBlocks.push(`### 技能: ${name}\n${content.slice(0, 2000)}`);
    }
    parts.push('---\n【可用技能】\n' + skillBlocks.join('\n\n'));
  }
  return parts.join('\n\n');
}

/**
 * 调用 OpenAI 兼容 chat/completions API
 */
async function callOpenAICompat(baseUrl, apiKey, model, messages, maxTokens = 2048) {
  const url = (baseUrl || 'https://api.openai.com/v1').replace(/\/$/, '') + '/chat/completions';
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: apiKey ? `Bearer ${apiKey}` : '',
    },
    body: JSON.stringify({
      model: model || 'gpt-3.5-turbo',
      messages,
      max_tokens: maxTokens,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`LLM 请求失败: ${res.status} ${err}`);
  }
  const data = await res.json();
  const content = data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
  const usage = data.usage ? { input_tokens: data.usage.prompt_tokens || 0, output_tokens: data.usage.completion_tokens || 0 } : null;
  return { content: content || '', usage };
}

/**
 * 回复：使用主 config + 员工 config 合并后的配置；若已配置自有 LLM 则调用 API，否则返回占位（含生存法则）
 */
async function reply(employee, ownerId, content, getConfig) {
  const templates = loadEmployeeTemplates(employee.id);
  const safe = typeof content === 'string' ? content.trim() : '';
  const systemPrompt = buildSystemPrompt(employee, templates);

  const c = getMergedConfigForEmployee(employee.id, getConfig);
  const custom = (c && c.providers && c.providers.custom) || (c && c.customLLM);
  const hasCustom = c && c.ownerId === ownerId && custom && (custom.apiKey || custom.apiBase || custom.baseUrl);
  const defaults = (c && c.agents && c.agents.defaults) || {};
  const maxTokens = defaults.maxTokens != null ? defaults.maxTokens : 2048;

  if (hasCustom) {
    const baseUrl = custom.apiBase || custom.baseUrl || 'https://api.openai.com/v1';
    const apiKey = custom.apiKey || '';
    const model = custom.model || defaults.model || 'gpt-3.5-turbo';
    try {
      const messages = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: safe || '请说你好。' },
      ];
      const { content: replyContent, usage } = await callOpenAICompat(
        baseUrl,
        apiKey,
        model,
        messages,
        maxTokens
      );
      return { reply: replyContent || '（无回复内容）', usage };
    } catch (e) {
      return { reply: `${employee.name}：调用大模型时出错（${e.message}），请检查自有 LLM 配置。` + SURVIVAL_RULES, usage: null };
    }
  }

  const soulPreview = templates.SOUL ? templates.SOUL.slice(0, 200).replace(/\n/g, ' ') + '…' : '';
  if (!safe) {
    return { reply: `${employee.name}：请说明你的需求。${soulPreview ? `（人格：${soulPreview}）` : ''} ${SURVIVAL_RULES}`, usage: null };
  }
  return {
    reply: `${employee.name}（占位）：已收到「${safe.slice(0, 100)}」。请在设置中配置「自有 LLM」（API Key、Base URL、模型）以启用真实对话。${SURVIVAL_RULES}`,
    usage: null,
  };
}

module.exports = { SURVIVAL_RULES, reply, loadEmployeeTemplates, buildSystemPrompt };
