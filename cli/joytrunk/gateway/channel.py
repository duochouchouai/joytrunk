"""
Channel 接口与注册（plan §6 阶段 4、10.30）：IM 平台消息 → A2A/InboundMessage；Worker 产出 → Channel.send。
首期仅定义接口与注册表，不实现具体 IM；各 Channel 实现方按 (channel, chat_id) 约定文档说明。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# 预定义 channel 类型常量（10.30）
CHANNEL_CLI = "cli"
CHANNEL_WEB = "web"
CHANNEL_AGENT = "agent"
CHANNEL_FEISHU = "feishu"
CHANNEL_TELEGRAM = "telegram"


class Channel(ABC):
    """
    出站通道：Gateway 将 Worker 产出的 OutboundMessage 按 (channel, chat_id) 路由到对应 Channel，
    由实现方将 A2A Message/Part 转为平台格式并发送。
    """

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """返回 channel 类型标识，如 feishu、telegram、web。"""

    @abstractmethod
    async def send(
        self,
        chat_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        将内容发送到指定 chat_id 对应的会话端点。
        content: 文本内容（对应 A2A agent Message 的 text Part）。
        metadata: 可选，含 task_id、usage 等，供实现方记录或回执。
        """


_registry: dict[str, Channel] = {}


def register_channel(channel: Channel) -> None:
    """注册 Channel 实现；同一 channel_type 后注册覆盖先注册。"""
    _registry[channel.channel_type] = channel


def get_channel(channel_type: str) -> Channel | None:
    """按 channel 类型获取已注册的 Channel。"""
    return _registry.get(channel_type)


def list_channels() -> list[str]:
    """返回已注册的 channel_type 列表。"""
    return list(_registry.keys())
