"""Resource 仓库。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlmodel import delete, select

from joytrunk.agent.memory.models import Resource
from joytrunk.agent.memory.sqlite.base import SQLiteRepoBase
from joytrunk.agent.memory.sqlite.models import SQLiteResourceModel
from joytrunk.agent.memory.sqlite.session import SQLiteSessionManager
from joytrunk.agent.memory.state import DatabaseState


class SQLiteResourceRepo(SQLiteRepoBase):
    def __init__(
        self,
        *,
        state: DatabaseState,
        sessions: SQLiteSessionManager,
    ) -> None:
        super().__init__(state=state, sessions=sessions)
        self.resources = self._state.resources

    def list_resources(self, where: Mapping[str, Any] | None = None) -> dict[str, Resource]:
        if not where and self.resources:
            return dict(self.resources)
        with self._sessions.session() as session:
            stmt = select(SQLiteResourceModel)
            filters = self._build_filters(SQLiteResourceModel, where)
            if filters:
                stmt = stmt.where(*filters)
            rows = session.exec(stmt).all()
        result: dict[str, Resource] = {}
        for row in rows:
            res = Resource(
                id=row.id,
                url=row.url,
                modality=row.modality,
                local_path=row.local_path,
                caption=row.caption,
                embedding=self._normalize_embedding(row.embedding_json),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            result[row.id] = res
            self.resources[row.id] = res
        return result

    def create_resource(
        self,
        *,
        url: str,
        modality: str,
        local_path: str,
        caption: str | None,
        embedding: list[float] | None,
    ) -> Resource:
        now = self._now()
        row = SQLiteResourceModel(
            url=url,
            modality=modality,
            local_path=local_path,
            caption=caption,
            embedding_json=self._prepare_embedding(embedding),
            created_at=now,
            updated_at=now,
        )
        with self._sessions.session() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
        res = Resource(
            id=row.id,
            url=row.url,
            modality=row.modality,
            local_path=row.local_path,
            caption=row.caption,
            embedding=embedding,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        self.resources[row.id] = res
        return res

    def load_existing(self) -> None:
        self.list_resources()


__all__ = ["SQLiteResourceRepo"]
