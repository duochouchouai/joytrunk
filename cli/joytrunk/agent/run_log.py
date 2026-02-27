"""员工智能体运行时结构化日志：JSONL 写入工作区 employees/<id>/logs/agent.jsonl，便于前端加载与 debug。

每条日志一行 JSON，字段：
- ts: ISO 8601 UTC 时间戳
- event: 事件类型（见 EVENT_* 常量）
- employee_id: 员工 ID
- run_id: 本轮循环唯一 ID，用于前端按会话分组
- payload: 事件相关数据（因 event 而异）
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from joytrunk import paths

# 事件类型：前端可按 event 过滤、分组
EVENT_LOOP_START = "loop_start"
EVENT_ITERATION = "iteration"
EVENT_LLM_REQUEST = "llm_request"   # 发给大模型的完整 messages（截断后）
EVENT_LLM_RESPONSE = "llm_response"  # 大模型完整回复 content + tool_calls + usage
EVENT_TOOL_CALLS = "tool_calls"
EVENT_TOOL_RESULT = "tool_result"    # 含 result 全文（截断后）
EVENT_FINAL_REPLY = "final_reply"
EVENT_MAX_ITERATIONS = "max_iterations"
EVENT_LOOP_DONE = "loop_done"
EVENT_APPEND_TURN_DONE = "append_turn_done"

# 单条日志内字符串截断上限，避免单行过大
MAX_MSG_CONTENT_LEN = 8000
MAX_RESPONSE_CONTENT_LEN = 16000
MAX_TOOL_RESULT_LEN = 8000
MAX_MESSAGES_IN_LOG = 60

__all__ = [
    "log",
    "EVENT_LOOP_START",
    "EVENT_ITERATION",
    "EVENT_LLM_REQUEST",
    "EVENT_LLM_RESPONSE",
    "EVENT_TOOL_CALLS",
    "EVENT_TOOL_RESULT",
    "EVENT_FINAL_REPLY",
    "EVENT_MAX_ITERATIONS",
    "EVENT_LOOP_DONE",
    "EVENT_APPEND_TURN_DONE",
    "MAX_MSG_CONTENT_LEN",
    "MAX_RESPONSE_CONTENT_LEN",
    "MAX_TOOL_RESULT_LEN",
    "prepare_messages_for_log",
    "truncate_str",
]


def _log_path(employee_id: str) -> Path:
    return paths.get_employee_log_dir(employee_id) / "agent.jsonl"


def truncate_str(s: str, max_len: int) -> str:
    """截断字符串并标注是否被截断。"""
    if not s or len(s) <= max_len:
        return s
    return s[:max_len] + "\n...[truncated, total " + str(len(s)) + " chars]"


def prepare_messages_for_log(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    将发给大模型的 messages 转为可落盘的结构（每条 content 截断，限制条数），便于 debug。
    """
    out: list[dict[str, Any]] = []
    take = messages[-MAX_MESSAGES_IN_LOG:] if len(messages) > MAX_MESSAGES_IN_LOG else messages
    for m in take:
        entry: dict[str, Any] = {"role": m.get("role")}
        content = m.get("content")
        if content is not None:
            if isinstance(content, str):
                entry["content"] = truncate_str(content, MAX_MSG_CONTENT_LEN)
            else:
                entry["content"] = content
        if m.get("tool_calls"):
            entry["tool_calls"] = [
                {
                    "id": tc.get("id"),
                    "function": tc.get("function"),
                }
                for tc in (m.get("tool_calls") or [])[:20]
            ]
        if m.get("name"):
            entry["name"] = m["name"]
        out.append(entry)
    return out


def _serialize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """确保 payload 可 JSON 序列化（Path -> str 等）。"""
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if v is None or isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, Path):
            out[k] = str(v)
        elif isinstance(v, dict):
            out[k] = _serialize_payload(v)
        elif isinstance(v, list):
            out[k] = [
                _serialize_payload(x) if isinstance(x, dict) else str(x) if isinstance(x, Path) else x
                for x in v
            ]
        else:
            out[k] = str(v)
    return out


def log(
    employee_id: str,
    event: str,
    payload: dict[str, Any] | None = None,
    *,
    run_id: str | None = None,
) -> None:
    """
    追加一条结构化日志（一行 JSON）到该员工工作区的 agent.jsonl。
    前端可按 ts、event、run_id、employee_id 解析与筛选。

    payload 依 event 约定：
    - loop_start: session_key, channel, chat_id, history_len, user_message_preview
    - iteration: iteration, model, messages_count
    - tool_calls: iteration, tool_names[]
    - tool_result: tool_name, result_len
    - final_reply: reply_len
    - max_iterations: reason
    - loop_done: reply_len, usage { prompt_tokens, completion_tokens }
    - append_turn_done: (空)
    - llm_request: iteration, model, messages_count, messages (发给 API 的完整 messages，每条 content 截断)
    - llm_response: iteration, content (助理回复全文截断), tool_calls [{ name, arguments }], usage
    - tool_result: tool_name, result_len, result (工具返回全文截断)
    """
    log_dir = paths.get_employee_log_dir(employee_id)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        entry: dict[str, Any] = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "event": event,
            "employee_id": employee_id,
            "payload": _serialize_payload(payload or {}),
        }
        if run_id is not None:
            entry["run_id"] = run_id
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        with _log_path(employee_id).open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
