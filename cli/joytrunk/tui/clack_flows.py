# -*- coding: utf-8 -*-
"""
基于 python-clack 的 TUI 流程：joytrunk language（语言选择）、joytrunk chat（员工选择/新建与对话循环）。
满足 agent.md §4.8：列表选择、↑↓ 移动、Enter 确定。
"""

from __future__ import annotations

import asyncio
import webbrowser

from python_clack import cancel, intro, is_cancel, log, outro, select, spinner, text

from joytrunk.config_store import (
    create_employee_in_config,
    ensure_owner_id,
    list_employees_from_config,
)
from joytrunk.i18n import t
from joytrunk.agent.loop import run_employee_loop


# 语言选项（value, label）
LANG_OPTIONS = [
    {"value": "zh", "label": "中文 (zh)"},
    {"value": "en", "label": "English (en)"},
]


def run_language_picker() -> str | None:
    """
    使用 python-clack 选择 CLI 语言。
    返回 "zh" | "en"，取消则返回 None。
    """
    intro(t("tui.lang_picker.title"))
    result = select(
        t("tui.lang_picker.hint"),
        options=LANG_OPTIONS,
    )
    if is_cancel(result):
        cancel(t("tui.lang_picker.cancelled"))
        return None
    return result


def run_new_employee(owner_id: str, skip_intro: bool = False) -> tuple[str, str, str] | None:
    """
    新建员工流程（供 chat 与 employee 命令共用）。
    使用 config_store 写入 config.json，不连接 gateway。
    使用 python-clack：text() 输入名称，create_employee_in_config 后返回 (employee_id, owner_id, employee_name)。
    取消或失败返回 None。skip_intro=True 时省略 intro（用于从 chat 入口进入时）。
    """
    if not skip_intro:
        intro(t("employee.new.title"))
    name_val = text(
        t("tui.entry.new_employee_prompt"),
        placeholder=t("tui.entry.new_employee_name"),
    )
    if is_cancel(name_val):
        cancel(t("tui.lang_picker.cancelled"))
        return None
    name = (name_val or "").strip() or "新员工"
    try:
        created = create_employee_in_config(owner_id, name)
        emp_id = created.get("id") or created["id"]
        emp_name = created.get("name") or emp_id
        if not skip_intro:
            log.success(t("employee.created", name=emp_name, id=emp_id))
        return (emp_id, owner_id, emp_name)
    except Exception as e:
        log.error(t("employee.create_failed", error=str(e)))
        return None


def run_chat_entry() -> tuple[str, str, str] | None:
    """
    使用 python-clack 完成 chat 入口：从 config.json 读取员工，不连接 gateway。
    选择或新建员工。返回 (employee_id, owner_id, employee_name)，取消或失败返回 None。
    """
    intro("JoyTrunk")
    owner_id = ensure_owner_id()
    employees = list_employees_from_config(owner_id) or []

    while True:
        if not employees:
            choice = select(
                t("tui.entry.select_employee"),
                options=[
                    {"value": "new", "label": t("tui.entry.new_employee")},
                    {"value": "open", "label": t("tui.entry.open_admin")},
                ],
            )
            if is_cancel(choice):
                return None
            if choice == "open":
                from joytrunk.api_client import get_base_url
                webbrowser.open(get_base_url())
                continue
            triple = run_new_employee(owner_id, skip_intro=True)
            if triple:
                return triple
            continue

        # 有员工列表：选项 = 员工 + 最后一项「新建员工」+ 可选「打开管理页」
        options = [
            {"value": e["id"], "label": f"{e.get('name') or e['id']}  ({e['id']})"}
            for e in employees
        ]
        options.append({"value": "__new__", "label": t("tui.entry.new_employee")})
        options.append({"value": "__open__", "label": t("tui.entry.open_admin")})

        choice = select(t("tui.entry.select_employee"), options=options)
        if is_cancel(choice):
            return None
        if choice == "__open__":
            from joytrunk.api_client import get_base_url
            webbrowser.open(get_base_url())
            continue
        if choice == "__new__":
            triple = run_new_employee(owner_id, skip_intro=True)
            if triple:
                return triple
            employees = list_employees_from_config(owner_id) or []
            continue
        emp = next((e for e in employees if e["id"] == choice), None)
        if emp:
            return (choice, owner_id, emp.get("name") or choice)
        return None


def run_employee_menu(owner_id: str) -> None:
    """
    员工管理 TUI 菜单（joytrunk employee 无子命令时）：列出员工 / 新建员工 / 退出。
    从 config.json 读取，不连接 gateway。
    """
    while True:
        intro(t("employee.menu.title"))
        choice = select(
            t("employee.menu.prompt"),
            options=[
                {"value": "list", "label": t("employee.menu.list")},
                {"value": "new", "label": t("employee.menu.new")},
                {"value": "exit", "label": t("employee.menu.exit")},
            ],
        )
        if is_cancel(choice):
            cancel(t("tui.lang_picker.cancelled"))
            return
        if choice == "exit":
            outro(t("employee.menu.exit"))
            return
        if choice == "list":
            employees = list_employees_from_config(owner_id) or []
            if not employees:
                log.warn(t("chat.no_employees"))
                continue
            options = [
                {"value": e["id"], "label": f"{e.get('name') or e['id']}  ({e['id']})"}
                for e in employees
            ]
            options.append({"value": "__back__", "label": t("employee.menu.back")})
            selected = select(t("employee.menu.select_to_chat"), options=options)
            if is_cancel(selected):
                continue
            if selected == "__back__":
                continue
            emp = next((e for e in employees if e["id"] == selected), None)
            if emp:
                run_chat_loop(selected, owner_id, emp.get("name") or selected)
            continue
        if choice == "new":
            run_new_employee(owner_id, skip_intro=False)
            continue


def run_memory_export_flow(owner_id: str) -> None:
    """
    记忆导出 TUI：选择员工 → 可选输入输出路径 → 执行导出。
    取消或失败时 return。
    """
    intro(t("memory.tui.title"))
    employees = list_employees_from_config(owner_id) or []
    if not employees:
        log.warn(t("chat.no_employees"))
        return
    options = [
        {"value": e["id"], "label": f"{e.get('name') or e['id']}  ({e['id']})"}
        for e in employees
    ]
    options.append({"value": "__back__", "label": t("employee.menu.back")})
    choice = select(t("memory.tui.select_employee"), options=options)
    if is_cancel(choice) or choice == "__back__":
        cancel(t("tui.lang_picker.cancelled"))
        return
    emp = next((e for e in employees if e["id"] == choice), None)
    if not emp:
        return
    employee_id = choice
    out_prompt = t("memory.tui.output_prompt")
    out_val = text(out_prompt, placeholder=t("memory.tui.output_placeholder"))
    if is_cancel(out_val):
        cancel(t("tui.lang_picker.cancelled"))
        return
    output_path = (out_val or "").strip() or None
    if output_path:
        from pathlib import Path
        output_path = Path(output_path).resolve()
    try:
        from joytrunk.agent.memory.export_md import export_memory_to_md
        out_path = export_memory_to_md(employee_id, output_path=output_path)
        log.success(t("memory.export_done", path=str(out_path)))
    except Exception as e:
        log.error(t("memory.export_failed", error=str(e)))


def run_chat_loop(employee_id: str, owner_id: str, employee_name: str) -> None:
    """
    使用 python-clack 的对话循环：intro 后循环 text() 输入，调用 run_employee_loop，用 log 输出回复与用量。
    输入 /exit 或取消时 outro 并退出。
    """
    intro(t("tui.chat_with", name=employee_name))
    log.info(t("tui.hint"))
    while True:
        msg = text(
            t("chat.you"),
            placeholder=t("tui.input_placeholder"),
        )
        if is_cancel(msg):
            cancel(t("tui.lang_picker.cancelled"))
            return
        raw = (msg or "").strip()
        if not raw:
            continue
        if raw.lower() in ("/exit", "/quit", "exit", "quit"):
            outro(t("tui.lang_picker.cancelled"))
            return
        s = None
        try:
            s = spinner()
            s.start(t("tui.entry.loading"))
            reply, usage = asyncio.run(
                run_employee_loop(
                    employee_id,
                    owner_id,
                    raw,
                    session_key="cli:direct",
                    on_progress=None,
                )
            )
            s.stop("")
            log.success(t("chat.employee") + " " + (reply or ""))
            if usage and (usage.get("prompt_tokens") or usage.get("completion_tokens")):
                log.info(
                    t("chat.usage", input=usage.get("prompt_tokens", 0), output=usage.get("completion_tokens", 0))
                )
        except Exception as e:
            if s is not None:
                try:
                    s.error(str(e))
                except Exception:
                    pass
            log.error(t("chat.send_failed", error=str(e)))
