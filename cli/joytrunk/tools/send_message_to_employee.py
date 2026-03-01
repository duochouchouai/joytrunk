"""
send_message_to_employee tool (plan phase 3): Agent A 向员工 B 发消息。
通过 A2A Send Message；Gateway 不可用时回退为直连 run_employee_loop。同 owner 校验由 Gateway 或本工具完成。
设计上可以「唤醒」其他 agent：直连时在本进程内同步执行目标员工的 run_employee_loop 获取回复，无需单独启动 Gateway。
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from joytrunk.tools.base import Tool


class SendMessageToEmployeeTool(Tool):
    """向指定员工发送消息（A2A 或直连）。仅允许同一 owner 下员工。"""

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
        return "send_message_to_employee"

    def description(self) -> str:
        return "向团队内另一员工发送消息并获取其回复。若用户提到「2号员工」「3号员工」等，请先调用 list_team_employees 查看当前员工列表，再用返回中的名称或 ID 作为 target_employee_id。参数：target_employee_id（员工 ID 或名称）、content（消息内容）。"

    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target_employee_id": {"type": "string", "description": "目标员工：员工 ID 或名称（如「1号员工」「2号员工」为名称时填该名称）"},
                "content": {"type": "string", "description": "消息内容"},
            },
            "required": ["target_employee_id", "content"],
        }

    async def execute(
        self,
        target_employee_id: str,
        content: str,
        **kwargs: Any,
    ) -> str:
        from joytrunk.config_store import list_employees_from_config, resolve_employee_id
        try:
            resolved_id = resolve_employee_id(self._owner_id, target_employee_id)
        except Exception as e:
            return f"错误：解析员工标识时出错（{e}）。请先调用 list_team_employees 查看当前员工列表。"
        if not resolved_id:
            employees = list_employees_from_config(self._owner_id)
            names = [str((e.get("name") or e.get("id") or "")) for e in employees[:10]]
            return f"错误：未找到员工「{target_employee_id}」。请先调用 list_team_employees 查看当前员工列表，再用返回中的名称或 ID 重试（当前同负责人员工：{', '.join(names)}{'…' if len(employees) > 10 else ''}）。"
        if resolved_id == self._from_employee_id:
            return "错误：不能给自己发消息。"

        from joytrunk import a2a_client
        result = None
        try:
            result = a2a_client.send_message(
                self._owner_id,
                resolved_id,
                content or "",
                session_key=None,
                from_employee_id=self._from_employee_id,
            )
        except Exception as e:
            pass  # 下面用直连 run_employee_loop 兜底
        if result is not None:
            reply, _usage = result
            return reply or "（无回复内容）"

        from joytrunk.agent.loop import run_employee_loop
        try:
            reply, _ = await run_employee_loop(
                resolved_id,
                self._owner_id,
                content or "",
                session_key="agent:" + self._from_employee_id,
            )
            return reply or "（无回复内容）"
        except Exception as e:
            return f"错误：向员工 {target_employee_id} 发送消息时失败（{e}）。若需通过 Gateway 转发，请先运行 joytrunk gateway；否则请确认目标员工配置正常。"
