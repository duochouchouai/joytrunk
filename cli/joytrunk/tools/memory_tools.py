"""记忆工具：save_memory、search_memory（可选，记忆启用时注册）。"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from joytrunk.agent.memory.store import CATEGORY_NAMES
from joytrunk.tools.base import Tool

logger = logging.getLogger(__name__)

# 写入对话历史的简短提示，避免把 API/embedding 技术错误写入 owner.json
MSG_MEMORY_SEARCH_UNAVAILABLE = "记忆检索暂时不可用，请依据当前对话与下方长期记忆继续回答。"
MSG_MEMORY_SAVE_UNAVAILABLE = "记忆保存暂时不可用，请稍后再试。"


def _get_embed_client(employee_id: str):
    """获取该员工的 embedding 客户端；无配置时返回零向量的 Dummy。"""
    from joytrunk.agent.employee_config import get_llm_params, get_memory_config, get_merged_config_for_employee
    memory_cfg = get_memory_config(employee_id)
    config = get_merged_config_for_employee(employee_id)
    owner_id = config.get("ownerId") or ""
    llm_params = get_llm_params(employee_id, owner_id)
    emb = memory_cfg.get("embedding") or {}
    base_url = emb.get("base_url") or llm_params.get("base_url")
    if not base_url:
        class Dummy:
            async def embed(self, inputs, embed_type=None):
                return [[0.0] * 1536 for _ in inputs]
        return Dummy()
    from joytrunk.agent.memory.embedding_client import HTTPEmbeddingClient
    group_id = (emb.get("group_id") or os.environ.get("MINIMAX_GROUP_ID") or "").strip()
    return HTTPEmbeddingClient(
        base_url=base_url,
        api_key=emb.get("api_key") or llm_params.get("api_key") or "",
        embed_model=emb.get("embed_model") or "embo-01",
        group_id=group_id or None,
    )


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
        return (
            "Save one fact or preference into your long-term memory. "
            "Content must be a single short sentence (e.g. '名字：李太白' or '我叫李太白，是团队的一员'). "
            "Do not write essays, analysis, or long paragraphs."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "One short sentence only (e.g. '名字：李太白' or '我叫李太白，是团队的一员'). No essays or analysis.",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category for this memory.",
                    "enum": list(CATEGORY_NAMES),
                },
            },
            "required": ["content"],
        }

    async def execute(self, content: str, category: str | None = None, **kwargs: Any) -> str:
        try:
            from joytrunk.agent.memory import get_store
            store = get_store(self._employee_id)
            store.load_existing()
            embed_client = _get_embed_client(self._employee_id)
            vec = (await embed_client.embed([content], embed_type="db"))[0]
            item = store.memory_item_repo.create_item(
                resource_id=None,
                memory_type="profile",
                summary=content,
                embedding=vec,
                reinforce=False,
            )
            cat_name = category or "user"
            cat = store.memory_category_repo.get_category_by_name(cat_name)
            if cat:
                store.category_item_repo.link_item_category(item.id, cat.id)
            content_preview = content if len(content) <= 100 else content[:100] + "..."
            return f"已写入长期记忆。分类：{cat_name}。内容：{content_preview}"
        except Exception as e:
            logger.warning("Save memory failed (embedding/store error): %s", e)
            return MSG_MEMORY_SAVE_UNAVAILABLE


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
                    group_id = (emb.get("group_id") or os.environ.get("MINIMAX_GROUP_ID") or "").strip()
                    embed_client = HTTPEmbeddingClient(
                        base_url=base_url, api_key=emb.get("api_key") or llm_params.get("api_key") or "",
                        embed_model=emb.get("embed_model") or "embo-01",
                        group_id=group_id or None,
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
            logger.warning("Search memory failed (embedding/retrieve error): %s", e)
            return MSG_MEMORY_SEARCH_UNAVAILABLE


__all__ = ["SaveMemoryTool", "SearchMemoryTool"]
