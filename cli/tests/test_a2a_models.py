# -*- coding: utf-8 -*-
"""A2A 模型与转换（方案 10.1、10.17、10.18）：Part/Message/Task、part_to_text、序列化。"""

import pytest

from joytrunk.a2a.models import (
    Message,
    Part,
    SendMessageConfiguration,
    SendMessageRequest,
    Task,
    agent_card_to_dict,
    message_to_dict,
    part_to_text,
    task_to_dict,
)


# --- part_to_text (10.1) ---
def test_part_to_text_empty():
    assert part_to_text([]) == ""


def test_part_to_text_single():
    assert part_to_text([Part(type="text", text="hello")]) == "hello"


def test_part_to_text_concatenates():
    assert part_to_text([
        Part(type="text", text="a"),
        Part(type="text", text="b"),
    ]) == "ab"


def test_part_to_text_skips_non_text():
    assert part_to_text([
        Part(type="text", text="x"),
        Part(type="file", text=None),
        Part(type="text", text="y"),
    ]) == "xy"


def test_part_to_text_none_text_becomes_empty():
    assert part_to_text([Part(type="text", text=None)]) == ""


# --- Message / message_to_dict ---
def test_message_to_dict():
    m = Message(role="user", parts=[Part(type="text", text="hi")], context_id="ctx-1")
    d = message_to_dict(m)
    assert d["role"] == "user"
    assert d["parts"] == [{"type": "text", "text": "hi"}]
    assert d["contextId"] == "ctx-1"


def test_message_to_dict_omits_optional():
    m = Message(role="agent", parts=[])
    d = message_to_dict(m)
    assert "contextId" not in d or d.get("contextId") is None


# --- Task / task_to_dict (10.18, 10.32: metadata.usage) ---
def test_task_to_dict():
    user_msg = Message(role="user", parts=[Part(type="text", text="q")])
    agent_msg = Message(role="agent", parts=[Part(type="text", text="a")])
    t = Task(
        id="tid",
        owner_id="owner1",
        status="completed",
        context_id="ctx1",
        history=[user_msg, agent_msg],
        artifacts=[{"type": "text", "text": "a"}],
        metadata={"usage": {"prompt_tokens": 10, "completion_tokens": 20}},
        created_at="2025-01-01T00:00:00.000Z",
        updated_at="2025-01-01T00:00:01.000Z",
    )
    d = task_to_dict(t)
    assert d["id"] == "tid"
    assert d["status"] == "completed"
    assert d["contextId"] == "ctx1"
    assert len(d["history"]) == 2
    assert d["history"][0]["role"] == "user"
    assert d["history"][1]["role"] == "agent"
    assert d["metadata"]["usage"] == {"prompt_tokens": 10, "completion_tokens": 20}
    assert d["artifacts"] == [{"type": "text", "text": "a"}]


# --- SendMessageRequest / configuration ---
def test_send_message_request_blocking():
    msg = Message(role="user", parts=[Part(type="text", text="x")])
    cfg = SendMessageConfiguration(blocking=True, history_length=10)
    req = SendMessageRequest(message=msg, configuration=cfg, metadata={"channel": "cli"})
    assert req.configuration.blocking is True
    assert req.configuration.history_length == 10
    assert req.metadata["channel"] == "cli"


# --- AgentCard ---
def test_agent_card_to_dict():
    from joytrunk.a2a.models import AgentCard, AgentCardCapabilities
    c = AgentCard(
        name="Test",
        description="Desc",
        capabilities=AgentCardCapabilities(streaming=False, push_notifications=True),
        url="http://localhost/agent",
    )
    d = agent_card_to_dict(c)
    assert d["name"] == "Test"
    assert d["capabilities"]["pushNotifications"] is True
    assert d["capabilities"]["streaming"] is False
