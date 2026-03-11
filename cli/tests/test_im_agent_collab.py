# -*- coding: utf-8 -*-
"""IM 多 Agent 协作（协调员方案）相关测试：on_agent_reply 回调、worker 装配、official_ws_client 上报。"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRunEmployeeLoopOnAgentReply:
    """run_employee_loop 将 on_agent_reply 传给 create_default_registry。"""

    @pytest.mark.asyncio
    async def test_run_employee_loop_passes_on_agent_reply_to_registry(self, employee_dir):
        import json
        (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
        (employee_dir / "config.json").write_text(json.dumps({"id": "emp-001", "ownerId": "owner-1"}), encoding="utf-8")

        with patch("joytrunk.tools.create_default_registry") as mk_reg:
            reg = MagicMock()
            reg.get_definitions.return_value = []
            mk_reg.return_value = reg
            with patch("joytrunk.agent.loop.get_llm_params", return_value={
                "source": "router",
                "model": "test",
                "max_tokens": 1024,
                "temperature": 0.1,
                "server_base_url": "http://test",
                "owner_id": "owner-1",
                "router_api_key": None,
            }):
                with patch("joytrunk.agent.loop.load_history", return_value=[]):
                    with patch("joytrunk.agent.loop.get_merged_config_for_employee", return_value={}):
                        with patch("joytrunk.agent.loop.get_memory_config", return_value={}):
                            with patch("joytrunk.agent.loop._memory_clients", return_value=(None, None)):
                                with patch("joytrunk.agent.loop.chat_via_router", new_callable=AsyncMock) as chat:
                                    chat.return_value = MagicMock(
                                        content="ok",
                                        has_tool_calls=False,
                                        tool_calls=[],
                                        usage={"prompt_tokens": 1, "completion_tokens": 1},
                                    )
                                    with patch("joytrunk.agent.loop.append_turn"):
                                        with patch("joytrunk.agent.loop.run_log"):
                                            from joytrunk.agent.loop import run_employee_loop

                                            cb = AsyncMock()
                                            await run_employee_loop(
                                                "emp-001",
                                                "owner-1",
                                                "hi",
                                                on_agent_reply=cb,
                                            )
                                    mk_reg.assert_called_once()
                                    call_kw = mk_reg.call_args[1]
                                    assert call_kw.get("on_agent_reply") is cb


class TestWorkerOnAgentReply:
    """Worker 在 channel=official 且 chat_id 存在时传入 on_agent_reply。"""

    @pytest.mark.asyncio
    async def test_process_one_official_with_chat_id_passes_on_agent_reply(self):
        from joytrunk.bus.events import InboundMessage
        from joytrunk.gateway.worker import _process_one
        from joytrunk.gateway.task_store import TaskStore

        inbound = InboundMessage(
            task_id="t1",
            target_employee_id="coordinator",
            owner_id="owner-1",
            content="topic",
            session_key="owner",
            channel="official",
            chat_id="conv-123",
        )
        store = MagicMock(spec=TaskStore)
        store.complete = AsyncMock()

        with patch("joytrunk.gateway.worker.run_employee_loop", new_callable=AsyncMock) as mock_loop:
            mock_loop.return_value = ("done", None)
            await _process_one(inbound, store)
            mock_loop.assert_called_once()
            call_kw = mock_loop.call_args[1]
            assert "on_agent_reply" in call_kw
            assert callable(call_kw["on_agent_reply"])

    @pytest.mark.asyncio
    async def test_process_one_official_without_chat_id_no_on_agent_reply(self):
        from joytrunk.bus.events import InboundMessage
        from joytrunk.gateway.worker import _process_one
        from joytrunk.gateway.task_store import TaskStore

        inbound = InboundMessage(
            task_id="t2",
            target_employee_id="emp-1",
            owner_id="owner-1",
            content="hi",
            session_key="owner",
            channel="official",
            chat_id="",  # 无 chat_id
        )
        store = MagicMock(spec=TaskStore)
        store.complete = AsyncMock()

        with patch("joytrunk.gateway.worker.run_employee_loop", new_callable=AsyncMock) as mock_loop:
            mock_loop.return_value = ("done", None)
            await _process_one(inbound, store)
            call_kw = mock_loop.call_args[1]
            assert call_kw.get("on_agent_reply") is None


class TestSendAgentReplyToOfficial:
    """official_ws_client.send_agent_reply_to_official 发送正确 payload。"""

    @pytest.mark.asyncio
    async def test_send_agent_reply_to_official_payload(self):
        import json
        from joytrunk.official_ws_client import send_agent_reply_to_official

        sent = []

        async def fake_send(data):
            sent.append(json.loads(data))

        with patch("joytrunk.official_ws_client._lock", asyncio.Lock()):
            with patch("joytrunk.official_ws_client._ws", MagicMock(send=AsyncMock(side_effect=fake_send))):
                await send_agent_reply_to_official(
                    conversation_id="conv-1",
                    owner_id="owner-1",
                    employee_id="emp-B",
                    content="hello from B",
                )
        assert len(sent) == 1
        payload = sent[0]
        assert payload["type"] == "agent_reply"
        assert payload["conversation_id"] == "conv-1"
        assert payload["owner_id"] == "owner-1"
        assert payload["employee_id"] == "emp-B"
        assert payload["content"] == "hello from B"

    @pytest.mark.asyncio
    async def test_send_agent_reply_to_official_no_ws_skips(self):
        from joytrunk.official_ws_client import send_agent_reply_to_official

        with patch("joytrunk.official_ws_client._lock", asyncio.Lock()):
            with patch("joytrunk.official_ws_client._ws", None):
                await send_agent_reply_to_official("c", "o", "e", "x")
        # 无异常、不发送即可
        pass
