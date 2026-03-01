# -*- coding: utf-8 -*-
"""Channel 接口与注册（阶段 4，方案 10.30、10.45）。"""

import pytest

from joytrunk.gateway.channel import (
    CHANNEL_AGENT,
    CHANNEL_CLI,
    CHANNEL_FEISHU,
    CHANNEL_TELEGRAM,
    CHANNEL_WEB,
    Channel,
    get_channel,
    list_channels,
    register_channel,
)


class DummyChannel(Channel):
    def __init__(self, channel_type: str):
        self._type = channel_type

    @property
    def channel_type(self) -> str:
        return self._type

    async def send(self, chat_id: str, content: str, metadata=None):
        pass


def test_channel_constants():
    assert CHANNEL_CLI == "cli"
    assert CHANNEL_WEB == "web"
    assert CHANNEL_AGENT == "agent"
    assert CHANNEL_FEISHU == "feishu"
    assert CHANNEL_TELEGRAM == "telegram"


def test_register_and_get():
    c = DummyChannel("feishu")
    register_channel(c)
    try:
        assert get_channel("feishu") is c
        assert "feishu" in list_channels()
    finally:
        import joytrunk.gateway.channel as mod
        mod._registry.clear()


def test_get_channel_missing_returns_none():
    import joytrunk.gateway.channel as mod
    mod._registry.clear()
    assert get_channel("nonexistent") is None
    assert list_channels() == []
