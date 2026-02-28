"""SQLite 记忆库（每员工一库，无 scope）。"""

from __future__ import annotations

import logging

from sqlmodel import SQLModel

from joytrunk.agent.memory.sqlite.session import SQLiteSessionManager
from joytrunk.agent.memory.sqlite.models import (
    SQLiteCategoryItemModel,
    SQLiteMemoryCategoryModel,
    SQLiteMemoryItemModel,
    SQLiteResourceModel,
)
from joytrunk.agent.memory.sqlite.resource_repo import SQLiteResourceRepo
from joytrunk.agent.memory.sqlite.memory_category_repo import SQLiteMemoryCategoryRepo
from joytrunk.agent.memory.sqlite.memory_item_repo import SQLiteMemoryItemRepo
from joytrunk.agent.memory.sqlite.category_item_repo import SQLiteCategoryItemRepo
from joytrunk.agent.memory.state import DatabaseState

logger = logging.getLogger(__name__)


class SQLiteMemoryStore:
    """每员工一个 SQLite 文件，提供 resource/category/item/category_item 仓库。"""

    def __init__(self, *, dsn: str) -> None:
        self.dsn = dsn
        self._state = DatabaseState()
        self._sessions = SQLiteSessionManager(dsn=dsn)
        self._create_tables()
        self.resource_repo = SQLiteResourceRepo(state=self._state, sessions=self._sessions)
        self.memory_category_repo = SQLiteMemoryCategoryRepo(state=self._state, sessions=self._sessions)
        self.memory_item_repo = SQLiteMemoryItemRepo(state=self._state, sessions=self._sessions)
        self.category_item_repo = SQLiteCategoryItemRepo(state=self._state, sessions=self._sessions)
        self.resources = self._state.resources
        self.items = self._state.items
        self.categories = self._state.categories
        self.relations = self._state.relations

    def _create_tables(self) -> None:
        SQLModel.metadata.create_all(self._sessions.engine)

    def close(self) -> None:
        self._sessions.close()

    def load_existing(self) -> None:
        self.resource_repo.load_existing()
        self.memory_category_repo.load_existing()
        self.memory_item_repo.load_existing()
        self.category_item_repo.load_existing()


__all__ = ["SQLiteMemoryStore"]
