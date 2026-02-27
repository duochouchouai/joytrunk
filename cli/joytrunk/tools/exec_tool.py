"""Shell 执行工具（参考 nanobot.agent.tools.shell，独立实现）。"""

import asyncio
import os
import re
from pathlib import Path
from typing import Any

from joytrunk.tools.base import Tool


class ExecTool(Tool):
    def __init__(
        self,
        timeout: int = 60,
        working_dir: str | None = None,
        restrict_to_workspace: bool = False,
    ):
        self.timeout = timeout
        self.working_dir = working_dir
        self.restrict_to_workspace = restrict_to_workspace
        self.deny_patterns = [
            r"\brm\s+-[rf]{1,2}\b",
            r"\bdel\s+/[fq]\b",
            r"\brmdir\s+/s\b",
            r"(?:^|[;&|]\s*)format\b",
            r"\b(mkfs|diskpart)\b",
            r"\bdd\s+if=",
            r">\s*/dev/sd",
            r"\b(shutdown|reboot|poweroff)\b",
        ]

    @property
    def name(self) -> str:
        return "exec"

    @property
    def description(self) -> str:
        return "Execute a shell command and return its output. Use with caution. On Windows use PowerShell syntax."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "working_dir": {"type": "string", "description": "Optional working directory"},
            },
            "required": ["command"],
        }

    def _guard_command(self, command: str, cwd: str) -> str | None:
        cmd = command.strip().lower()
        for pat in self.deny_patterns:
            if re.search(pat, cmd):
                return "Error: Command blocked by safety guard (dangerous pattern)."
        if self.restrict_to_workspace:
            if ".." in command:
                return "Error: Command blocked (path traversal)."
            cwd_path = Path(cwd).resolve()
            for raw in re.findall(r"[A-Za-z]:\\[^\\\"']+", command) + re.findall(r"(?:^|[\s|>])(/[^\s\"'>]+)", command):
                try:
                    p = Path(raw.strip()).resolve()
                    if p.is_absolute() and cwd_path not in p.parents and p != cwd_path:
                        return "Error: Command blocked (path outside working dir)."
                except Exception:
                    pass
        return None

    async def execute(self, command: str, working_dir: str | None = None, **kwargs: Any) -> str:
        cwd = working_dir or self.working_dir or os.getcwd()
        err = self._guard_command(command, cwd)
        if err:
            return err
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=os.environ.copy(),
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError:
            process.kill()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                pass
            return f"Error: Command timed out after {self.timeout} seconds"
        parts = []
        if stdout:
            parts.append(stdout.decode("utf-8", errors="replace"))
        if stderr:
            t = stderr.decode("utf-8", errors="replace").strip()
            if t:
                parts.append(f"STDERR:\n{t}")
        if process.returncode != 0:
            parts.append(f"\nExit code: {process.returncode}")
        result = "\n".join(parts) if parts else "(no output)"
        if len(result) > 10000:
            result = result[:10000] + f"\n... (truncated, {len(result) - 10000} more chars)"
        return result
