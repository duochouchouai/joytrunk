"""员工智能体上下文构建：从员工 workspace 组装 system prompt 与 messages（参考 nanobot.agent.context）。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from joytrunk import paths
from joytrunk.agent.employee_config import get_memory_config

# 员工生存法则（product.md §9），与 gateway agent.js 一致
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

    def build_system_prompt(
        self,
        current_query: str | None = None,
        memory_retrieve_result: dict[str, Any] | None = None,
    ) -> str:
        """人格 + 指令 + 生存法则 + USER + MEMORY + SKILLS。若提供 memory_retrieve_result 则用于「本员工记忆」段落。"""
        parts: list[str] = []
        memory_cfg = get_memory_config(self.employee_id)
        use_memory = memory_cfg.get("enabled") is True
        if use_memory:
            try:
                from joytrunk.agent.memory import get_store
                store = get_store(self.employee_id)
                store.load_existing()
                for name in ("soul", "user", "agents", "tools"):
                    cat = store.memory_category_repo.get_category_by_name(name)
                    if cat and (cat.summary or "").strip():
                        parts.append((cat.summary or "").strip())
                    else:
                        f = self.employee_dir / {"soul": "SOUL.md", "user": "USER.md", "agents": "AGENTS.md", "tools": "TOOLS.md"}[name]
                        if f.exists():
                            content = _read_optional(f)
                            if content:
                                parts.append(content)
            except Exception:
                use_memory = False
        if not use_memory:
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
        if memory_retrieve_result and (memory_retrieve_result.get("items") or memory_retrieve_result.get("categories")):
            live = []
            for c in memory_retrieve_result.get("categories") or []:
                s = c.get("summary") or c.get("description") or ""
                if s:
                    live.append(s[:500])
            for it in memory_retrieve_result.get("items") or []:
                live.append((it.get("summary") or "")[:300])
            if live:
                mem_parts.append("【本员工记忆】\n" + "\n".join(live))
        if emp_mem.strip() and not (memory_retrieve_result and memory_retrieve_result.get("items")):
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

    async def build_system_prompt_with_retrieve(
        self, current_query: str, embed_client: Any | None = None, llm_chat: Any | None = None
    ) -> str:
        """若启用记忆且配置了检索，则先检索再拼 system prompt。未配置 embedding 时若配置了 LLM 则自动用 LLM 检索。"""
        memory_cfg = get_memory_config(self.employee_id)
        if not memory_cfg.get("enabled") or not current_query:
            return self.build_system_prompt()
        method = (memory_cfg.get("retrieve") or {}).get("method") or "rag"
        if method == "rag" and not embed_client and llm_chat:
            method = "llm"
        item_cfg = (memory_cfg.get("retrieve") or {}).get("item") or {}
        cat_cfg = (memory_cfg.get("retrieve") or {}).get("category") or {}
        try:
            from joytrunk.agent.memory.retrieve import retrieve
            result = await retrieve(
                self.employee_id,
                current_query,
                method=method,
                embed_client=embed_client,
                llm_chat=llm_chat,
                top_k_category=cat_cfg.get("top_k", 3),
                top_k_item=item_cfg.get("top_k", 10),
                item_ranking=item_cfg.get("ranking", "similarity"),
                recency_decay_days=item_cfg.get("recency_decay_days", 30.0),
            )
            return self.build_system_prompt(memory_retrieve_result=result)
        except Exception:
            return self.build_system_prompt()

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

    async def build_messages_with_memory(
        self,
        history: list[dict[str, Any]],
        current_message: str,
        channel: str = "cli",
        chat_id: str = "cli",
        embed_client: Any | None = None,
        llm_chat: Any | None = None,
    ) -> list[dict[str, Any]]:
        """若启用记忆则先按 current_message 检索再拼 system，否则同 build_messages。"""
        memory_cfg = get_memory_config(self.employee_id)
        if memory_cfg.get("enabled") and (embed_client or llm_chat):
            system = await self.build_system_prompt_with_retrieve(
                current_message or "", embed_client=embed_client, llm_chat=llm_chat
            )
        else:
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
