"""工具注册表与执行（参考 nanobot.agent.tools.registry）。"""

from typing import Any

from joytrunk.tools.base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_definitions(self) -> list[dict[str, Any]]:
        return [t.to_schema() for t in self._tools.values()]

    async def execute(self, name: str, params: dict[str, Any]) -> str:
        hint = "\n\n[Analyze the error and try a different approach if needed.]"
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found. Available: {', '.join(self._tools.keys())}"
        try:
            errs = tool.validate_params(params)
            if errs:
                return f"Error: Invalid parameters for '{name}': " + "; ".join(errs) + hint
            result = await tool.execute(**params)
            if isinstance(result, str) and result.startswith("Error"):
                return result + hint
            return result
        except Exception as e:
            return f"Error executing {name}: {str(e)}" + hint
