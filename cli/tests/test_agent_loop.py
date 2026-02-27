"""测试 joytrunk.agent.loop。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from joytrunk.agent.loop import run_employee_loop


@pytest.mark.asyncio
async def test_run_employee_loop_returns_final_content(config_with_custom_llm, employee_dir):
    (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
    (employee_dir / "config.json").write_text("{}", encoding="utf-8")

    resp_no_tools = MagicMock(
        content="已帮你完成。",
        usage={"prompt_tokens": 1, "completion_tokens": 1},
        tool_calls=[],
        has_tool_calls=False,
    )
    with patch("joytrunk.agent.loop.provider_chat", new_callable=AsyncMock, return_value=resp_no_tools):
        content, usage = await run_employee_loop("emp-001", "owner-1", "帮我截图", session_key="test-session")
    assert content == "已帮你完成。"
    assert usage["prompt_tokens"] == 1
    assert usage["completion_tokens"] == 1


@pytest.mark.asyncio
async def test_run_employee_loop_executes_tool_then_returns(config_with_custom_llm, employee_dir):
    (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
    (employee_dir / "config.json").write_text("{}", encoding="utf-8")

    class FakeToolCall:
        def __init__(self, id: str, name: str, arguments: dict):
            self.id = id
            self.name = name
            self.arguments = arguments

    resp_with_tool = MagicMock(
        content="",
        usage={"prompt_tokens": 2, "completion_tokens": 2},
        tool_calls=[FakeToolCall("c1", "read_file", {"path": "SOUL.md"})],
        has_tool_calls=True,
    )
    resp_final = MagicMock(
        content="已读取 SOUL.md。",
        usage={"prompt_tokens": 1, "completion_tokens": 1},
        tool_calls=[],
        has_tool_calls=False,
    )
    with patch("joytrunk.agent.loop.provider_chat", new_callable=AsyncMock, side_effect=[resp_with_tool, resp_final]):
        content, usage = await run_employee_loop("emp-001", "owner-1", "读一下 SOUL", session_key="test-session2")
    assert "已读取" in content or "Soul" in content
    assert usage["prompt_tokens"] == 3


@pytest.mark.asyncio
async def test_run_employee_loop_router_source(config_without_custom_llm, employee_dir):
    (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
    resp = MagicMock(
        content="来自 Router 的回复。",
        usage={"prompt_tokens": 1, "completion_tokens": 1},
        tool_calls=[],
        has_tool_calls=False,
    )
    with patch("joytrunk.agent.loop.chat_via_router", new_callable=AsyncMock, return_value=resp):
        content, usage = await run_employee_loop("emp-001", "owner-1", "你好", session_key="test-session3")
    assert "来自 Router" in content
    assert usage is not None
