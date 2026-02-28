"""MemoryCategory 仓库。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlmodel import select

from joytrunk.agent.memory.models import MemoryCategory
from joytrunk.agent.memory.sqlite.base import SQLiteRepoBase
from joytrunk.agent.memory.sqlite.models import SQLiteMemoryCategoryModel
from joytrunk.agent.memory.sqlite.session import SQLiteSessionManager
from joytrunk.agent.memory.state import DatabaseState


class SQLiteMemoryCategoryRepo(SQLiteRepoBase):
    def __init__(
        self,
        *,
        state: DatabaseState,
        sessions: SQLiteSessionManager,
    ) -> None:
        super().__init__(state=state, sessions=sessions)
        self.categories = self._state.categories

    def list_categories(self, where: Mapping[str, Any] | None = None) -> dict[str, MemoryCategory]:
        with self._sessions.session() as session:
            stmt = select(SQLiteMemoryCategoryModel)
            filters = self._build_filters(SQLiteMemoryCategoryModel, where)
            if filters:
                stmt = stmt.where(*filters)
            rows = session.exec(stmt).all()
        result: dict[str, MemoryCategory] = {}
        for row in rows:
            cat = MemoryCategory(
                id=row.id,
                name=row.name,
                description=row.description,
                embedding=self._normalize_embedding(row.embedding_json),
                summary=row.summary,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            result[row.id] = cat
            self.categories[row.id] = cat
        return result

    def get_category_by_name(self, name: str) -> MemoryCategory | None:
        with self._sessions.session() as session:
            stmt = select(SQLiteMemoryCategoryModel).where(SQLiteMemoryCategoryModel.name == name)
            row = session.exec(stmt).first()
        if row is None:
            return None
        cat = MemoryCategory(
            id=row.id,
            name=row.name,
            description=row.description,
            embedding=self._normalize_embedding(row.embedding_json),
            summary=row.summary,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        self.categories[row.id] = cat
        return cat

    def get_or_create_category(
        self,
        *,
        name: str,
        description: str,
        summary: str | None = None,
        embedding: list[float] | None = None,
    ) -> MemoryCategory:
        existing = self.get_category_by_name(name)
        if existing:
            return existing
        now = self._now()
        row = SQLiteMemoryCategoryModel(
            name=name,
            description=description,
            summary=summary,
            embedding_json=self._prepare_embedding(embedding),
            created_at=now,
            updated_at=now,
        )
        with self._sessions.session() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
        cat = MemoryCategory(
            id=row.id,
            name=row.name,
            description=row.description,
            embedding=embedding,
            summary=row.summary,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        self.categories[row.id] = cat
        return cat

    def update_category(
        self,
        *,
        category_id: str,
        name: str | None = None,
        description: str | None = None,
        embedding: list[float] | None = None,
        summary: str | None = None,
    ) -> MemoryCategory:
        with self._sessions.session() as session:
            stmt = select(SQLiteMemoryCategoryModel).where(SQLiteMemoryCategoryModel.id == category_id)
            row = session.exec(stmt).first()
            if row is None:
                raise KeyError(f"Category {category_id} not found")
            if name is not None:
                row.name = name
            if description is not None:
                row.description = description
            if embedding is not None:
                row.embedding_json = self._prepare_embedding(embedding)
            if summary is not None:
                row.summary = summary
            row.updated_at = self._now()
            session.add(row)
            session.commit()
            session.refresh(row)
        cat = MemoryCategory(
            id=row.id,
            name=row.name,
            description=row.description,
            embedding=self._normalize_embedding(row.embedding_json),
            summary=row.summary,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        self.categories[row.id] = cat
        return cat

    def load_existing(self) -> None:
        self.list_categories()


__all__ = ["SQLiteMemoryCategoryRepo"]
