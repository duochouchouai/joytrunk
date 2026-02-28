"""测试 joytrunk.agent.context。"""

import pytest

from joytrunk.agent.context import (
    RUNTIME_TAG,
    SURVIVAL_RULES,
    ContextBuilder,
)


def test_build_system_prompt_includes_survival_rules(employee_dir):
    (employee_dir / "SOUL.md").write_text("我是助手。", encoding="utf-8")
    (employee_dir / "AGENTS.md").write_text("遵守规则。", encoding="utf-8")
    ctx = ContextBuilder("emp-001")
    prompt = ctx.build_system_prompt()
    assert "员工生存法则" in prompt
    assert SURVIVAL_RULES.strip() in prompt
    assert "我是助手" in prompt
    assert "遵守规则" in prompt


def test_build_system_prompt_includes_memory(employee_dir, workspace_root):
    (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
    mem_dir = workspace_root / "memory"
    mem_dir.mkdir()
    (mem_dir / "MEMORY.md").write_text("团队记忆内容", encoding="utf-8")
    emp_mem = employee_dir / "memory"
    emp_mem.mkdir()
    (emp_mem / "MEMORY.md").write_text("员工记忆", encoding="utf-8")
    ctx = ContextBuilder("emp-001")
    prompt = ctx.build_system_prompt()
    assert "团队共享记忆" in prompt
    assert "团队记忆内容" in prompt
    assert "本员工记忆" in prompt
    assert "员工记忆" in prompt


def test_build_messages_structure(employee_dir):
    (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
    ctx = ContextBuilder("emp-001")
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    messages = ctx.build_messages(history, "帮我截图", channel="cli", chat_id="direct")
    assert len(messages) >= 4
    assert messages[0]["role"] == "system"
    assert "Soul" in messages[0]["content"]
    assert messages[1]["content"] == "hi"
    assert messages[2]["content"] == "hello"
    assert RUNTIME_TAG in messages[3]["content"]
    assert messages[4]["content"] == "帮我截图"


def test_build_messages_empty_message_uses_placeholder(employee_dir):
    (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
    ctx = ContextBuilder("emp-001")
    messages = ctx.build_messages([], "")
    assert any(m.get("content") == "请说你好。" for m in messages if m.get("role") == "user")


def test_add_assistant_message(employee_dir):
    ctx = ContextBuilder("emp-001")
    messages = [{"role": "system", "content": "sys"}]
    ContextBuilder.add_assistant_message(messages, "ok", None)
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == "ok"
    ContextBuilder.add_assistant_message(messages, "call", [{"id": "1", "type": "function", "function": {"name": "exec", "arguments": "{}"}}])
    assert "tool_calls" in messages[-1]


def test_add_tool_result(employee_dir):
    messages = [{"role": "assistant", "content": "..."}]
    ContextBuilder.add_tool_result(messages, "call-1", "read_file", "file content")
    assert messages[-1]["role"] == "tool"
    assert messages[-1]["tool_call_id"] == "call-1"
    assert messages[-1]["name"] == "read_file"
    assert messages[-1]["content"] == "file content"
