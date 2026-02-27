"""测试 joytrunk.tools。"""

import pytest

from joytrunk.tools import (
    ExecTool,
    ListDirTool,
    ReadFileTool,
    ToolRegistry,
    WriteFileTool,
    create_default_registry,
)

def test_registry_register_get():
    reg = ToolRegistry()
    assert reg.get("read_file") is None
    from pathlib import Path
    ws = Path("/tmp")
    reg.register(ReadFileTool(ws, None, "emp-1"))
    assert reg.get("read_file") is not None
    assert reg.get_definitions()
    assert len(reg.get_definitions()) == 1
    assert reg.get_definitions()[0]["function"]["name"] == "read_file"


@pytest.mark.asyncio
async def test_registry_execute_unknown():
    reg = ToolRegistry()
    out = await reg.execute("nonexistent", {})
    assert "not found" in out
    assert "Available" in out


@pytest.mark.asyncio
async def test_read_file_tool(employee_dir):
    (employee_dir / "hello.txt").write_text("hello world", encoding="utf-8")
    tool = ReadFileTool(employee_dir, employee_dir, "emp-001")
    out = await tool.execute(path="hello.txt")
    assert out == "hello world"


@pytest.mark.asyncio
async def test_read_file_tool_not_found(employee_dir):
    tool = ReadFileTool(employee_dir, employee_dir, "emp-001")
    out = await tool.execute(path="nonexistent.txt")
    assert "Error" in out
    assert "not found" in out


@pytest.mark.asyncio
async def test_write_file_tool(employee_dir):
    tool = WriteFileTool(employee_dir, employee_dir, "emp-001")
    out = await tool.execute(path="new.txt", content="new content")
    assert "Successfully" in out
    assert (employee_dir / "new.txt").read_text(encoding="utf-8") == "new content"


@pytest.mark.asyncio
async def test_list_dir_tool(employee_dir):
    (employee_dir / "a.txt").write_text("")
    (employee_dir / "sub").mkdir()
    tool = ListDirTool(employee_dir, employee_dir, "emp-001")
    out = await tool.execute(path=".")
    assert "a.txt" in out
    assert "sub" in out


@pytest.mark.asyncio
async def test_exec_tool_safe_command(employee_dir):
    tool = ExecTool(working_dir=str(employee_dir), timeout=5, restrict_to_workspace=True)
    out = await tool.execute(command="echo hello")
    assert "hello" in out


@pytest.mark.asyncio
async def test_exec_tool_blocked(employee_dir):
    tool = ExecTool(working_dir=str(employee_dir), timeout=5, restrict_to_workspace=True)
    out = await tool.execute(command="rm -rf /")
    assert "Error" in out
    assert "blocked" in out or "guard" in out


@pytest.mark.asyncio
async def test_edit_file_tool(employee_dir):
    from joytrunk.tools.filesystem import EditFileTool
    (employee_dir / "f.txt").write_text("hello world", encoding="utf-8")
    tool = EditFileTool(employee_dir, employee_dir, "emp-001")
    out = await tool.execute(path="f.txt", old_text="world", new_text="edit_file")
    assert "Successfully" in out
    assert (employee_dir / "f.txt").read_text(encoding="utf-8") == "hello edit_file"


@pytest.mark.asyncio
async def test_edit_file_tool_old_text_not_found(employee_dir):
    from joytrunk.tools.filesystem import EditFileTool
    (employee_dir / "g.txt").write_text("only this", encoding="utf-8")
    tool = EditFileTool(employee_dir, employee_dir, "emp-001")
    out = await tool.execute(path="g.txt", old_text="missing", new_text="x")
    assert "Error" in out
    assert "not found" in out


def test_create_default_registry(employee_dir):
    from pathlib import Path
    reg = create_default_registry(Path(employee_dir), "emp-001", restrict_to_workspace=True)
    names = [d["function"]["name"] for d in reg.get_definitions()]
    assert "read_file" in names
    assert "write_file" in names
    assert "list_dir" in names
    assert "exec" in names
    assert "edit_file" in names
