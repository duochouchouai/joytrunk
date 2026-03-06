"""SQLite 仓库基类（无 scope，每员工一库）。"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from joytrunk.agent.memory.sqlite.session import SQLiteSessionManager
from joytrunk.agent.memory.state import DatabaseState

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SQLiteRepoBase:
    def __init__(
        self,
        *,
        state: DatabaseState,
        sessions: SQLiteSessionManager,
    ) -> None:
        self._state = state
        self._sessions = sessions

    def _normalize_embedding(self, embedding: Any) -> list[float] | None:
        if embedding is None:
            return None
        if isinstance(embedding, str):
            try:
                return [float(x) for x in json.loads(embedding)]
            except (json.JSONDecodeError, TypeError):
                return None
        try:
            return [float(x) for x in embedding]
        except (ValueError, TypeError):
            return None

    def _prepare_embedding(self, embedding: list[float] | None) -> str | None:
        if embedding is None:
            return None
        return json.dumps(embedding)

    def _now(self) -> datetime:
        return _utc_now()

    def _build_filters(self, model: Any, where: Mapping[str, Any] | None) -> list[Any]:
        if not where:
            return []
        filters: list[Any] = []
        for raw_key, expected in where.items():
            if expected is None:
                continue
            parts = raw_key.split("__", 1)
            field_name = parts[0]
            op = parts[1] if len(parts) > 1 else None
            column = getattr(model, str(field_name), None)
            if column is None:
                raise ValueError(f"Unknown filter field '{field_name}' for model '{model.__name__}'")
            if op == "in":
                filters.append(column.in_(expected) if not isinstance(expected, str) else column == expected)
            else:
                filters.append(column == expected)
        return filters


__all__ = ["SQLiteRepoBase"]
