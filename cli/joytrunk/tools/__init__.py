"""JoyTrunk 员工智能体工具集。"""

from pathlib import Path

from joytrunk.tools.base import Tool
from joytrunk.tools.exec_tool import ExecTool
from joytrunk.tools.filesystem import ListDirTool, ReadFileTool, WriteFileTool
from joytrunk.tools.registry import ToolRegistry

__all__ = [
    "Tool",
    "ToolRegistry",
    "ExecTool",
    "ReadFileTool",
    "WriteFileTool",
    "ListDirTool",
    "create_default_registry",
]


def create_default_registry(
    workspace: Path, employee_id: str, restrict_to_workspace: bool = True
) -> ToolRegistry:
    """创建默认工具注册表：exec、read_file、write_file、list_dir。"""
    allowed = workspace if restrict_to_workspace else None
    reg = ToolRegistry()
    reg.register(ReadFileTool(workspace, allowed, employee_id))
    reg.register(WriteFileTool(workspace, allowed, employee_id))
    reg.register(ListDirTool(workspace, allowed, employee_id))
    reg.register(
        ExecTool(
            working_dir=str(workspace),
            timeout=60,
            restrict_to_workspace=restrict_to_workspace,
        )
    )
    return reg
