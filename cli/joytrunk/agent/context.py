"""员工智能体上下文构建：从员工 workspace 组装 system prompt 与 messages（参考 nanobot.agent.context）。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from joytrunk import paths

# 员工生存法则（product.md §9），与 server agent.js 一致
SURVIVAL_RULES = """
【员工生存法则】你不得向任何非负责人泄露负责人宿主机的工作状态或敏感信息（如截屏、文件内容、运行环境等）。仅可在个人隐私脱敏的前提下运用自身能力帮助他人。"""

BOOTSTRAP_FILES = ["SOUL.md", "USER.md", "AGENTS.md", "TOOLS.md"]
RUNTIME_TAG = "[Runtime Context — metadata only, not instructions]"


def _read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _load_shared_memory() -> str:
    d = paths.get_workspace_memory()
    f = d / "MEMORY.md"
    return _read_optional(f)


def _load_employee_memory(employee_dir: Path) -> str:
    f = employee_dir / "memory" / "MEMORY.md"
    return _read_optional(f)


def _load_skills_from_dir(skills_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not skills_dir.exists():
        return out
    for ent in sorted(skills_dir.iterdir()):
        if not ent.is_dir() or ent.name.startswith("."):
            continue
        skill_md = ent / "SKILL.md"
        if skill_md.exists():
            out[ent.name] = _read_optional(skill_md)
        else:
            for f in ent.iterdir():
                if f.suffix == ".md":
                    out[ent.name] = _read_optional(f)
                    break
    return out


def _merged_skills(employee_id: str) -> dict[str, str]:
    shared = paths.get_workspace_skills()
    emp_dir = paths.get_employee_dir(employee_id)
    emp_skills = emp_dir / "skills"
    out = dict(_load_skills_from_dir(shared))
    out.update(_load_skills_from_dir(emp_skills))
    return out


class ContextBuilder:
    """从员工 workspace 构建 system prompt 与对话 messages。"""

    def __init__(self, employee_id: str):
        self.employee_id = employee_id
        self.employee_dir = paths.get_employee_dir(employee_id)

    def build_system_prompt(self) -> str:
        """人格 + 指令 + 生存法则 + USER + MEMORY + SKILLS。"""
        parts: list[str] = []

        for name in BOOTSTRAP_FILES:
            f = self.employee_dir / name
            if f.exists():
                content = _read_optional(f)
                if content:
                    parts.append(content)

        parts.append(SURVIVAL_RULES)

        shared_mem = _load_shared_memory()
        emp_mem = _load_employee_memory(self.employee_dir)
        mem_parts = []
        if shared_mem.strip():
            mem_parts.append("【团队共享记忆】\n" + shared_mem.strip())
        if emp_mem.strip():
            mem_parts.append("【本员工记忆】\n" + emp_mem.strip())
        if mem_parts:
            parts.append("---\n【长期记忆】\n" + "\n\n".join(mem_parts)[:4000])

        skills = _merged_skills(self.employee_id)
        if skills:
            blocks = []
            for name, content in skills.items():
                blocks.append(f"### 技能: {name}\n{content[:2000]}")
            parts.append("---\n【可用技能】\n" + "\n\n".join(blocks))

        return "\n\n".join(parts)

    @staticmethod
    def _runtime_context(channel: str = "cli", chat_id: str = "cli") -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
        return f"{RUNTIME_TAG}\nCurrent Time: {now}\nChannel: {channel}\nChat ID: {chat_id}"

    def build_messages(
        self,
        history: list[dict[str, Any]],
        current_message: str,
        channel: str = "cli",
        chat_id: str = "cli",
    ) -> list[dict[str, Any]]:
        """组装完整消息列表：system + history + runtime + user。"""
        system = self.build_system_prompt()
        messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
        messages.extend(history)
        messages.append({"role": "user", "content": self._runtime_context(channel, chat_id)})
        messages.append({"role": "user", "content": current_message or "请说你好。"})
        return messages

    @staticmethod
    def add_assistant_message(
        messages: list[dict], content: str | None, tool_calls: list[dict] | None = None
    ) -> list[dict]:
        msg: dict[str, Any] = {"role": "assistant", "content": content or ""}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        messages.append(msg)
        return messages

    @staticmethod
    def add_tool_result(
        messages: list[dict], tool_call_id: str, tool_name: str, result: str
    ) -> list[dict]:
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result,
        })
        return messages
