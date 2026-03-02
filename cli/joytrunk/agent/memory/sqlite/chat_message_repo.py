"""聊天记录仓库：按 session_key 追加与查询（每员工一库，与 memory 同库）。"""

from __future__ import annotations

import json
from typing import Any

from sqlmodel import select

from joytrunk.agent.memory.sqlite.models import SQLiteChatMessageModel
from joytrunk.agent.memory.sqlite.session import SQLiteSessionManager


def _message_to_row(session_key: str, msg: dict[str, Any]) -> dict[str, Any]:
    """将一条 message 转为 ORM 行字段。"""
    role = msg.get("role") or "user"
    content = msg.get("content")
    extra: dict[str, Any] = {}
    if isinstance(content, list):
        extra["content"] = content
        content_str = None
    elif content is not None:
        content_str = str(content) if not isinstance(content, str) else content
    else:
        content_str = None
    for k in ("name", "tool_call_id", "tool_calls"):
        if k in msg and msg[k] is not None:
            extra[k] = msg[k]
    return {
        "session_key": session_key,
        "role": role,
        "content": content_str,
        "extra_json": json.dumps(extra, ensure_ascii=False) if extra else None,
    }


def _row_to_message(row: SQLiteChatMessageModel) -> dict[str, Any]:
    """将一行转为 message dict。"""
    out: dict[str, Any] = {"role": row.role}
    if row.extra_json:
        try:
            extra = json.loads(row.extra_json)
            if isinstance(extra.get("content"), list):
                out["content"] = extra["content"]
            else:
                out["content"] = row.content or ""
            for k in ("name", "tool_call_id", "tool_calls"):
                if k in extra:
                    out[k] = extra[k]
        except (json.JSONDecodeError, TypeError):
            out["content"] = row.content or ""
    else:
        out["content"] = row.content or ""
    if getattr(row, "created_at", None) is not None:
        out["timestamp"] = row.created_at.isoformat()
    return out


class SQLiteChatMessageRepo:
    """同一 SQLite（员工 memory.db）内的聊天记录表。"""

    def __init__(self, *, sessions: SQLiteSessionManager) -> None:
        self._sessions = sessions

    def add_messages(self, session_key: str, messages: list[dict[str, Any]]) -> None:
        """追加多条消息（按顺序插入）。"""
        if not messages:
            return
        with self._sessions.session() as session:
            for msg in messages:
                row = SQLiteChatMessageModel(**_message_to_row(session_key, msg))
                session.add(row)
            session.commit()

    def get_messages(self, session_key: str, limit: int = 500) -> list[dict[str, Any]]:
        """按时间正序返回该 session 的最近 limit 条消息。"""
        with self._sessions.session() as session:
            stmt = (
                select(SQLiteChatMessageModel)
                .where(SQLiteChatMessageModel.session_key == session_key)
                .order_by(SQLiteChatMessageModel.created_at.asc())
            )
            rows = session.exec(stmt).all()
            out = [_row_to_message(r) for r in rows]
            if len(out) > limit:
                out = out[-limit:]
            return out

    def replace_messages(self, session_key: str, messages: list[dict[str, Any]]) -> None:
        """先删该 session 全部再插入（用于整段历史覆盖）。"""
        with self._sessions.session() as session:
            from sqlmodel import delete
            session.exec(delete(SQLiteChatMessageModel).where(SQLiteChatMessageModel.session_key == session_key))
            session.commit()
        self.add_messages(session_key, messages)

    def clear_session(self, session_key: str) -> None:
        """清空该 session 的所有消息。"""
        with self._sessions.session() as session:
            from sqlmodel import delete
            session.exec(delete(SQLiteChatMessageModel).where(SQLiteChatMessageModel.session_key == session_key))
            session.commit()

    def list_all_for_export(self, limit: int = 5000) -> list[dict[str, Any]]:
        """导出全部聊天消息（按时间正序），供前端/脚本展示。返回可序列化 dict 列表。"""
        with self._sessions.session() as session:
            stmt = (
                select(SQLiteChatMessageModel)
                .order_by(SQLiteChatMessageModel.created_at.asc())
            )
            rows = session.exec(stmt).all()
            out: list[dict[str, Any]] = []
            for r in rows[:limit]:
                obj: dict[str, Any] = {
                    "id": r.id,
                    "created_at": r.created_at.isoformat() if getattr(r.created_at, "isoformat", None) else str(r.created_at),
                    "session_key": r.session_key,
                    "role": r.role,
                    "content": r.content,
                }
                if r.extra_json:
                    try:
                        obj["extra"] = json.loads(r.extra_json)
                    except (json.JSONDecodeError, TypeError):
                        obj["extra"] = None
                out.append(obj)
            return out


__all__ = ["SQLiteChatMessageRepo", "_message_to_row", "_row_to_message"]
