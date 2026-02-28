"""记忆库入口：按员工返回 SQLite store，14 类 category 仅存 DB，种子从 defaults 读。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from joytrunk import paths
from joytrunk.agent.memory.sqlite.store import SQLiteMemoryStore

if TYPE_CHECKING:
    from joytrunk.agent.memory.sqlite.store import SQLiteMemoryStore as StoreType

logger = logging.getLogger(__name__)

# 14 个 category：前 4 个与 system prompt 注入一致，后 10 个为 memU 扩展
CATEGORY_NAMES = [
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

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "soul": "人格/身份",
    "user": "负责人/用户信息",
    "agents": "员工指令/行为",
    "tools": "工具使用",
    "personal_info": "用户个人信息",
    "preferences": "偏好与好恶",
    "relationships": "人际关系",
    "activities": "活动与行为",
    "goals": "目标与计划",
    "experiences": "经历与事件",
    "knowledge": "知识与技能",
    "opinions": "观点与态度",
    "habits": "习惯与惯例",
    "work_life": "工作与生活",
}

# 前 4 个 category 的默认种子文件名（包内 templates/defaults/ 下）
DEFAULT_SEED_FILES = {"soul": "soul.md", "user": "user.md", "agents": "agents.md", "tools": "tools.md"}

# 旧员工迁移：若 DB 中 summary 为空且员工目录下仍有该 .md，则读入一次
LEGACY_MD_MAP = {
    "soul": "SOUL.md",
    "user": "USER.md",
    "agents": "AGENTS.md",
    "tools": "TOOLS.md",
}

_store_cache: dict[str, "StoreType"] = {}


def get_bundled_defaults_path(filename: str) -> Path:
    """包内 defaults 目录下某文件的路径。"""
    return paths.get_bundled_defaults_dir() / filename


def ensure_all_categories(employee_id: str, store: "StoreType") -> None:
    """
    确保 14 个 category 存在；若不存在则创建，summary 先为空。
    对 soul/user/agents/tools：新建时优先从员工目录旧 .md 读入（迁移），否则从包内 defaults 种子读入。
    兼容旧员工：若 category 已存在且 summary 为空且员工目录有对应 .md，则读入一次（迁移）。
    """
    emp_dir = paths.get_employee_dir(employee_id)
    for name in CATEGORY_NAMES:
        desc = CATEGORY_DESCRIPTIONS.get(name, name)
        existing = store.memory_category_repo.get_category_by_name(name)
        if existing:
            # 迁移：summary 为空且员工目录下有旧 .md 则读入
            if not (existing.summary or "").strip() and name in LEGACY_MD_MAP:
                legacy_path = emp_dir / LEGACY_MD_MAP[name]
                if legacy_path.exists():
                    try:
                        content = legacy_path.read_text(encoding="utf-8").strip()
                        if content:
                            store.memory_category_repo.update_category(
                                category_id=existing.id, summary=content
                            )
                            logger.info("Migrated %s from %s", name, legacy_path)
                    except Exception as e:
                        logger.warning("Failed to migrate %s from %s: %s", name, legacy_path, e)
            continue
        # 新建：对前 4 个优先用员工目录旧 .md，否则用包内 defaults 种子
        initial_summary: str | None = None
        if name in LEGACY_MD_MAP:
            legacy_path = emp_dir / LEGACY_MD_MAP[name]
            if legacy_path.exists():
                try:
                    initial_summary = legacy_path.read_text(encoding="utf-8").strip() or None
                except Exception as e:
                    logger.warning("Failed to read legacy %s: %s", legacy_path, e)
        if initial_summary is None and name in DEFAULT_SEED_FILES:
            seed_path = get_bundled_defaults_path(DEFAULT_SEED_FILES[name])
            if seed_path.exists():
                try:
                    initial_summary = seed_path.read_text(encoding="utf-8").strip() or None
                except Exception as e:
                    logger.warning("Failed to seed %s from %s: %s", name, seed_path, e)
        cat = store.memory_category_repo.get_or_create_category(
            name=name,
            description=desc,
            summary=initial_summary,
        )


def get_store(employee_id: str) -> "StoreType":
    """获取该员工的记忆库；若尚未打开则创建并建表。并确保 14 个 category 存在（含种子/迁移）。"""
    if employee_id in _store_cache:
        return _store_cache[employee_id]
    db_path = paths.get_employee_memory_db_path(employee_id)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    dsn = f"sqlite:///{db_path.as_posix()}"
    store = SQLiteMemoryStore(dsn=dsn)
    _store_cache[employee_id] = store
    ensure_all_categories(employee_id, store)
    return store


__all__ = ["get_store", "ensure_all_categories", "CATEGORY_NAMES", "CATEGORY_DESCRIPTIONS"]
