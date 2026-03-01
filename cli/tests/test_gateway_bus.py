# -*- coding: utf-8 -*-
"""MessageBus（方案 10.13、10.40）：FIFO、InboundMessage 入队/出队。"""

import asyncio

import pytest

from joytrunk.bus.events import InboundMessage
from joytrunk.bus.queue import MessageBus


@pytest.mark.asyncio
async def test_put_get_fifo():
    bus = MessageBus()
    m1 = InboundMessage(task_id="t1", target_employee_id="e1", owner_id="o1", content="c1", session_key="s1")
    m2 = InboundMessage(task_id="t2", target_employee_id="e2", owner_id="o1", content="c2", session_key="s2")
    await bus.put(m1)
    await bus.put(m2)
    assert await bus.get() == m1
    assert await bus.get() == m2


@pytest.mark.asyncio
async def test_empty_and_qsize():
    bus = MessageBus()
    assert bus.empty()
    assert bus.qsize() == 0
    await bus.put(InboundMessage(task_id="t", target_employee_id="e", owner_id="o", content="", session_key="s"))
    assert not bus.empty()
    assert bus.qsize() == 1
