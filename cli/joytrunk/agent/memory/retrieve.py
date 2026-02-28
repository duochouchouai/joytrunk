"""Retrieve 流程：RAG（向量）与 LLM 排序双路径。"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from joytrunk.agent.memory.prompts import (
    LLM_CATEGORY_RANKER_PROMPT,
    LLM_ITEM_RANKER_PROMPT,
    LLM_RESOURCE_RANKER_PROMPT,
)
from joytrunk.agent.memory.store import get_store
from joytrunk.agent.memory.vector import cosine_topk

logger = logging.getLogger(__name__)


def _extract_json_blob(raw: str) -> str:
    """从 LLM 回复中取出 JSON 块。"""
    if not raw:
        return "{}"
    raw = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if m:
        return m.group(1).strip()
    for start in ("{", "["):
        i = raw.find(start)
        if i != -1:
            return raw[i:]
    return raw


def _model_dump_no_embedding(obj: Any) -> dict[str, Any]:
    """转为 dict 并去掉 embedding 字段。"""
    if hasattr(obj, "model_dump"):
        d = obj.model_dump()
    elif hasattr(obj, "__dict__"):
        d = dict(obj.__dict__)
    else:
        d = dict(obj)
    d.pop("embedding", None)
    return d


def _materialize(
    hits: list[tuple[str, float]],
    pool: dict[str, Any],
    summary_lookup: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    out = []
    for _id, score in hits:
        obj = pool.get(_id)
        if not obj:
            continue
        d = _model_dump_no_embedding(obj)
        d["score"] = float(score)
        if summary_lookup and _id in summary_lookup:
            d["summary"] = summary_lookup[_id]
        out.append(d)
    return out


async def retrieve_rag(
    employee_id: str,
    query: str,
    *,
    embed_client: Any,
    top_k_category: int = 3,
    top_k_item: int = 10,
    top_k_resource: int = 5,
    item_ranking: str = "similarity",
    recency_decay_days: float = 30.0,
) -> dict[str, Any]:
    """RAG 检索：query 向量 + category summary 现场 embed + item 向量检索。"""
    store = get_store(employee_id)
    store.load_existing()
    qvec = (await embed_client.embed([query]))[0]
    categories_pool = store.memory_category_repo.list_categories()
    category_hits: list[tuple[str, float]] = []
    summary_lookup: dict[str, str] = {}
    if categories_pool:
        entries = [(cid, cat.summary) for cid, cat in categories_pool.items() if cat.summary]
        if entries:
            texts = [e[1] for e in entries]
            vecs = await embed_client.embed(texts)
            corpus = [(e[0], v) for e, v in zip(entries, vecs, strict=False)]
            category_hits = cosine_topk(qvec, corpus, k=top_k_category)
            summary_lookup = {cid: s for cid, s in entries}
    item_hits = store.memory_item_repo.vector_search_items(
        qvec, top_k_item, ranking=item_ranking, recency_decay_days=recency_decay_days
    )
    items_pool = store.memory_item_repo.list_items()
    resource_hits: list[tuple[str, float]] = []
    resources_pool = store.resource_repo.list_resources()
    corpus_res = [(rid, r.embedding) for rid, r in resources_pool.items() if r.embedding]
    if corpus_res:
        resource_hits = cosine_topk(qvec, corpus_res, k=top_k_resource)
    return {
        "categories": _materialize(category_hits, categories_pool, summary_lookup),
        "items": _materialize(item_hits, items_pool),
        "resources": _materialize(resource_hits, resources_pool),
    }


async def retrieve_llm(
    employee_id: str,
    query: str,
    *,
    llm_chat: Any,
    top_k_category: int = 3,
    top_k_item: int = 10,
    top_k_resource: int = 5,
) -> dict[str, Any]:
    """LLM 检索：用 LLM 对 category / item / resource 排序。"""
    store = get_store(employee_id)
    store.load_existing()
    categories_pool = store.memory_category_repo.list_categories()
    if not categories_pool:
        return {"categories": [], "items": [], "resources": []}
    lines = []
    for cid, cat in categories_pool.items():
        lines.append(f"ID: {cid}\nName: {cat.name}\nDescription: {cat.description}")
        if cat.summary:
            lines.append(f"Summary: {cat.summary}")
        lines.append("---")
    categories_data = "\n".join(lines)
    prompt_cat = LLM_CATEGORY_RANKER_PROMPT.format(
        query=query, top_k=top_k_category, categories_data=categories_data
    )
    try:
        resp_cat = await llm_chat([{"role": "user", "content": prompt_cat}])
    except Exception as e:
        logger.warning("LLM category rank failed: %s", e)
        resp_cat = "{}"
    cat_ids = _parse_json_list(_extract_json_blob(resp_cat or ""), "categories")
    category_hits_objs = []
    for cid in cat_ids:
        if cid in categories_pool:
            category_hits_objs.append(_model_dump_no_embedding(categories_pool[cid]))
    relations = store.category_item_repo.list_relations()
    item_ids_in_cats = {r.item_id for r in relations if r.category_id in cat_ids}
    items_pool = store.memory_item_repo.list_items()
    items_in_cats = {iid: items_pool[iid] for iid in item_ids_in_cats if iid in items_pool}
    if not items_in_cats:
        return {
            "categories": category_hits_objs,
            "items": [],
            "resources": [],
        }
    lines_item = []
    for iid, item in items_in_cats.items():
        lines_item.append(f"ID: {iid}\nType: {item.memory_type}\nSummary: {item.summary}\n---")
    items_data = "\n".join(lines_item)
    relevant_cats_str = "\n".join(
        f"- {categories_pool[c].name}: {categories_pool[c].summary or ''}"
        for c in cat_ids if c in categories_pool
    )
    prompt_item = LLM_ITEM_RANKER_PROMPT.format(
        query=query,
        top_k=top_k_item,
        relevant_categories=relevant_cats_str,
        items_data=items_data,
    )
    try:
        resp_item = await llm_chat([{"role": "user", "content": prompt_item}])
    except Exception as e:
        logger.warning("LLM item rank failed: %s", e)
        resp_item = "{}"
    item_ids = _parse_json_list(_extract_json_blob(resp_item or ""), "items")
    item_hits_objs = []
    for iid in item_ids:
        if iid in items_pool:
            item_hits_objs.append(_model_dump_no_embedding(items_pool[iid]))
    resource_pool = store.resource_repo.list_resources()
    resource_ids_from_items = {
        items_pool[i].resource_id for i in item_ids
        if i in items_pool and items_pool[i].resource_id
    }
    resources_subset = {
        rid: resource_pool[rid] for rid in resource_ids_from_items if rid in resource_pool
    }
    if not resources_subset:
        return {"categories": category_hits_objs, "items": item_hits_objs, "resources": []}
    lines_res = []
    for rid, res in resources_subset.items():
        lines_res.append(f"ID: {rid}\nURL: {res.url}\nModality: {res.modality}")
        if res.caption:
            lines_res.append(f"Caption: {res.caption}")
        lines_res.append("---")
    context_info = "Relevant categories and items above."
    prompt_res = LLM_RESOURCE_RANKER_PROMPT.format(
        query=query,
        top_k=top_k_resource,
        context_info=context_info,
        resources_data="\n".join(lines_res),
    )
    try:
        resp_res = await llm_chat([{"role": "user", "content": prompt_res}])
    except Exception as e:
        logger.warning("LLM resource rank failed: %s", e)
        resp_res = "{}"
    res_ids = _parse_json_list(_extract_json_blob(resp_res or ""), "resources")
    resource_hits_objs = [
        _model_dump_no_embedding(resource_pool[rid])
        for rid in res_ids if rid in resource_pool
    ]
    return {
        "categories": category_hits_objs,
        "items": item_hits_objs,
        "resources": resource_hits_objs,
    }


def _parse_json_list(blob: str, key: str) -> list[str]:
    try:
        data = json.loads(blob)
        lst = data.get(key)
        if isinstance(lst, list):
            return [x for x in lst if isinstance(x, str)]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


async def retrieve(
    employee_id: str,
    query: str,
    *,
    method: str = "rag",
    embed_client: Any | None = None,
    llm_chat: Any | None = None,
    top_k_category: int = 3,
    top_k_item: int = 10,
    top_k_resource: int = 5,
    item_ranking: str = "similarity",
    recency_decay_days: float = 30.0,
) -> dict[str, Any]:
    """统一检索入口：method in ('rag','llm')。"""
    if method == "llm":
        if not llm_chat:
            raise ValueError("llm_chat required for method=llm")
        return await retrieve_llm(
            employee_id,
            query,
            llm_chat=llm_chat,
            top_k_category=top_k_category,
            top_k_item=top_k_item,
            top_k_resource=top_k_resource,
        )
    if not embed_client:
        raise ValueError("embed_client required for method=rag")
    return await retrieve_rag(
        employee_id,
        query,
        embed_client=embed_client,
        top_k_category=top_k_category,
        top_k_item=top_k_item,
        top_k_resource=top_k_resource,
        item_ranking=item_ranking,
        recency_decay_days=recency_decay_days,
    )


__all__ = ["retrieve", "retrieve_rag", "retrieve_llm"]
