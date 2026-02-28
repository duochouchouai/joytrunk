# -*- coding: utf-8 -*-
"""集成测试：验证 joytrunk chat 所用 API 能连上 server（127.0.0.1）。"""

import json

import httpx
import pytest


def _server_health_ok(host: str = "127.0.0.1", port: int = 32890) -> bool:
    try:
        r = httpx.get(f"http://{host}:{port}/api/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def test_get_base_url_normalizes_localhost():
    """get_base_url() 将 localhost 规范为 127.0.0.1，避免 Windows IPv6 连不上。"""
    from unittest.mock import patch

    from joytrunk.api_client import get_base_url

    with patch("joytrunk.api_client._load_config") as load:
        load.return_value = {"server": {"host": "localhost", "port": 32890}}
        url = get_base_url()
        assert "127.0.0.1" in url
        assert "32890" in url


@pytest.mark.skipif(not _server_health_ok(), reason="server not running on 127.0.0.1:32890")
def test_chat_reaches_server_when_running(joytrunk_root, monkeypatch):
    """当本机已有 server 在 127.0.0.1:32890 时，ensure_owner_via_server() 能连上并返回 ownerId。"""
    monkeypatch.setenv("JOYTRUNK_ROOT", str(joytrunk_root))
    (joytrunk_root / "config.json").write_text(
        json.dumps({"server": {"host": "127.0.0.1", "port": 32890}, "version": 1}, ensure_ascii=False),
        encoding="utf-8",
    )
    from joytrunk.api_client import ensure_owner_via_server, get_base_url

    assert get_base_url() == "http://127.0.0.1:32890"
    owner_id, _ = ensure_owner_via_server()
    assert owner_id is not None
    assert len(owner_id) > 0
