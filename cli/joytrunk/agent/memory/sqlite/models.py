"""SQLite 表模型（embedding 存 JSON 文本）。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Integer, JSON, DateTime, String, Text
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


class SQLiteChatMessageModel(SQLModel, table=True):
    """员工与负责人/其他智能体的单条聊天消息（每员工一库，同 memory.db）。"""
    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_session_created", "session_key", "created_at"),)

    id: str = Field(primary_key=True, sa_type=String(36), default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=_utc_now, sa_type=DateTime)
    session_key: str = Field(sa_column=Column(String, nullable=False))  # owner | agent:<employee_id>
    role: str = Field(sa_column=Column(String, nullable=False))  # user | assistant | system | tool
    content: str | None = Field(default=None, sa_column=Column(Text, nullable=True))  # 纯文本或占位
    extra_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))  # tool_calls, name, tool_call_id, 或 content 列表
    seq: int = Field(default=0, sa_column=Column(Integer, nullable=False))  # 同 session 内顺序，保证 assistant/tool 配对


__all__ = [
    "SQLiteCategoryItemModel",
    "SQLiteMemoryCategoryModel",
    "SQLiteMemoryItemModel",
    "SQLiteResourceModel",
    "SQLiteChatMessageModel",
]

