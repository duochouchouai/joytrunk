# -*- coding: utf-8 -*-
"""A2A Client（阶段 2）：get_gateway_base_url、gateway_available、send_message 与直连回退。"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from joytrunk import a2a_client


def test_get_gateway_base_url_no_gateway(joytrunk_root):
    (joytrunk_root / "config.json").write_text(json.dumps({"version": 1, "ownerId": "o1"}, ensure_ascii=False), encoding="utf-8")
    with patch("joytrunk.a2a_client.load_config") as m:
        m.return_value = {"version": 1}
        assert a2a_client.get_gateway_base_url() is None


def test_get_gateway_base_url_from_port(joytrunk_root):
    (joytrunk_root / "config.json").write_text(
        json.dumps({"version": 1, "gateway": {"a2a_port": 32891}, "server": {"host": "127.0.0.1"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    from joytrunk.config_store import load_config
    with patch("joytrunk.a2a_client.load_config", load_config):
        url = a2a_client.get_gateway_base_url()
    assert url == "http://127.0.0.1:32891"


def test_get_gateway_base_url_from_backend_url(joytrunk_root):
    (joytrunk_root / "config.json").write_text(
        json.dumps({"version": 1, "gateway": {"a2a_backend_url": "http://localhost:32891/"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    from joytrunk.config_store import load_config
    with patch("joytrunk.a2a_client.load_config", load_config):
        url = a2a_client.get_gateway_base_url()
    assert url == "http://localhost:32891"


def test_send_message_returns_none_when_no_base(joytrunk_root):
    (joytrunk_root / "config.json").write_text(json.dumps({"version": 1}, ensure_ascii=False), encoding="utf-8")
    with patch("joytrunk.a2a_client.get_gateway_base_url", return_value=None):
        assert a2a_client.send_message("o1", "e1", "hi") is None


@patch("joytrunk.a2a_client.get_gateway_base_url")
@patch("joytrunk.a2a_client.httpx")
def test_send_message_returns_reply_and_usage(mock_httpx_module, mock_base, joytrunk_root):
    mock_base.return_value = "http://127.0.0.1:32891"
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
    mock_base.return_value = "http://127.0.0.1:32891"
    mock_resp = mock_httpx_module.Client.return_value.__enter__.return_value.post.return_value
    mock_resp.is_success = False
    assert a2a_client.send_message("o1", "e1", "hi") is None
