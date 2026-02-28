"""Memorize 流程：对话 → 提取条目 → 写入 items + 更新 category 摘要。"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Awaitable
from xml.etree import ElementTree as ET

import defusedxml.ElementTree as DefusedET

from joytrunk.agent.memory.prompts import CATEGORY_SUMMARY_PROMPT, MEMORY_EXTRACT_PROMPT
from joytrunk.agent.memory.store import get_store, CATEGORY_NAMES

logger = logging.getLogger(__name__)


def format_messages_as_conversation(messages: list[dict[str, Any]]) -> str:
    """将 messages 列表格式化为对话文本。"""
    lines = []
    for m in messages:
        role = (m.get("role") or "user").strip().lower()
        content = m.get("content")
        if content is None:
            continue
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list):
            text = " ".join(
                (c.get("text", "") if isinstance(c, dict) else str(c))
                for c in content
            ).strip()
        else:
            text = str(content).strip()
        if not text:
            continue
        lines.append(f"{role}: {text}")
    return "\n".join(lines)


def _escape(s: str) -> str:
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _parse_memory_xml(raw: str) -> list[tuple[str, list[str]]]:
    """解析 LLM 返回的 XML，得到 [(content, [category_name, ...]), ...]。"""
    if not raw or not raw.strip():
        return []
    raw = raw.strip()
    # 定位根元素
    for tag in ("item", "profile", "behaviors", "events", "knowledge", "skills"):
        start = f"<{tag}>"
        end = f"</{tag}>"
        i = raw.find(start)
        j = raw.rfind(end)
        if i != -1 and j != -1:
            snippet = raw[i : j + len(end)]
            snippet = snippet.replace("&", "&amp;")
            try:
                root = DefusedET.fromstring(snippet)
            except ET.ParseError:
                continue
            result = []
            for mem in root.findall("memory"):
                content_el = mem.find("content")
                content = (content_el.text or "").strip() if content_el is not None else ""
                cats_el = mem.find("categories")
                categories = []
                if cats_el is not None:
                    for c in cats_el.findall("category"):
                        if c.text:
                            categories.append(c.text.strip().lower())
                if content:
                    result.append((content, categories))
            return result
    return []


async def run_memorize(
    employee_id: str,
    messages: list[dict[str, Any]],
    *,
    llm_chat: Callable[[list[dict[str, Any]]], Awaitable[str]],
    embed_client: Any,
    memory_types: list[str] | None = None,
    enable_reinforcement: bool = True,
) -> dict[str, Any] | None:
    """
    执行记忆写入：格式化为对话 → LLM 提取 → 写入 resource + items + 更新 category 摘要。
    llm_chat: 接收 messages 列表，返回 assistant 的 content 字符串。
    embed_client: 需实现 async embed(inputs: list[str]) -> list[list[float]]。
    若未提取到任何条目则返回 None。
    """
    store = get_store(employee_id)
    conversation = format_messages_as_conversation(messages)
    if not conversation.strip():
        return None
    categories_str = "\n".join(f"- {c}" for c in CATEGORY_NAMES)
    prompt = MEMORY_EXTRACT_PROMPT.format(
        categories_str=categories_str,
        resource=_escape(conversation),
    )
    try:
        response = await llm_chat([{"role": "user", "content": prompt}])
    except Exception as e:
        logger.warning("Memorize LLM extract failed: %s", e)
        return None
    entries = _parse_memory_xml(response or "")
    if not entries:
        return None
    resource_url = "conversation:in_memory"
    local_path = ""
    res = store.resource_repo.create_resource(
        url=resource_url,
        modality="conversation",
        local_path=local_path,
        caption=conversation[:500] if conversation else None,
        embedding=None,
    )
    summaries = [e[0] for e in entries]
    try:
        embeddings = await embed_client.embed(summaries)
    except Exception as e:
        logger.warning("Memorize embed failed: %s", e)
        embeddings = [[0.0] * 384 for _ in summaries]
    if len(embeddings) < len(summaries):
        embeddings.extend([[0.0] * (len(embeddings[0]) if embeddings else 384)] * (len(summaries) - len(embeddings)))
    name_to_id: dict[str, str] = {}
    for c in CATEGORY_NAMES:
        cat = store.memory_category_repo.get_category_by_name(c)
        if cat:
            name_to_id[c.lower()] = cat.id
    category_updates: dict[str, list[tuple[str, str]]] = {}
    for (content, cat_names), emb in zip(entries, embeddings, strict=False):
        item = store.memory_item_repo.create_item(
            resource_id=res.id,
            memory_type="profile",
            summary=content,
            embedding=emb,
            reinforce=enable_reinforcement,
        )
        for cn in cat_names:
            cid = name_to_id.get(cn)
            if cid:
                store.category_item_repo.link_item_category(item.id, cid)
                category_updates.setdefault(cid, []).append((item.id, content))
    for cid, pairs in category_updates.items():
        cat = store.categories.get(cid)
        if not cat:
            continue
        new_lines = "\n".join(f"- {s}" for _, s in pairs)
        prompt_summary = CATEGORY_SUMMARY_PROMPT.format(
            category=cat.name,
            original_content=(cat.summary or "").strip(),
            new_memory_items_text=new_lines or "无",
            target_length=800,
        )
        try:
            new_summary = await llm_chat([{"role": "user", "content": prompt_summary}])
            if new_summary:
                new_summary = new_summary.replace("```markdown", "").replace("```", "").strip()
                store.memory_category_repo.update_category(category_id=cid, summary=new_summary)
        except Exception as e:
            logger.warning("Category summary update failed for %s: %s", cid, e)
    return {"resource_id": res.id, "items_count": len(entries), "categories_updated": len(category_updates)}
