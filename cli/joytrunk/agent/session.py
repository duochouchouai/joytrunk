"""员工与负责人的对话历史：按固定键持久化到 workspace/employees/<id>/sessions/，CLI 与网页共用同一上下文，无 session 区分。
聊天记录同时写入该员工的 memory.db（chat_messages 表），与负责人、其他智能体的对话均入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from joytrunk import paths

# 员工与负责人之间仅有一条连续对话，CLI/网页共用此 key，不因渠道切换而换「session」
OWNER_CHAT_KEY = "owner"

# 单次上下文中保留的最近消息数（与 nanobot memory_window 类似）
DEFAULT_MEMORY_WINDOW = 50
# 工具结果截断长度
TOOL_RESULT_MAX_CHARS = 500
# DB 中最多保留的聊天条数（按 session 维度）
CHAT_DB_LIMIT = 500


def _get_chat_repo(employee_id: str):
    """获取该员工的聊天记录 repo（memory.db 内），失败返回 None。"""
    try:
        from joytrunk.agent.memory import get_store
        return get_store(employee_id).chat_message_repo
    except Exception:
        return None


def _sessions_dir(employee_id: str) -> Path:
    return paths.get_employee_dir(employee_id) / "sessions"


def _session_file(employee_id: str, session_key: str) -> Path:
    # 键中若有非法文件名字符，用替换
    safe = session_key.replace(":", "_").replace("/", "_")
    return _sessions_dir(employee_id) / f"{safe}.json"


def load_history(employee_id: str, session_key: str) -> list[dict[str, Any]]:
    """加载该员工与该会话键对应的历史消息列表。与负责人对话统一使用 OWNER_CHAT_KEY。优先从 DB 读，无则从文件迁入。"""
    repo = _get_chat_repo(employee_id)
    if repo is not None:
        try:
            messages = repo.get_messages(session_key, limit=CHAT_DB_LIMIT)
            if messages:
                return messages
        except Exception:
            pass
    f = _session_file(employee_id, session_key)
    if not f.exists():
        # 升级兼容：曾用 cli_direct 的对话历史迁到 owner，避免换 key 后历史丢失
        if session_key == OWNER_CHAT_KEY:
            legacy = _session_file(employee_id, "cli_direct")
            if legacy.exists():
                try:
                    data = json.loads(legacy.read_text(encoding="utf-8"))
                    messages = data.get("messages", []) if isinstance(data, dict) else []
                    if messages:
                        save_history(employee_id, OWNER_CHAT_KEY, messages)
                        return messages
                except Exception:
                    pass
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        messages = data.get("messages", []) if isinstance(data, dict) else []
        if messages and repo is not None:
            try:
                repo.replace_messages(session_key, messages)
            except Exception:
                pass
        return messages
    except Exception:
        return []


def _serialize_message(entry: dict[str, Any]) -> dict[str, Any]:
    """深拷贝并确保 entry 可 JSON 序列化（剔除或转换 method 等不可序列化类型）。"""
    out: dict[str, Any] = {}
    for k, v in entry.items():
        if v is None or isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, dict):
            out[k] = _serialize_message(v)
        elif isinstance(v, list):
            out[k] = [
                _serialize_message(x) if isinstance(x, dict) else (
                    x if isinstance(x, (str, int, float, bool, type(None))) else str(x)
                )
                for x in v
            ]
        elif isinstance(v, (datetime, Path)):
            out[k] = str(v)
        else:
            out[k] = str(v)
    return out


def save_history(
    employee_id: str,
    session_key: str,
    messages: list[dict[str, Any]],
) -> None:
    """保存历史；对 tool 消息的 content 做截断，并确保可 JSON 序列化。同时写入 DB（chat_messages）与 sessions 文件。"""
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
        out.append(_serialize_message(entry))

    repo = _get_chat_repo(employee_id)
    if repo is not None:
        try:
            repo.replace_messages(session_key, out)
        except Exception:
            pass

    dir_path = _sessions_dir(employee_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    _session_file(employee_id, session_key).write_text(
        json.dumps({"messages": out, "updated_at": datetime.now().isoformat()}, ensure_ascii=False, indent=0, default=str),
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
        history.append(_serialize_message(entry))
    save_history(employee_id, session_key, history)
