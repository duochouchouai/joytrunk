"""JoyTrunk 员工智能体工具集。"""

from pathlib import Path
from typing import Any

from joytrunk.tools.base import Tool
from joytrunk.tools.exec_tool import ExecTool
from joytrunk.tools.filesystem import EditFileTool, ListDirTool, ReadFileTool, WriteFileTool
from joytrunk.tools.registry import ToolRegistry
from joytrunk.tools.web import WebFetchTool, WebSearchTool

__all__ = [
    "Tool",
    "ToolRegistry",
    "ExecTool",
    "ReadFileTool",
    "WriteFileTool",
    "ListDirTool",
    "EditFileTool",
    "WebSearchTool",
    "WebFetchTool",
    "create_default_registry",
]


def _search_api_key_from_config(tools_config: dict[str, Any] | None) -> str:
    """Resolve web search API key: config (tools.web.search.apiKey) overrides env BRAVE_API_KEY."""
    import os

    if tools_config:
        web = tools_config.get("web")
        if isinstance(web, dict):
            search = web.get("search")
            if isinstance(search, dict) and search.get("apiKey"):
                return str(search["apiKey"]).strip()
    return os.environ.get("BRAVE_API_KEY", "")


def create_default_registry(
    workspace: Path,
    employee_id: str,
    restrict_to_workspace: bool = True,
    tools_config: dict[str, Any] | None = None,
) -> ToolRegistry:
    """创建默认工具注册表：文件系统、exec、web_search（始终注册）、web_fetch。MCP 在 loop 内通过 connect_mcp_servers 注册。"""
    allowed = workspace if restrict_to_workspace else None
    reg = ToolRegistry()
    reg.register(ReadFileTool(workspace, allowed, employee_id))
    reg.register(WriteFileTool(workspace, allowed, employee_id))
    reg.register(ListDirTool(workspace, allowed, employee_id))
    reg.register(EditFileTool(workspace, allowed, employee_id))
    reg.register(
        ExecTool(
            working_dir=str(workspace),
            timeout=60,
            restrict_to_workspace=restrict_to_workspace,
        )
    )
    api_key = _search_api_key_from_config(tools_config)
    reg.register(WebSearchTool(api_key=api_key or None))
    max_chars = 50000
    if tools_config:
        web = tools_config.get("web")
        if isinstance(web, dict) and isinstance(web.get("fetch"), dict) and "maxChars" in web["fetch"]:
            max_chars = int(web["fetch"]["maxChars"])
    reg.register(WebFetchTool(max_chars=max_chars))
    return reg
