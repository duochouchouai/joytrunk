"""工具基类与 OpenAI function 格式（参考 nanobot.agent.tools.base，独立实现）。"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """工具抽象基类。"""

    _TYPE_MAP = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        pass

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        schema = self.parameters or {}
        if schema.get("type", "object") != "object":
            return [f"Schema must be object type"]
        return self._validate(params, {**schema, "type": "object"}, "")

    def _validate(self, val: Any, schema: dict, path: str) -> list[str]:
        t, label = schema.get("type"), path or "parameter"
        if t in self._TYPE_MAP:
            if not isinstance(val, self._TYPE_MAP[t]):
                return [f"{label} should be {t}"]
        errors = []
        if "enum" in schema and val not in schema["enum"]:
            errors.append(f"{label} must be one of {schema['enum']}")
        if t == "object":
            props = schema.get("properties", {})
            for k in schema.get("required", []):
                if k not in val:
                    errors.append(f"missing required {path + '.' + k if path else k}")
            for k, v in (val or {}).items():
                if k in props:
                    errors.extend(self._validate(v, props[k], path + "." + k if path else k))
        return errors

    def to_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
