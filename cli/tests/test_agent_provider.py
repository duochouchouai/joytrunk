"""测试 joytrunk.agent.provider。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from joytrunk.agent.provider import (
    _parse_response,
    chat,
    chat_via_router,
)


def test_parse_response_content_only():
    data = {
        "choices": [{"message": {"content": "Hello", "role": "assistant"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    r = _parse_response(data)
    assert r.content == "Hello"
    assert r.usage == {"prompt_tokens": 10, "completion_tokens": 5}
    assert r.tool_calls == []
    assert r.has_tool_calls is False


def test_parse_response_tool_calls():
    data = {
        "choices": [{
            "message": {
                "content": "",
                "role": "assistant",
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path": "a.txt"}'},
                }],
            },
        }],
        "usage": {},
    }
    r = _parse_response(data)
    assert r.has_tool_calls is True
    assert len(r.tool_calls) == 1
    assert r.tool_calls[0].id == "call_1"
    assert r.tool_calls[0].name == "read_file"
    assert r.tool_calls[0].arguments == {"path": "a.txt"}


def test_parse_response_empty_choices():
    r = _parse_response({"choices": []})
    assert r.content == ""
    assert r.usage is None
    assert r.tool_calls == []


@pytest.mark.asyncio
async def test_chat_calls_url():
    resp_json = {
        "choices": [{"message": {"content": "Hi", "role": "assistant"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }
    mock_response = MagicMock(raise_for_status=MagicMock(), json=MagicMock(return_value=resp_json))
    with patch("joytrunk.agent.provider.httpx") as m_httpx:
        mock_post = AsyncMock(return_value=mock_response)
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=AsyncMock(post=mock_post))
        mock_client.__aexit__ = AsyncMock(return_value=None)
        m_httpx.AsyncClient.return_value = mock_client
        r = await chat(
            "https://api.example.com/v1",
            "sk-key",
            "gpt-3.5-turbo",
            [{"role": "user", "content": "Hello"}],
        )
    assert r.content == "Hi"
    assert r.usage["prompt_tokens"] == 1
    assert mock_post.await_count == 1


@pytest.mark.asyncio
async def test_chat_via_router_calls_gateway():
    resp_json = {
        "choices": [{"message": {"content": "From router", "role": "assistant"}}],
        "usage": {"prompt_tokens": 2, "completion_tokens": 2},
    }
    mock_response = MagicMock(raise_for_status=MagicMock(), json=MagicMock(return_value=resp_json))
    with patch("joytrunk.agent.provider.httpx") as m_httpx:
        mock_post = AsyncMock(return_value=mock_response)
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=AsyncMock(post=mock_post))
        mock_client.__aexit__ = AsyncMock(return_value=None)
        m_httpx.AsyncClient.return_value = mock_client
        r = await chat_via_router(
            "http://localhost:32890",
            "owner-1",
            "gpt-3.5-turbo",
            [{"role": "user", "content": "Hi"}],
        )
    assert r.content == "From router"
    assert r.usage["completion_tokens"] == 2
    call_kw = mock_post.call_args[1]
    assert call_kw["headers"].get("X-Owner-Id") == "owner-1"
