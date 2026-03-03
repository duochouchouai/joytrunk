"""
记忆库入口：按员工返回 SQLite store，并确保 category/item 表就绪。

memory.db 结构：
- **category 表**：所有分类一张表，字段含 name、description、summary。LLM 可根据 summary 查找最相近的 category。
- **item 表**：条目由 LLM 或用户写入，通过 category_id 归属到某分类。查「负责人相关」时先查 category 得 user，再查 item 中 category_id=user；内容过长时用 RAG 再检索。

SYSTEM_PROMPT.md 中的占位符 {{identity}}、{{style}}、{{soul}}、{{user}}、{{colleagues}}、{{agents}}、{{tools}} 由对应 category 下的 **item** 列表填入（每条 item 的 summary 一行），实现长期记忆。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from joytrunk import paths
from joytrunk.agent.memory.sqlite.store import SQLiteMemoryStore

if TYPE_CHECKING:
    from joytrunk.agent.memory.sqlite.store import SQLiteMemoryStore as StoreType

# ---------------------------------------------------------------------------
# 常量：与 SYSTEM_PROMPT.md「你的记忆」表一致
# ---------------------------------------------------------------------------

# 初始 category 名称（与 SYSTEM_PROMPT.md 顺序一致：身份→沟通与风格→人格→…）
CATEGORY_NAMES = [
    "identity",
    "style",
    "soul",
    "user",
    "agents",
    "tools",
    "personal_info",
    "preferences",
    "relationships",
    "activities",
    "goals",
    "experiences",
    "knowledge",
    "opinions",
    "habits",
    "work_life",
]

# 占位符名 -> category name（SYSTEM_PROMPT 中 {{x}} 取自该 category 下所有 item 的 summary 列表）
PLACEHOLDER_CATEGORIES: dict[str, str] = {
    "identity": "identity",
    "style": "style",
    "soul": "soul",
    "user": "user",
    "colleagues": "relationships",
    "agents": "agents",
    "tools": "tools",
}

# category name -> 说明（供 LLM 与导出使用；含格式要求，便于填入 SYSTEM_PROMPT 占位符）
CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "identity": "身份（Identity）：本员工的个人信息、名字、自我介绍等。格式：标题：信息；如 名字：李太白",
    "style": "沟通与风格（Style）：补充的沟通与风格说明。格式：一条一条的简短说明，可直接作为列表项；如 回复时多用短句、避免客套话",
    "soul": "人格（Soul）：价值观与沟通方式。格式：一条一条的价值观或沟通方式，可直接作为列表项；如 以团队利益为先、计划先行",
    "user": "负责人/用户（User）：对负责人的了解。格式：标题：信息；如 偏好：喜欢简洁回复、负责人创造了我",
    "agents": "工作准则（Agents）：员工指令与行为。格式：一条一条的准则，可直接作为列表项；如 涉及删改前先确认",
    "tools": "工具（Tools）：工具使用方式与约束。格式：工具名或场景：说明；如 读文件：仅读工作区内文件",
    "personal_info": "身份/个人信息（与 identity 同义）：名字、自我介绍等。格式：标题：信息；如 名字：xxx",
    "preferences": "偏好与好恶。格式：对象或领域：偏好内容；如 沟通：偏好简洁",
    "relationships": "人际关系/同事（Colleagues）：与同事的协作与记忆。格式：与谁：关系或协作要点；如 与张三：常协作需求评审",
    "activities": "活动与行为。格式：时间或场景：活动描述；如 本周：完成需求文档",
    "goals": "目标与计划。格式：目标或计划：简述；如 Q1：完成上线",
    "experiences": "经历与事件。格式：事件：简述；如 上次发布：遇到回滚",
    "knowledge": "知识与技能。格式：领域或技能：简述；如 Python：常用写脚本",
    "opinions": "观点与态度。格式：主题：观点；如 技术选型：优先可维护性",
    "habits": "习惯与惯例。格式：习惯：描述；如 每日：先看邮件再开工",
    "work_life": "工作与生活。格式：方面：描述；如 作息：习惯晚间编码",
}

_store_cache: dict[str, "StoreType"] = {}


def get_category_item_summaries(store: "StoreType", category_name: str) -> list[str]:
    """返回该 category 下所有 item 的 summary 列表（用于填入 SYSTEM_PROMPT 占位符）。"""
    cat = store.memory_category_repo.get_category_by_name(category_name)
    if not cat:
        return []
    relations = store.category_item_repo.list_relations(where={"category_id": cat.id})
    summaries: list[str] = []
    for rel in relations:
        item = store.memory_item_repo.get_item(rel.item_id)
        if item and (item.summary or "").strip():
            summaries.append((item.summary or "").strip())
    return summaries


def ensure_all_categories(employee_id: str, store: "StoreType") -> None:
    """确保 CATEGORY_NAMES 中的 category 均存在；不存在则创建（不读旧 .md/种子）。"""
    for name in CATEGORY_NAMES:
        desc = CATEGORY_DESCRIPTIONS.get(name, name)
        existing = store.memory_category_repo.get_category_by_name(name)
        if not existing:
            store.memory_category_repo.get_or_create_category(
                name=name,
                description=desc,
                summary=None,
            )


def get_store(employee_id: str) -> "StoreType":
    """获取该员工的记忆库；若尚未打开则创建并建表，并确保所有 category 存在。"""
    if employee_id in _store_cache:
        return _store_cache[employee_id]
    db_path = paths.get_employee_memory_db_path(employee_id)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    store = SQLiteMemoryStore(dsn=f"sqlite:///{db_path.as_posix()}")
    _store_cache[employee_id] = store
    ensure_all_categories(employee_id, store)
    return store


__all__ = [
    "get_store",
    "ensure_all_categories",
    "get_category_item_summaries",
    "PLACEHOLDER_CATEGORIES",
    "CATEGORY_NAMES",
    "CATEGORY_DESCRIPTIONS",
]
