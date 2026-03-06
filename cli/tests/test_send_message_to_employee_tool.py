# -*- coding: utf-8 -*-
"""send_message_to_employee 工具（阶段 3）：同 owner 校验、A2A 与直连回退。"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# 避免 tools 包加载时触发 memory_tools -> sqlmodel 等依赖；无 sqlmodel 时跳过
try:
    from joytrunk.tools.send_message_to_employee import SendMessageToEmployeeTool
except Exception:
    SendMessageToEmployeeTool = None


@pytest.fixture
def tool(workspace_root):
    if SendMessageToEmployeeTool is None:
        pytest.skip("SendMessageToEmployeeTool not importable (e.g. missing sqlmodel)")
    allowed = workspace_root
    return SendMessageToEmployeeTool(allowed, allowed, from_employee_id="emp-A", owner_id="owner-1")


@pytest.mark.asyncio
async def test_execute_target_not_in_owner_returns_error(tool):
    with patch("joytrunk.config_store.list_employees_from_config", return_value=[{"id": "emp-B"}]):
        out = await tool.execute(target_employee_id="emp-C", content="hi")
    assert "错误" in out
    assert "不存在" in out or "不属于" in out


@pytest.mark.asyncio
async def test_execute_self_message_returns_error(tool):
    with patch("joytrunk.config_store.list_employees_from_config", return_value=[{"id": "emp-A"}, {"id": "emp-B"}]):
        out = await tool.execute(target_employee_id="emp-A", content="hi")
    assert "不能给自己" in out


@pytest.mark.asyncio
async def test_execute_a2a_success_returns_reply(tool):
    with patch("joytrunk.config_store.list_employees_from_config", return_value=[{"id": "emp-A"}, {"id": "emp-B"}]):
        with patch("joytrunk.a2a_client.send_message") as m:
            m.return_value = ("agent reply", {"prompt_tokens": 1, "completion_tokens": 2})
            out = await tool.execute(target_employee_id="emp-B", content="hello")
    assert out == "agent reply"


@pytest.mark.asyncio
async def test_execute_a2a_unavailable_falls_back_to_loop(tool):
    with patch("joytrunk.config_store.list_employees_from_config", return_value=[{"id": "emp-A"}, {"id": "emp-B"}]):
        with patch("joytrunk.a2a_client.send_message", return_value=None):
            with patch("joytrunk.agent.loop.run_employee_loop", new_callable=AsyncMock) as mock_loop:
                mock_loop.return_value = ("direct reply", None)
                out = await tool.execute(target_employee_id="emp-B", content="hi")
    assert out == "direct reply"
    mock_loop.assert_called_once()
    args, kwargs = mock_loop.call_args
    assert args[0] == "emp-B"
    assert args[1] == "owner-1"
    assert args[2] == "hi"
