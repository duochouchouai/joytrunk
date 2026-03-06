# -*- coding: utf-8 -*-
"""A2A Client（阶段 2）：get_gateway_base_url、gateway_available、send_message 与直连回退。端口仅从 cli/.env 读取。"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from joytrunk import a2a_client


def test_get_gateway_base_url_default_when_no_env(joytrunk_root):
    """无 .env 时使用默认 32900。"""
    with patch("joytrunk.a2a_client.paths.get_cli_root", return_value=Path(joytrunk_root)):
        with patch("joytrunk.a2a_client.os.environ", {}):
            url = a2a_client.get_gateway_base_url()
    assert url == "http://127.0.0.1:32900"


def test_get_gateway_base_url_from_env(joytrunk_root):
    """从环境变量 JOYTRUNK_A2A_PORT 读取端口。"""
    (Path(joytrunk_root) / ".env").write_text("JOYTRUNK_A2A_PORT=32902", encoding="utf-8")
    with patch("joytrunk.a2a_client.paths.get_cli_root", return_value=Path(joytrunk_root)):
        with patch.dict(os.environ, {"JOYTRUNK_A2A_PORT": "32902"}, clear=False):
            url = a2a_client.get_gateway_base_url()
    assert url == "http://127.0.0.1:32902"


def test_get_gateway_base_url_from_dotenv(joytrunk_root):
    """从 cli/.env 文件读取 JOYTRUNK_A2A_PORT。"""
    cli_root = Path(joytrunk_root)
    (cli_root / ".env").write_text("JOYTRUNK_A2A_PORT=32903\n", encoding="utf-8")
    with patch("joytrunk.a2a_client.paths.get_cli_root", return_value=cli_root):
        with patch.dict(os.environ, {}, clear=False):
            if "JOYTRUNK_A2A_PORT" in os.environ:
                del os.environ["JOYTRUNK_A2A_PORT"]
            url = a2a_client.get_gateway_base_url()
    assert url == "http://127.0.0.1:32903"


def test_send_message_returns_none_when_gateway_unavailable(joytrunk_root):
    """Gateway 不可达时返回 None（base URL 始终存在，但请求失败）。"""
    with patch("joytrunk.a2a_client.get_gateway_base_url", return_value="http://127.0.0.1:32900"):
        with patch("joytrunk.a2a_client.httpx") as mock_httpx:
            mock_httpx.Client.return_value.__enter__.return_value.post.side_effect = Exception("connection refused")
            assert a2a_client.send_message("o1", "e1", "hi") is None


@patch("joytrunk.a2a_client.get_gateway_base_url")
@patch("joytrunk.a2a_client.httpx")
def test_send_message_returns_reply_and_usage(mock_httpx_module, mock_base, joytrunk_root):
    mock_base.return_value = "http://127.0.0.1:32900"
    mock_resp = mock_httpx_module.Client.return_value.__enter__.return_value.post.return_value
    mock_resp.is_success = True
    mock_resp.json.return_value = {
        "history": [
            {"role": "user", "parts": [{"type": "text", "text": "q"}]},
            {"role": "agent", "parts": [{"type": "text", "text": "reply"}]},
        ],
        "metadata": {"usage": {"prompt_tokens": 10, "completion_tokens": 20}},
    }
    result = a2a_client.send_message("owner-1", "emp-1", "hello")
    assert result is not None
    reply, usage = result
    assert reply == "reply"
    assert usage == {"prompt_tokens": 10, "completion_tokens": 20}


@patch("joytrunk.a2a_client.get_gateway_base_url")
@patch("joytrunk.a2a_client.httpx")
def test_send_message_http_error_returns_none(mock_httpx_module, mock_base):
    mock_base.return_value = "http://127.0.0.1:32900"
    mock_resp = mock_httpx_module.Client.return_value.__enter__.return_value.post.return_value
    mock_resp.is_success = False
    assert a2a_client.send_message("o1", "e1", "hi") is None
