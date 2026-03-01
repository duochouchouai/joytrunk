"""
MessageBus: in-memory asyncio queue for Gateway (plan §7).
Boundary layer enqueues InboundMessage; Worker dequeues and runs run_employee_loop.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from joytrunk.bus.events import InboundMessage


class MessageBus:
    """FIFO queue of InboundMessage. Single process; optional Redis later."""

    def __init__(self) -> None:
        self._q: asyncio.Queue[InboundMessage] = asyncio.Queue()

    async def put(self, msg: InboundMessage) -> None:
        await self._q.put(msg)

    async def get(self) -> InboundMessage:
        return await self._q.get()

    def put_nowait(self, msg: InboundMessage) -> None:
        self._q.put_nowait(msg)

    def get_nowait(self) -> InboundMessage:
        return self._q.get_nowait()

    def empty(self) -> bool:
        return self._q.empty()

    def qsize(self) -> int:
        return self._q.qsize()


# Singleton for gateway process (optional; can be passed by a2a_server)
_default_bus: MessageBus | None = None


def get_default_bus() -> MessageBus:
    global _default_bus
    if _default_bus is None:
        _default_bus = MessageBus()
    return _default_bus
