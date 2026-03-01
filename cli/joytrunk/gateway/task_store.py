"""
In-memory TaskStore (plan 10.5): taskId -> Task.
Worker and boundary layer write/read; Get Task reads from here.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from joytrunk.a2a.models import Message, Part, Task, TaskStatus


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class TaskStore:
    """In-memory store. Must include owner_id on Task (plan 10.5)."""

    def __init__(
        self,
        ttl_seconds: int = 86400,
        cleanup_interval_seconds: int = 60,
    ) -> None:
        self._tasks: dict[str, Task] = {}
        self._events: dict[str, asyncio.Event] = {}  # task_id -> Event for blocking wait
        self._lock = asyncio.Lock()
        self._ttl = ttl_seconds
        self._cleanup_interval = cleanup_interval_seconds
        self._last_cleanup: float = 0

    async def create(self, task_id: str, owner_id: str, context_id: str, user_message: Message) -> Task:
        """Create initial working task (boundary layer)."""
        async with self._lock:
            t = Task(
                id=task_id,
                owner_id=owner_id,
                status="working",
                context_id=context_id,
                history=[user_message],
                metadata={},
                created_at=_iso_now(),
                updated_at=_iso_now(),
            )
            self._tasks[task_id] = t
            self._events[task_id] = asyncio.Event()
            return t

    async def get(self, task_id: str) -> Task | None:
        async with self._lock:
            return self._tasks.get(task_id)

    async def complete(
        self,
        task_id: str,
        status: TaskStatus,
        agent_message: Message,
        usage: dict[str, int] | None = None,
        error: str | None = None,
    ) -> None:
        """Worker calls this after run_employee_loop (plan 10.14)."""
        async with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return
            t.status = status
            t.history = list(t.history) + [agent_message]
            t.metadata = dict(t.metadata)
            if usage is not None:
                t.metadata["usage"] = usage
            if error:
                t.metadata["error"] = error
            t.updated_at = _iso_now()
            if status == "completed" and agent_message.parts:
                text = "".join(p.text or "" for p in agent_message.parts if p.type == "text")
                t.artifacts = [{"type": "text", "text": text}]
            ev = self._events.pop(task_id, None)
        if ev:
            ev.set()

    def get_event(self, task_id: str) -> asyncio.Event | None:
        """Return event for task_id (boundary uses for blocking wait)."""
        return self._events.get(task_id)

    async def wait_done(self, task_id: str, timeout_seconds: float) -> Task | None:
        """Wait until task reaches terminal state or timeout. Returns updated Task or None on timeout."""
        ev = self.get_event(task_id)
        if not ev:
            t = await self.get(task_id)
            return t if t and t.status in ("completed", "failed", "canceled") else None
        try:
            await asyncio.wait_for(ev.wait(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return await self.get(task_id)
        return await self.get(task_id)


_default_store: TaskStore | None = None


def get_default_task_store(ttl_seconds: int = 86400, cleanup_interval_seconds: int = 60) -> TaskStore:
    global _default_store
    if _default_store is None:
        _default_store = TaskStore(ttl_seconds=ttl_seconds, cleanup_interval_seconds=cleanup_interval_seconds)
    return _default_store
