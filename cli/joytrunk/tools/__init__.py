"""JoyTrunk 员工智能体工具集。"""

from pathlib import Path

from joytrunk.tools.base import Tool
from joytrunk.tools.exec_tool import ExecTool
from joytrunk.tools.filesystem import EditFileTool, ListDirTool, ReadFileTool, WriteFileTool
from joytrunk.tools.memory_tools import SaveMemoryTool, SearchMemoryTool
from joytrunk.tools.registry import ToolRegistry
from joytrunk.tools.web import WebSearchTool

__all__ = [
    "Tool",
    "ToolRegistry",
    "ExecTool",
    "ReadFileTool",
    "WriteFileTool",
    "ListDirTool",
    "EditFileTool",
    "WebSearchTool",
    "SaveMemoryTool",
    "SearchMemoryTool",
    "create_default_registry",
]


def create_default_registry(
    workspace: Path, employee_id: str, restrict_to_workspace: bool = True
) -> ToolRegistry:
    """创建默认工具注册表：read_file、write_file、list_dir、exec、edit_file；若配置了 BRAVE_API_KEY 则加入 web_search；始终加入 save_memory、search_memory。"""
    import os

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
    if os.environ.get("BRAVE_API_KEY"):
        reg.register(WebSearchTool())
    try:
        reg.register(SaveMemoryTool(workspace, allowed, employee_id))
        reg.register(SearchMemoryTool(workspace, allowed, employee_id))
    except Exception:
        pass
    return reg
