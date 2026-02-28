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

RUNTIME_TAG = "[Runtime Context — metadata only, not instructions]"

# 记忆机制说明：告知模型可主动查阅与写入记忆
MEMORY_SYSTEM_INSTRUCTION = """【记忆工具说明】下方「本员工记忆」为按当前对话自动检索出的内容，每轮对话结束后系统也会自动提取要点写入。如需主动查阅：请使用 search_memory 工具，传入要查的问题或关键词。如需主动保存当前对话中的重要信息：请使用 save_memory 工具。"""


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
        """从 SYSTEM_PROMPT.md 模板 + DB 中 soul/user/agents/tools 的 summary 替换占位符，拼出 system prompt。"""
        # 1. 加载模板：优先员工目录，否则包内
        tpl_path = self.employee_dir / "SYSTEM_PROMPT.md"
        if not tpl_path.exists():
            tpl_path = paths.get_bundled_templates_dir() / "SYSTEM_PROMPT.md"
        template_str = _read_optional(tpl_path)
        if not template_str.strip():
            template_str = "{{soul}}\n\n{{user}}\n\n{{agents}}\n\n{{tools}}\n\n{{survival_rules}}\n\n{{memory}}\n\n{{skills}}"

        # 2. 从 store 取 soul/user/agents/tools 的 summary
        soul = user = agents = tools = ""
        try:
            from joytrunk.agent.memory import get_store
            store = get_store(self.employee_id)
            store.load_existing()
            for name in ("soul", "user", "agents", "tools"):
                cat = store.memory_category_repo.get_category_by_name(name)
                val = (cat.summary or "").strip() if cat else ""
                if name == "soul":
                    soul = val
                elif name == "user":
                    user = val
                elif name == "agents":
                    agents = val
                else:
                    tools = val
        except Exception:
            pass

        # 3. 长期记忆段落（与现逻辑一致）
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
        memory_block = ""
        if mem_parts:
            memory_block = MEMORY_SYSTEM_INSTRUCTION + "\n\n---\n【长期记忆】\n" + "\n\n".join(mem_parts)[:4000]

        # 4. 技能块
        skills = _merged_skills(self.employee_id)
        skills_block = ""
        if skills:
            blocks = [f"### 技能: {name}\n{content[:2000]}" for name, content in skills.items()]
            skills_block = "---\n【可用技能】\n" + "\n\n".join(blocks)

        # 5. 占位符替换
        result = template_str
        for placeholder, value in [
            ("{{soul}}", soul),
            ("{{user}}", user),
            ("{{agents}}", agents),
            ("{{tools}}", tools),
            ("{{survival_rules}}", SURVIVAL_RULES.strip()),
            ("{{memory}}", memory_block),
            ("{{skills}}", skills_block),
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
