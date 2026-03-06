"""MCP client: connects to MCP servers and wraps their tools as JoyTrunk tools (mirrors nanobot.agent.tools.mcp)."""

from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Any

import httpx

from joytrunk.tools.base import Tool
from joytrunk.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class MCPToolWrapper(Tool):
    """Wraps a single MCP server tool as a JoyTrunk Tool."""

    def __init__(self, session: Any, server_name: str, tool_def: Any, tool_timeout: int = 30) -> None:
        self._session = session
        self._original_name = tool_def.name
        self._name = f"mcp_{server_name}_{tool_def.name}"
        self._description = tool_def.description or tool_def.name
        self._parameters = tool_def.inputSchema or {"type": "object", "properties": {}}
        self._tool_timeout = tool_timeout

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    async def execute(self, **kwargs: Any) -> str:
        from mcp import types

        try:
            result = await asyncio.wait_for(
                self._session.call_tool(self._original_name, arguments=kwargs),
                timeout=self._tool_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("MCP tool '%s' timed out after %ds", self._name, self._tool_timeout)
            return f"(MCP tool call timed out after {self._tool_timeout}s)"
        parts = []
        for block in result.content:
            if isinstance(block, types.TextContent):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return "\n".join(parts) or "(no output)"


async def connect_mcp_servers(
    mcp_servers: dict[str, Any],
    registry: ToolRegistry,
    stack: AsyncExitStack,
) -> None:
    """Connect to configured MCP servers and register their tools. Config entries are dicts with command/args/env or url/headers, and optional tool_timeout."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    for name, cfg in mcp_servers.items():
        if not isinstance(cfg, dict):
            logger.warning("MCP server '%s': config must be a dict, skipping", name)
            continue
        try:
            command = cfg.get("command")
            args = cfg.get("args") or []
            env = cfg.get("env")
            url = cfg.get("url")
            headers = cfg.get("headers")
            tool_timeout = int(cfg.get("tool_timeout", 30))

            if command:
                params = StdioServerParameters(
                    command=command,
                    args=args if isinstance(args, list) else [],
                    env=env if isinstance(env, dict) else None,
                )
                read, write = await stack.enter_async_context(stdio_client(params))
            elif url:
                from mcp.client.streamable_http import streamable_http_client

                http_client = await stack.enter_async_context(
                    httpx.AsyncClient(
                        headers=headers if isinstance(headers, dict) else None,
                        follow_redirects=True,
                        timeout=None,
                    )
                )
                read, write, _ = await stack.enter_async_context(
                    streamable_http_client(url, http_client=http_client)
                )
            else:
                logger.warning("MCP server '%s': no command or url configured, skipping", name)
                continue

            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            tools = await session.list_tools()
            tools_list = getattr(tools, "tools", None) or []
            for tool_def in tools_list:
                wrapper = MCPToolWrapper(session, name, tool_def, tool_timeout=tool_timeout)
                registry.register(wrapper)
                logger.debug("MCP: registered tool '%s' from server '%s'", wrapper.name, name)
            logger.info("MCP server '%s': connected, %d tools registered", name, len(tools_list))
        except Exception as e:
            logger.error("MCP server '%s': failed to connect: %s", name, e)
