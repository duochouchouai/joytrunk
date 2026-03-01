"""
list_team_employees：列出同负责人下所有员工（id、名称），供 send_message_to_employee 前先查看。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from joytrunk.tools.base import Tool


class ListTeamEmployeesTool(Tool):
    """列出当前负责人下的所有员工（id 与名称），便于向指定员工发消息时使用正确 ID 或名称。"""

    def __init__(
        self,
        workspace: Path,
        allowed_dir: Path | None,
        from_employee_id: str,
        owner_id: str,
    ) -> None:
        self._workspace = workspace
        self._allowed_dir = allowed_dir
        self._from_employee_id = from_employee_id
        self._owner_id = owner_id

    def name(self) -> str:
        return "list_team_employees"

    def description(self) -> str:
        return "列出当前负责人下的所有员工（id 与名称）。在用户提到「2号员工」「3号员工」等时，应先调用本工具查看列表，再用返回中的名称或 ID 调用 send_message_to_employee 联系对应员工。无参数。"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        try:
            from joytrunk.config_store import list_employees_from_config
            employees = list_employees_from_config(self._owner_id)
        except Exception as e:
            return f"错误：获取员工列表失败（{e}）。请确认已运行 joytrunk onboard 且 workspace/employees 存在。"
        if not employees:
            return "当前负责人下暂无其他员工。"
        lines = []
        for i, e in enumerate(employees, 1):
            eid = str(e.get("id") or "")
            name = str(e.get("name") or "").strip() or eid
            self_mark = "（本员工）" if eid == self._from_employee_id else ""
            lines.append(f"{i}. {name} (id: {eid}){self_mark}")
        return "当前同负责人员工：\n" + "\n".join(lines)
