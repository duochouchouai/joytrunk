"""员工智能体上下文构建：从员工 workspace 组装 system prompt 与 messages。"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from joytrunk import paths
from joytrunk.agent.employee_config import get_memory_config

logger = logging.getLogger(__name__)

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
        """从 SYSTEM_PROMPT.md 模板 + memory.db 中各 category 的 item 列表替换占位符，拼出 system prompt。"""
        tpl_path = paths.get_bundled_templates_dir() / "SYSTEM_PROMPT.md"
        template_str = _read_optional(tpl_path)

        from joytrunk.agent.memory import get_store
        from joytrunk.agent.memory.store import PLACEHOLDER_CATEGORIES, get_category_item_summaries

        def format_item_list(summaries: list[str]) -> str:
            if not summaries:
                return "- （空）"
            return "\n".join("- " + s for s in summaries)

        placeholder_values: dict[str, str] = {}
        try:
            store = get_store(self.employee_id)
            store.load_existing()
            for placeholder_name, category_name in PLACEHOLDER_CATEGORIES.items():
                summaries = get_category_item_summaries(store, category_name)
                placeholder_values[placeholder_name] = format_item_list(summaries)
        except Exception:
            pass

        identity = placeholder_values.get("identity", "")
        style = placeholder_values.get("style", "")
        soul = placeholder_values.get("soul", "")
        user = placeholder_values.get("user", "")
        colleagues = placeholder_values.get("colleagues", "")
        agents = placeholder_values.get("agents", "")
        tools = placeholder_values.get("tools", "")

        builtin_tools_path = paths.get_bundled_templates_dir() / "BUILTIN_TOOLS.md"
        builtin_tools = _read_optional(builtin_tools_path)
        if builtin_tools.strip():
            tools_from_items = tools.strip() if (tools.strip() and tools.strip() != "- （空）") else ""
            tools = (tools_from_items + "\n\n" + builtin_tools.strip()).strip() if tools_from_items else builtin_tools.strip()
        if not tools.strip():
            tools = "- （空）"

        memory_block = ""
        skills_block = ""

        result = template_str
        for placeholder, value in [
            ("{{identity}}", identity or "- （空）"),
            ("{{style}}", style or ""),
            ("{{soul}}", soul or "- （空）"),
            ("{{user}}", user or "- （空）"),
            ("{{colleagues}}", colleagues or "- （空）"),
            ("{{agents}}", agents or "- （空）"),
            ("{{tools}}", tools),
            ("{{memory}}", memory_block or "- （空）"),
            ("{{skills}}", skills_block or "- （空）"),
        ]:
            if placeholder in result:
                result = result.replace(placeholder, value or "")
        return result.strip()

    async def build_system_prompt_with_retrieve(
        self, current_query: str, embed_client: Any | None = None, llm_chat: Any | None = None
    ) -> str:
        """先检索再拼 system prompt（未配置 embedding 时若配置了 LLM 则自动用 LLM 检索）。"""
        memory_cfg = get_memory_config(self.employee_id)
        if not current_query:
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
        except Exception as e:
            logger.warning(
                "Memory retrieve failed, building prompt without memory: %s", e
            )
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
        """若提供 embed_client 或 llm_chat 则先按 current_message 检索再拼 system，否则同 build_messages。"""
        if embed_client or llm_chat:
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
