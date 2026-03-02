"""员工运行日志读取与清理：解析 agent.jsonl，供 TUI 与 CLI 使用。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from joytrunk import paths


def get_log_path(employee_id: str) -> Path:
    """该员工 agent 运行日志文件路径。"""
    return paths.get_employee_log_dir(employee_id) / "agent.jsonl"


def load_entries(
    employee_id: str,
    *,
    sort_newest_first: bool = True,
    event_filter: str | None = None,
    run_id_filter: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    读取该员工的 agent.jsonl，返回解析后的条目列表。
    sort_newest_first: True 则按 ts 倒序（最新在前）。
    event_filter: 仅保留 event 等于该值的条目。
    run_id_filter: 仅保留 run_id 等于该值的条目。
    limit: 最多返回条数，None 表示全部。
    """
    log_path = get_log_path(employee_id)
    if not log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    try:
        with log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if not isinstance(entry, dict):
                        continue
                    if event_filter is not None and entry.get("event") != event_filter:
                        continue
                    if run_id_filter is not None and entry.get("run_id") != run_id_filter:
                        continue
                    entries.append(entry)
                except (json.JSONDecodeError, TypeError):
                    continue
    except OSError:
        return []
    if sort_newest_first:
        entries.sort(key=lambda e: e.get("ts") or "", reverse=True)
    if limit is not None and limit > 0:
        entries = entries[:limit]
    return entries


def get_run_ids(employee_id: str, limit: int = 100) -> list[str]:
    """去重、按出现顺序返回最近的 run_id 列表（文件末尾的 run 在先）。"""
    log_path = get_log_path(employee_id)
    if not log_path.exists():
        return []
    seen: set[str] = set()
    result: list[str] = []
    try:
        with log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    rid = entry.get("run_id") if isinstance(entry, dict) else None
                    if rid and isinstance(rid, str) and rid not in seen:
                        seen.add(rid)
                        result.append(rid)
                        if len(result) >= limit:
                            break
                except (json.JSONDecodeError, TypeError):
                    continue
    except OSError:
        return []
    result.reverse()
    return result


def clear_log(employee_id: str) -> bool:
    """清空该员工的 agent.jsonl（截断为 0 字节）。成功返回 True。"""
    log_path = get_log_path(employee_id)
    if not log_path.exists():
        return True
    try:
        log_path.write_text("", encoding="utf-8")
        return True
    except OSError:
        return False
