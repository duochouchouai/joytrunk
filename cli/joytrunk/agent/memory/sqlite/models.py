"""SQLite 表模型（embedding 存 JSON 文本）。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlmodel import Column, Field, Index, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SQLiteResourceModel(SQLModel, table=True):
    __tablename__ = "resources"
    __table_args__ = ()

    id: str = Field(primary_key=True, sa_type=String(36), default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    updated_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    url: str = Field(sa_column=Column(String, nullable=False))
    modality: str = Field(sa_column=Column(String, nullable=False))
    local_path: str = Field(sa_column=Column(String, nullable=False))
    caption: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    embedding_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


class SQLiteMemoryItemModel(SQLModel, table=True):
    __tablename__ = "memory_items"
    __table_args__ = ()

    id: str = Field(primary_key=True, sa_type=String(36), default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    updated_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    resource_id: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    memory_type: str = Field(sa_column=Column(String, nullable=False))
    summary: str = Field(sa_column=Column(Text, nullable=False))
    embedding_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    happened_at: datetime | None = Field(default=None, sa_column=Column(DateTime, nullable=True))
    extra: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=True))


class SQLiteMemoryCategoryModel(SQLModel, table=True):
    __tablename__ = "memory_categories"
    __table_args__ = (Index("ix_memory_categories_name", "name"),)

    id: str = Field(primary_key=True, sa_type=String(36), default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    updated_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    name: str = Field(sa_column=Column(String, nullable=False))
    description: str = Field(sa_column=Column(Text, nullable=False))
    embedding_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    summary: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


class SQLiteCategoryItemModel(SQLModel, table=True):
    __tablename__ = "category_items"
    __table_args__ = (Index("idx_category_items_unique", "item_id", "category_id", unique=True),)

    id: str = Field(primary_key=True, sa_type=String(36), default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    updated_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    item_id: str = Field(sa_column=Column(String, nullable=False))
    category_id: str = Field(sa_column=Column(String, nullable=False))


__all__ = [
    "SQLiteCategoryItemModel",
    "SQLiteMemoryCategoryModel",
    "SQLiteMemoryItemModel",
    "SQLiteResourceModel",
]

