# -*- coding: utf-8 -*-
"""TaskStore（方案 10.5、10.4）：create/get/complete/wait_done、owner_id、blocking 通知。"""

import asyncio

import pytest

from joytrunk.a2a.models import Message, Part, Task
from joytrunk.gateway.task_store import TaskStore


@pytest.fixture
def store():
    return TaskStore(ttl_seconds=86400, cleanup_interval_seconds=60)


@pytest.mark.asyncio
async def test_create_and_get(store):
    user_msg = Message(role="user", parts=[Part(type="text", text="hi")])
    task = await store.create("task-1", "owner-1", "ctx-1", user_msg)
    assert task.id == "task-1"
    assert task.owner_id == "owner-1"
    assert task.status == "working"
    assert task.context_id == "ctx-1"
    assert len(task.history) == 1
    got = await store.get("task-1")
    assert got is not None
    assert got.owner_id == "owner-1"


@pytest.mark.asyncio
async def test_get_missing_returns_none(store):
    assert await store.get("nonexistent") is None


@pytest.mark.asyncio
async def test_complete_sets_status_and_notifies(store):
    user_msg = Message(role="user", parts=[Part(type="text", text="q")])
    await store.create("t1", "o1", "c1", user_msg)
    agent_msg = Message(role="agent", parts=[Part(type="text", text="a")])
    await store.complete("t1", "completed", agent_msg, usage={"prompt_tokens": 1, "completion_tokens": 2})
    t = await store.get("t1")
    assert t.status == "completed"
    assert len(t.history) == 2
    assert t.metadata.get("usage") == {"prompt_tokens": 1, "completion_tokens": 2}
    assert t.artifacts == [{"type": "text", "text": "a"}]


@pytest.mark.asyncio
async def test_wait_done_blocks_until_complete(store):
    user_msg = Message(role="user", parts=[Part(type="text", text="q")])
    await store.create("t2", "o1", "c1", user_msg)

    async def complete_later():
        await asyncio.sleep(0.05)
        await store.complete(
            "t2",
            "completed",
            Message(role="agent", parts=[Part(type="text", text="done")]),
        )

    asyncio.create_task(complete_later())
    result = await store.wait_done("t2", timeout_seconds=2.0)
    assert result is not None
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_wait_done_timeout_returns_task(store):
    user_msg = Message(role="user", parts=[Part(type="text", text="q")])
    await store.create("t3", "o1", "c1", user_msg)
    result = await store.wait_done("t3", timeout_seconds=0.05)
    assert result is not None
    assert result.status == "working"
