"""员工会话历史：按会话键持久化到 workspace/employees/<id>/sessions/（供 CLI 与后续 server 共用）。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from joytrunk import paths

# 单次上下文中保留的最近消息数（与 nanobot memory_window 类似）
DEFAULT_MEMORY_WINDOW = 50
# 工具结果截断长度
TOOL_RESULT_MAX_CHARS = 500


def _sessions_dir(employee_id: str) -> Path:
    return paths.get_employee_dir(employee_id) / "sessions"


def _session_file(employee_id: str, session_key: str) -> Path:
    # 键中若有非法文件名字符，用替换
    safe = session_key.replace(":", "_").replace("/", "_")
    return _sessions_dir(employee_id) / f"{safe}.json"


def load_history(employee_id: str, session_key: str) -> list[dict[str, Any]]:
    """加载该员工该会话的历史消息列表。"""
    f = _session_file(employee_id, session_key)
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data.get("messages", []) if isinstance(data, dict) else []
    except Exception:
        return []


def save_history(
    employee_id: str,
    session_key: str,
    messages: list[dict[str, Any]],
) -> None:
    """保存历史；对 tool 消息的 content 做截断。"""
    out: list[dict[str, Any]] = []
    for m in messages:
        entry = dict(m)
        if entry.get("role") == "tool" and isinstance(entry.get("content"), str):
            c = entry["content"]
            if len(c) > TOOL_RESULT_MAX_CHARS:
                entry["content"] = c[:TOOL_RESULT_MAX_CHARS] + "\n... (truncated)"
        if "reasoning_content" in entry:
            del entry["reasoning_content"]
        entry.setdefault("timestamp", datetime.now().isoformat())
        out.append(entry)

    dir_path = _sessions_dir(employee_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    _session_file(employee_id, session_key).write_text(
        json.dumps({"messages": out, "updated_at": datetime.now().isoformat()}, ensure_ascii=False, indent=0),
        encoding="utf-8",
    )


def append_turn(
    employee_id: str,
    session_key: str,
    new_messages: list[dict[str, Any]],
    skip_count: int,
) -> None:
    """将本轮的 assistant/tool 等消息追加到历史并落盘。"""
    history = load_history(employee_id, session_key)
    for m in new_messages[skip_count:]:
        entry = {k: v for k, v in m.items() if k != "reasoning_content"}
        if entry.get("role") == "tool" and isinstance(entry.get("content"), str):
            c = entry["content"]
            if len(c) > TOOL_RESULT_MAX_CHARS:
                entry["content"] = c[:TOOL_RESULT_MAX_CHARS] + "\n... (truncated)"
        if entry.get("role") == "user" and isinstance(entry.get("content"), list):
            entry["content"] = [
                {"type": "text", "text": "[image]"} if (
                    isinstance(c, dict) and c.get("type") == "image_url"
                ) else c
                for c in entry["content"]
            ]
        entry.setdefault("timestamp", datetime.now().isoformat())
        history.append(entry)
    save_history(employee_id, session_key, history)
