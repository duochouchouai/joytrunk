"""CategoryItem 仓库。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlmodel import select

from joytrunk.agent.memory.models import CategoryItem
from joytrunk.agent.memory.sqlite.base import SQLiteRepoBase
from joytrunk.agent.memory.sqlite.models import SQLiteCategoryItemModel
from joytrunk.agent.memory.sqlite.session import SQLiteSessionManager
from joytrunk.agent.memory.state import DatabaseState


class SQLiteCategoryItemRepo(SQLiteRepoBase):
    def __init__(
        self,
        *,
        state: DatabaseState,
        sessions: SQLiteSessionManager,
    ) -> None:
        super().__init__(state=state, sessions=sessions)
        self.relations = self._state.relations

    def list_relations(self, where: Mapping[str, Any] | None = None) -> list[CategoryItem]:
        with self._sessions.session() as session:
            stmt = select(SQLiteCategoryItemModel)
            filters = self._build_filters(SQLiteCategoryItemModel, where)
            if filters:
                stmt = stmt.where(*filters)
            rows = session.exec(stmt).all()
        result: list[CategoryItem] = []
        for row in rows:
            rel = CategoryItem(
                id=row.id,
                item_id=row.item_id,
                category_id=row.category_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            result.append(rel)
            if not any(r.id == rel.id for r in self.relations):
                self.relations.append(rel)
        return result

    def link_item_category(self, item_id: str, category_id: str) -> CategoryItem:
        for r in self.relations:
            if r.item_id == item_id and r.category_id == category_id:
                return r
        now = self._now()
        row = SQLiteCategoryItemModel(
            item_id=item_id,
            category_id=category_id,
            created_at=now,
            updated_at=now,
        )
        with self._sessions.session() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
        rel = CategoryItem(
            id=row.id,
            item_id=row.item_id,
            category_id=row.category_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        self.relations.append(rel)
        return rel

    def load_existing(self) -> None:
        self.list_relations()


__all__ = ["SQLiteCategoryItemRepo"]
