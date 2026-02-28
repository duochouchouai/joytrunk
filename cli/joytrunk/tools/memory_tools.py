"""记忆工具：save_memory、search_memory（可选，记忆启用时注册）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from joytrunk.tools.base import Tool


class SaveMemoryTool(Tool):
    """将一段内容写入当前员工的长期记忆。"""

    def __init__(self, workspace: Path, allowed_dir: Path | None, employee_id: str):
        self._workspace = workspace
        self._allowed_dir = allowed_dir
        self._employee_id = employee_id

    @property
    def name(self) -> str:
        return "save_memory"

    @property
    def description(self) -> str:
        return "Save a piece of information into your long-term memory (e.g. user preference, fact, or instruction)."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The information to remember (concise, self-contained)."},
                "category": {
                    "type": "string",
                    "description": "Optional category: soul, user, agents, or tools.",
                    "enum": ["soul", "user", "agents", "tools"],
                },
            },
            "required": ["content"],
        }

    async def execute(self, content: str, category: str | None = None, **kwargs: Any) -> str:
        try:
            from joytrunk.agent.memory import get_store
            from joytrunk.agent.employee_config import get_llm_params, get_memory_config, get_merged_config_for_employee
            store = get_store(self._employee_id)
            memory_cfg = get_memory_config(self._employee_id)
            config = get_merged_config_for_employee(self._employee_id)
            owner_id = config.get("ownerId") or ""
            llm_params = get_llm_params(self._employee_id, owner_id)
            emb = (memory_cfg.get("embedding") or {})
            embed_client = None
            base_url = emb.get("base_url") or llm_params.get("base_url")
            if base_url:
                from joytrunk.agent.memory.embedding_client import HTTPEmbeddingClient
                embed_client = HTTPEmbeddingClient(
                    base_url=base_url,
                    api_key=emb.get("api_key") or llm_params.get("api_key") or "",
                    embed_model=emb.get("embed_model") or "embo-01",
                )
            if not embed_client:
                class Dummy:
                    async def embed(self, inputs): return [[0.0] * 384 for _ in inputs]
                embed_client = Dummy()
            async def llm_chat(msgs):
                from joytrunk.agent.provider import chat as provider_chat, chat_via_router
                if llm_params["source"] == "custom":
                    r = await provider_chat(llm_params["base_url"], llm_params["api_key"], llm_params["model"], msgs)
                else:
                    r = await chat_via_router(llm_params["gateway_base_url"], llm_params["owner_id"], llm_params["model"], msgs)
                return (r.content or "").strip()
            res = store.resource_repo.create_resource(
                url="tool:save_memory", modality="conversation", local_path="", caption=content, embedding=None
            )
            vec = (await embed_client.embed([content]))[0]
            cat_names = [category] if category else ["user"]
            name_to_id = {}
            for c in ("soul", "user", "agents", "tools"):
                cat = store.memory_category_repo.get_category_by_name(c)
                if cat:
                    name_to_id[c] = cat.id
            item = store.memory_item_repo.create_item(
                resource_id=res.id, memory_type="profile", summary=content, embedding=vec, reinforce=False
            )
            for cn in cat_names:
                cid = name_to_id.get(cn)
                if cid:
                    store.category_item_repo.link_item_category(item.id, cid)
            return f"Saved to memory: {content[:100]}..."
        except Exception as e:
            return f"Error saving memory: {e}"


class SearchMemoryTool(Tool):
    """在当前员工的长期记忆中检索与查询相关的内容。"""

    def __init__(self, workspace: Path, allowed_dir: Path | None, employee_id: str):
        self._workspace = workspace
        self._allowed_dir = allowed_dir
        self._employee_id = employee_id

    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def description(self) -> str:
        return "Search your long-term memory for information relevant to the query."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query."}},
            "required": ["query"],
        }

    async def execute(self, query: str, **kwargs: Any) -> str:
        try:
            from joytrunk.agent.memory.retrieve import retrieve
            from joytrunk.agent.employee_config import get_memory_config, get_llm_params, get_merged_config_for_employee
            memory_cfg = get_memory_config(self._employee_id)
            config = get_merged_config_for_employee(self._employee_id)
            owner_id = config.get("ownerId") or ""
            llm_params = get_llm_params(self._employee_id, owner_id)
            method = (memory_cfg.get("retrieve") or {}).get("method") or "rag"
            embed_client = None
            llm_chat = None
            if method == "rag":
                emb = (memory_cfg.get("embedding") or {})
                base_url = emb.get("base_url") or llm_params.get("base_url")
                if base_url:
                    from joytrunk.agent.memory.embedding_client import HTTPEmbeddingClient
                    embed_client = HTTPEmbeddingClient(
                        base_url=base_url, api_key=emb.get("api_key") or llm_params.get("api_key") or "",
                        embed_model=emb.get("embed_model") or "embo-01",
                    )
                if not embed_client:
                    method = "llm"
            if method == "llm":
                async def _chat(msgs):
                    from joytrunk.agent.provider import chat as provider_chat, chat_via_router
                    if llm_params["source"] == "custom":
                        r = await provider_chat(llm_params["base_url"], llm_params["api_key"], llm_params["model"], msgs)
                    else:
                        r = await chat_via_router(llm_params["gateway_base_url"], llm_params["owner_id"], llm_params["model"], msgs)
                    return (r.content or "").strip()
                llm_chat = _chat
            if (method == "rag" and not embed_client) or (method == "llm" and not llm_chat):
                return "Memory search is not available: configure embedding (for RAG) or LLM (for LLM-based search) in memory settings."
            result = await retrieve(
                self._employee_id, query, method=method,
                embed_client=embed_client, llm_chat=llm_chat,
                top_k_item=10,
            )
            items = result.get("items") or []
            if not items:
                return "No relevant memories found."
            return "\n".join((it.get("summary") or "") for it in items[:10])
        except Exception as e:
            return f"Error searching memory: {e}"


__all__ = ["SaveMemoryTool", "SearchMemoryTool"]
