"""文件系统工具：read_file、write_file、list_dir（参考 nanobot.agent.tools.filesystem，独立实现）。"""

import re
from pathlib import Path
from typing import Any

from joytrunk import paths
from joytrunk.tools.base import Tool


def _resolve_path(path: str, workspace: Path | None, allowed_dir: Path | None) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute() and workspace:
        p = workspace / p
    resolved = p.resolve()
    if allowed_dir:
        try:
            resolved.relative_to(allowed_dir.resolve())
        except ValueError:
            raise PermissionError(f"Path outside allowed directory: {path}")
    return resolved


class ReadFileTool(Tool):
    def __init__(self, workspace: Path, allowed_dir: Path | None, employee_id: str):
        self._workspace = workspace
        self._allowed_dir = allowed_dir
        self._employee_id = employee_id

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file at the given path."

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"path": {"type": "string", "description": "File path"}}, "required": ["path"]}

    async def execute(self, path: str, **kwargs: Any) -> str:
        try:
            fp = _resolve_path(path, self._workspace, self._allowed_dir)
            if not fp.exists():
                return f"Error: File not found: {path}"
            if not fp.is_file():
                return f"Error: Not a file: {path}"
            return fp.read_text(encoding="utf-8")
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


class WriteFileTool(Tool):
    def __init__(self, workspace: Path, allowed_dir: Path | None, employee_id: str):
        self._workspace = workspace
        self._allowed_dir = allowed_dir
        self._employee_id = employee_id

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file. Creates parent directories if needed."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        }

    async def execute(self, path: str, content: str, **kwargs: Any) -> str:
        try:
            fp = _resolve_path(path, self._workspace, self._allowed_dir)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} bytes to {path}"
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class ListDirTool(Tool):
    def __init__(self, workspace: Path, allowed_dir: Path | None, employee_id: str):
        self._workspace = workspace
        self._allowed_dir = allowed_dir
        self._employee_id = employee_id

    @property
    def name(self) -> str:
        return "list_dir"

    @property
    def description(self) -> str:
        return "List the contents of a directory."

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"path": {"type": "string", "description": "Directory path"}}, "required": ["path"]}

    async def execute(self, path: str, **kwargs: Any) -> str:
        try:
            dp = _resolve_path(path, self._workspace, self._allowed_dir)
            if not dp.exists():
                return f"Error: Directory not found: {path}"
            if not dp.is_dir():
                return f"Error: Not a directory: {path}"
            items = [("📁 " if x.is_dir() else "📄 ") + x.name for x in sorted(dp.iterdir())]
            return "\n".join(items) if items else f"Directory {path} is empty"
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error listing directory: {str(e)}"


def _edit_not_found_message(old_text: str, path: str) -> str:
    """Simple error when old_text is not found in file."""
    return f"Error: old_text not found in {path}. Provide the exact string to replace."


class EditFileTool(Tool):
    """Edit a file by replacing old_text with new_text. Same path rules as read_file/write_file."""

    def __init__(self, workspace: Path, allowed_dir: Path | None, employee_id: str):
        self._workspace = workspace
        self._allowed_dir = allowed_dir
        self._employee_id = employee_id

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Edit a file by replacing old_text with new_text. The old_text must exist exactly in the file."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "old_text": {"type": "string", "description": "Exact text to find and replace"},
                "new_text": {"type": "string", "description": "Text to replace with"},
            },
            "required": ["path", "old_text", "new_text"],
        }

    async def execute(self, path: str, old_text: str, new_text: str, **kwargs: Any) -> str:
        try:
            fp = _resolve_path(path, self._workspace, self._allowed_dir)
            if not fp.exists():
                return f"Error: File not found: {path}"
            if not fp.is_file():
                return f"Error: Not a file: {path}"
            content = fp.read_text(encoding="utf-8")
            if old_text not in content:
                return _edit_not_found_message(old_text, path)
            count = content.count(old_text)
            if count > 1:
                return f"Warning: old_text appears {count} times. Provide more context to make it unique."
            new_content = content.replace(old_text, new_text, 1)
            fp.write_text(new_content, encoding="utf-8")
            return f"Successfully edited {path}"
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error editing file: {str(e)}"
