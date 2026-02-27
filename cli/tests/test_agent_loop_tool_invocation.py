"""通过 mock 虚拟大模型返回数据，验证工具是否被正确调用。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from joytrunk.agent.loop import run_employee_loop
from joytrunk.agent.provider import ToolCall


def _fake_tool_call(tool_id: str, name: str, arguments: dict) -> ToolCall:
    return ToolCall(id=tool_id, name=name, arguments=arguments)


def _mock_response(
    content: str = "",
    tool_calls: list[ToolCall] | None = None,
    prompt_tokens: int = 1,
    completion_tokens: int = 1,
) -> MagicMock:
    tc = tool_calls or []
    return MagicMock(
        content=content,
        usage={"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        tool_calls=tc,
        has_tool_calls=len(tc) > 0,
    )


@pytest.mark.asyncio
async def test_mock_llm_read_file_tool_invoked_with_correct_args(config_with_custom_llm, employee_dir):
    """Mock 大模型首次返回 read_file tool_call，第二次返回最终文本；断言 read_file 被以正确参数调用。"""
    (employee_dir / "SOUL.md").write_text("Soul content", encoding="utf-8")
    (employee_dir / "config.json").write_text("{}", encoding="utf-8")

    resp_tool = _mock_response(
        content="",
        tool_calls=[_fake_tool_call("tc-1", "read_file", {"path": "SOUL.md"})],
    )
    resp_final = _mock_response(content="已读取 SOUL.md，内容是 Soul content。", tool_calls=None)

    execute_calls: list[tuple[str, dict]] = []

    async def capture_execute(name: str, params: dict):
        execute_calls.append((name, params))
        if name == "read_file" and params.get("path") == "SOUL.md":
            fp = employee_dir / "SOUL.md"
            return fp.read_text(encoding="utf-8") if fp.exists() else "Error: not found"
        if name == "list_dir":
            return "SOUL.md\nconfig.json"
        return "ok"

    with patch("joytrunk.agent.loop.provider_chat", new_callable=AsyncMock, side_effect=[resp_tool, resp_final]):
        with patch("joytrunk.agent.loop.create_default_registry") as mk_reg:
            from joytrunk.tools import create_default_registry
            from joytrunk import paths

            workspace = paths.get_employee_dir("emp-001")
            real_reg = create_default_registry(workspace, "emp-001", restrict_to_workspace=True)
            real_reg.execute = AsyncMock(side_effect=capture_execute)
            mk_reg.return_value = real_reg

            content, _ = await run_employee_loop(
                "emp-001", "owner-1", "读一下 SOUL.md", session_key="test-mock-read"
            )

    assert len(execute_calls) == 1
    assert execute_calls[0][0] == "read_file"
    assert execute_calls[0][1] == {"path": "SOUL.md"}
    assert "已读取" in content or "Soul" in content


@pytest.mark.asyncio
async def test_mock_llm_list_dir_tool_invoked(config_with_custom_llm, employee_dir):
    """Mock 大模型返回 list_dir tool_call；断言 list_dir 被调用且参数正确。"""
    employee_dir.mkdir(parents=True, exist_ok=True)
    (employee_dir / "SOUL.md").write_text("", encoding="utf-8")
    (employee_dir / "config.json").write_text("{}", encoding="utf-8")

    resp_tool = _mock_response(
        content="",
        tool_calls=[_fake_tool_call("tc-2", "list_dir", {"path": "."})],
    )
    resp_final = _mock_response(content="当前目录有 SOUL.md、config.json。", tool_calls=None)

    execute_calls: list[tuple[str, dict]] = []

    async def capture_execute(name: str, params: dict):
        execute_calls.append((name, params))
        if name == "list_dir":
            p = employee_dir / (params.get("path") or ".")
            if not p.is_absolute():
                p = employee_dir / params.get("path", ".")
            if p.exists() and p.is_dir():
                return "\n".join(f.name for f in sorted(p.iterdir()))
            return "Error: not a directory"
        return "ok"

    with patch("joytrunk.agent.loop.provider_chat", new_callable=AsyncMock, side_effect=[resp_tool, resp_final]):
        with patch("joytrunk.agent.loop.create_default_registry") as mk_reg:
            from joytrunk.tools import create_default_registry
            from joytrunk import paths

            real_reg = create_default_registry(paths.get_employee_dir("emp-001"), "emp-001", restrict_to_workspace=True)
            real_reg.execute = AsyncMock(side_effect=capture_execute)
            mk_reg.return_value = real_reg

            content, _ = await run_employee_loop(
                "emp-001", "owner-1", "列出当前目录", session_key="test-mock-list"
            )

    assert len(execute_calls) == 1
    assert execute_calls[0][0] == "list_dir"
    assert execute_calls[0][1].get("path") == "."
    assert "SOUL" in content or "config" in content or "目录" in content


@pytest.mark.asyncio
async def test_mock_llm_tool_result_passed_to_next_llm_call(config_with_custom_llm, employee_dir):
    """Mock 大模型：第一次返回 read_file，第二次应收到带 tool result 的 messages。"""
    (employee_dir / "SOUL.md").write_text("Secret content", encoding="utf-8")
    (employee_dir / "config.json").write_text("{}", encoding="utf-8")

    resp_tool = _mock_response(
        tool_calls=[_fake_tool_call("tc-3", "read_file", {"path": "SOUL.md"})],
    )
    resp_final = _mock_response(content="收到。")

    captured_messages_on_second_call: list[dict] = []

    async def fake_provider(*args, **kwargs):
        messages = kwargs.get("messages") or (args[3] if len(args) > 3 else [])
        if not hasattr(fake_provider, "_call_count"):
            fake_provider._call_count = 0
        fake_provider._call_count += 1
        if fake_provider._call_count == 1:
            return resp_tool
        captured_messages_on_second_call.extend(messages)
        return resp_final

    with patch("joytrunk.agent.loop.provider_chat", new_callable=AsyncMock, side_effect=fake_provider):
        await run_employee_loop(
            "emp-001", "owner-1", "读 SOUL.md", session_key="test-mock-messages"
        )

    assert len(captured_messages_on_second_call) > 0
    roles = [m.get("role") for m in captured_messages_on_second_call]
    assert "assistant" in roles
    assert "tool" in roles
    tool_msgs = [m for m in captured_messages_on_second_call if m.get("role") == "tool"]
    assert any("Secret content" in (m.get("content") or "") for m in tool_msgs)


@pytest.mark.asyncio
async def test_mock_llm_write_file_tool_invoked(config_with_custom_llm, employee_dir):
    """Mock 大模型返回 write_file tool_call；断言 write_file 被调用且文件被写入。"""
    employee_dir.mkdir(parents=True, exist_ok=True)
    (employee_dir / "config.json").write_text("{}", encoding="utf-8")

    resp_tool = _mock_response(
        tool_calls=[
            _fake_tool_call("tc-4", "write_file", {"path": "note.txt", "content": "Hello from mock LLM"}),
        ],
    )
    resp_final = _mock_response(content="已写入 note.txt。")

    with patch("joytrunk.agent.loop.provider_chat", new_callable=AsyncMock, side_effect=[resp_tool, resp_final]):
        content, _ = await run_employee_loop(
            "emp-001", "owner-1", "请创建 note.txt 并写入 Hello from mock LLM",
            session_key="test-mock-write",
        )

    note_file = employee_dir / "note.txt"
    assert note_file.exists()
    assert "Hello from mock LLM" in note_file.read_text(encoding="utf-8")
    assert "已写入" in content or "note" in content
