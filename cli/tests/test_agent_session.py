"""测试 joytrunk.agent.session。"""

import json

import pytest

from joytrunk.agent.session import append_turn, load_history, save_history


def test_load_history_empty(employee_dir):
    assert load_history("emp-001", "cli:direct") == []


def test_save_and_load_history(employee_dir):
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    save_history("emp-001", "cli_direct", messages)
    loaded = load_history("emp-001", "cli_direct")
    assert len(loaded) == 2
    assert loaded[0]["content"] == "hi"
    assert loaded[1]["content"] == "hello"
    session_file = employee_dir / "sessions" / "cli_direct.json"
    assert session_file.exists()
    data = json.loads(session_file.read_text(encoding="utf-8"))
    assert "messages" in data
    assert "updated_at" in data


def test_save_history_truncates_tool_content(employee_dir):
    long_content = "x" * 600
    messages = [{"role": "tool", "tool_call_id": "1", "name": "read_file", "content": long_content}]
    save_history("emp-001", "s1", messages)
    loaded = load_history("emp-001", "s1")
    assert "... (truncated)" in loaded[0]["content"]
    assert len(loaded[0]["content"]) < 600


def test_append_turn(employee_dir):
    save_history("emp-001", "s2", [{"role": "user", "content": "first"}])
    new_messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "runtime"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "reply"},
    ]
    append_turn("emp-001", "s2", new_messages, skip_count=2)
    loaded = load_history("emp-001", "s2")
    assert len(loaded) == 3
    assert loaded[0]["content"] == "first"
    assert loaded[1]["content"] == "second"
    assert loaded[2]["content"] == "reply"
