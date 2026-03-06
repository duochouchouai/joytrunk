"""记忆数据模型（移植自 memU，无 pendulum 依赖）。"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

MemoryType = Literal["profile", "event", "knowledge", "behavior", "skill", "tool"]


def compute_content_hash(summary: str, memory_type: str) -> str:
    """生成用于记忆去重的唯一哈希。"""
    normalized = " ".join(summary.lower().split())
    content = f"{memory_type}:{normalized}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseRecord(BaseModel):
    """与后端无关的记录接口。"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class Resource(BaseRecord):
    url: str
    modality: str
    local_path: str
    caption: str | None = None
    embedding: list[float] | None = None


class MemoryItem(BaseRecord):
    resource_id: str | None = None
    memory_type: str
    summary: str
    embedding: list[float] | None = None
    happened_at: datetime | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class MemoryCategory(BaseRecord):
    name: str
    description: str
    embedding: list[float] | None = None
    summary: str | None = None


class CategoryItem(BaseRecord):
    item_id: str
    category_id: str


__all__ = [
    "BaseRecord",
    "CategoryItem",
    "MemoryCategory",
    "MemoryItem",
    "MemoryType",
    "Resource",
    "compute_content_hash",
]
