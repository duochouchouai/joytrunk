"""SQLite 会话管理。"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, create_engine

logger = logging.getLogger(__name__)


class SQLiteSessionManager:
    """SQLite 连接与会话。"""

    def __init__(self, *, dsn: str, engine_kwargs: dict[str, Any] | None = None) -> None:
        kw: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
        if engine_kwargs:
            kw.update(engine_kwargs)
        self._engine = create_engine(dsn, **kw)

    def session(self) -> Session:
        return Session(self._engine, expire_on_commit=False)

    def close(self) -> None:
        try:
            self._engine.dispose()
        except SQLAlchemyError:
            logger.exception("Failed to close SQLite engine")

    @property
    def engine(self) -> Any:
        return self._engine


__all__ = ["SQLiteSessionManager"]
