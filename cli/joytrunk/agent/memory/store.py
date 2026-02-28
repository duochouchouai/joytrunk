"""记忆库入口：按员工返回 SQLite store，并从 .md bootstrap categories。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from joytrunk import paths
from joytrunk.agent.memory.sqlite.store import SQLiteMemoryStore

if TYPE_CHECKING:
    from joytrunk.agent.memory.sqlite.store import SQLiteMemoryStore as StoreType

logger = logging.getLogger(__name__)

# 固定 category 名与 .md 文件对应（SOUL/USER/AGENTS/TOOLS）
CATEGORY_NAMES = ["soul", "user", "agents", "tools"]
MD_FILE_MAP = {
    "soul": "SOUL.md",
    "user": "USER.md",
    "agents": "AGENTS.md",
    "tools": "TOOLS.md",
}

_store_cache: dict[str, "StoreType"] = {}


def get_store(employee_id: str) -> "StoreType":
    """获取该员工的记忆库；若尚未打开则创建并建表。"""
    if employee_id in _store_cache:
        return _store_cache[employee_id]
    db_path = paths.get_employee_memory_db_path(employee_id)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    dsn = f"sqlite:///{db_path.as_posix()}"
    store = SQLiteMemoryStore(dsn=dsn)
    _store_cache[employee_id] = store
    ensure_categories_from_md(employee_id, store)
    return store


def ensure_categories_from_md(employee_id: str, store: "StoreType" | None = None) -> None:
    """若员工目录下存在 SOUL.md / USER.md / AGENTS.md / TOOLS.md，则创建或更新对应 category，summary 为文件内容。"""
    if store is None:
        store = get_store(employee_id)
    emp_dir = paths.get_employee_dir(employee_id)
    for cat_name, filename in MD_FILE_MAP.items():
        md_path = emp_dir / filename
        content = ""
        if md_path.exists():
            try:
                content = md_path.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.warning("Failed to read %s: %s", md_path, e)
        existing = store.memory_category_repo.get_category_by_name(cat_name)
        if existing:
            if content and existing.summary != content:
                store.memory_category_repo.update_category(category_id=existing.id, summary=content)
        else:
            desc = {"soul": "人格/身份", "user": "负责人/用户信息", "agents": "员工指令/行为", "tools": "工具使用"}.get(cat_name, cat_name)
            store.memory_category_repo.get_or_create_category(
                name=cat_name,
                description=desc,
                summary=content or None,
            )


__all__ = ["get_store", "ensure_categories_from_md", "CATEGORY_NAMES", "MD_FILE_MAP"]
