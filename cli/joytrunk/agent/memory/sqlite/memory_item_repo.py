"""MemoryItem 仓库（含 vector_search_items）。"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlmodel import delete, select

from joytrunk.agent.memory.models import MemoryItem, compute_content_hash
from joytrunk.agent.memory.sqlite.base import SQLiteRepoBase
from joytrunk.agent.memory.sqlite.models import SQLiteMemoryItemModel
from joytrunk.agent.memory.sqlite.session import SQLiteSessionManager
from joytrunk.agent.memory.state import DatabaseState
from joytrunk.agent.memory.vector import cosine_topk, cosine_topk_salience


def _parse_datetime(dt_str: str | None) -> datetime | None:
    if dt_str is None:
        return None
    try:
        from datetime import datetime as dt
        return dt.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


class SQLiteMemoryItemRepo(SQLiteRepoBase):
    def __init__(
        self,
        *,
        state: DatabaseState,
        sessions: SQLiteSessionManager,
    ) -> None:
        super().__init__(state=state, sessions=sessions)
        self.items = self._state.items

    def get_item(self, item_id: str) -> MemoryItem | None:
        if item_id in self.items:
            return self.items[item_id]
        with self._sessions.session() as session:
            stmt = select(SQLiteMemoryItemModel).where(SQLiteMemoryItemModel.id == item_id)
            row = session.exec(stmt).first()
        if row is None:
            return None
        item = MemoryItem(
            id=row.id,
            resource_id=row.resource_id,
            memory_type=row.memory_type,
            summary=row.summary,
            embedding=self._normalize_embedding(row.embedding_json),
            created_at=row.created_at,
            updated_at=row.updated_at,
            happened_at=row.happened_at,
            extra=row.extra or {},
        )
        self.items[row.id] = item
        return item

    def list_items(self, where: Mapping[str, Any] | None = None) -> dict[str, MemoryItem]:
        with self._sessions.session() as session:
            stmt = select(SQLiteMemoryItemModel)
            filters = self._build_filters(SQLiteMemoryItemModel, where)
            if filters:
                stmt = stmt.where(*filters)
            rows = session.exec(stmt).all()
        result: dict[str, MemoryItem] = {}
        for row in rows:
            item = MemoryItem(
                id=row.id,
                resource_id=row.resource_id,
                memory_type=row.memory_type,
                summary=row.summary,
                embedding=self._normalize_embedding(row.embedding_json),
                created_at=row.created_at,
                updated_at=row.updated_at,
                happened_at=row.happened_at,
                extra=row.extra or {},
            )
            result[row.id] = item
            self.items[row.id] = item
        return result

    def create_item(
        self,
        *,
        resource_id: str,
        memory_type: str,
        summary: str,
        embedding: list[float],
        reinforce: bool = False,
    ) -> MemoryItem:
        if reinforce:
            return self._create_item_reinforce(
                resource_id=resource_id,
                memory_type=memory_type,
                summary=summary,
                embedding=embedding,
            )
        now = self._now()
        content_hash = compute_content_hash(summary, memory_type)
        extra: dict[str, Any] = {
            "content_hash": content_hash,
            "reinforcement_count": 1,
            "last_reinforced_at": now.isoformat(),
        }
        row = SQLiteMemoryItemModel(
            resource_id=resource_id,
            memory_type=memory_type,
            summary=summary,
            embedding_json=self._prepare_embedding(embedding),
            extra=extra,
            created_at=now,
            updated_at=now,
        )
        with self._sessions.session() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
        item = MemoryItem(
            id=row.id,
            resource_id=row.resource_id,
            memory_type=row.memory_type,
            summary=row.summary,
            embedding=embedding,
            created_at=row.created_at,
            updated_at=row.updated_at,
            extra=row.extra or {},
        )
        self.items[row.id] = item
        return item

    def _create_item_reinforce(
        self,
        *,
        resource_id: str,
        memory_type: str,
        summary: str,
        embedding: list[float],
    ) -> MemoryItem:
        content_hash = compute_content_hash(summary, memory_type)
        pool = self.list_items()
        for i in pool.values():
            if (i.extra or {}).get("content_hash") == content_hash:
                with self._sessions.session() as session:
                    stmt = select(SQLiteMemoryItemModel).where(SQLiteMemoryItemModel.id == i.id)
                    row = session.exec(stmt).first()
                    if row:
                        current_extra = row.extra or {}
                        count = current_extra.get("reinforcement_count", 1)
                        current_extra["reinforcement_count"] = count + 1
                        current_extra["last_reinforced_at"] = self._now().isoformat()
                        row.extra = current_extra
                        row.updated_at = self._now()
                        session.add(row)
                        session.commit()
                        session.refresh(row)
                    item = MemoryItem(
                        id=row.id,
                        resource_id=row.resource_id,
                        memory_type=row.memory_type,
                        summary=row.summary,
                        embedding=self._normalize_embedding(row.embedding_json),
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        extra=row.extra or {},
                    )
                    self.items[row.id] = item
                    return item
        now = self._now()
        row = SQLiteMemoryItemModel(
            resource_id=resource_id,
            memory_type=memory_type,
            summary=summary,
            embedding_json=self._prepare_embedding(embedding),
            extra={
                "content_hash": content_hash,
                "reinforcement_count": 1,
                "last_reinforced_at": now.isoformat(),
            },
            created_at=now,
            updated_at=now,
        )
        with self._sessions.session() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
        item = MemoryItem(
            id=row.id,
            resource_id=row.resource_id,
            memory_type=row.memory_type,
            summary=row.summary,
            embedding=embedding,
            created_at=row.created_at,
            updated_at=row.updated_at,
            extra=row.extra or {},
        )
        self.items[row.id] = item
        return item

    def vector_search_items(
        self,
        query_vec: list[float],
        top_k: int,
        where: Mapping[str, Any] | None = None,
        *,
        ranking: str = "similarity",
        recency_decay_days: float = 30.0,
    ) -> list[tuple[str, float]]:
        pool = self.list_items(where)
        if ranking == "salience":
            corpus = [
                (
                    i.id,
                    i.embedding,
                    (i.extra or {}).get("reinforcement_count", 1),
                    _parse_datetime((i.extra or {}).get("last_reinforced_at")),
                )
                for i in pool.values()
            ]
            return cosine_topk_salience(
                query_vec, corpus, k=top_k, recency_decay_days=recency_decay_days
            )
        return cosine_topk(query_vec, [(i.id, i.embedding) for i in pool.values()], k=top_k)

    def load_existing(self) -> None:
        self.list_items()


__all__ = ["SQLiteMemoryItemRepo"]
