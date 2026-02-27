# -*- coding: utf-8 -*-
"""
基于 python-clack 的 TUI 流程：joytrunk language（语言选择）、joytrunk chat（员工选择/新建）。
满足 agent.md §4.8：列表选择、↑↓ 移动、Enter 确定。
"""

from __future__ import annotations

import webbrowser

from python_clack import cancel, intro, is_cancel, outro, select, text

from joytrunk.api_client import (
    create_employee,
    ensure_owner_via_gateway,
    get_base_url,
    get_owner_id,
    list_employees,
)
from joytrunk.i18n import t


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


def run_chat_entry() -> tuple[str, str, str] | None:
    """
    使用 python-clack 完成 chat 入口：连接 gateway、选择或新建员工。
    返回 (employee_id, owner_id, employee_name)，取消或失败返回 None。
    """
    intro("JoyTrunk")
    owner_id = ensure_owner_via_gateway()
    if not owner_id:
        try:
            get_base_url()
        except Exception:
            pass
        outro(t("chat.gateway_error", error="连接失败", cmd="joytrunk gateway"))
        return None
    owner_id = get_owner_id() or owner_id
    try:
        employees = list_employees(owner_id) or []
    except Exception as e:
        outro(t("chat.gateway_error", error=str(e), cmd="joytrunk gateway"))
        return None

    while True:
        if not employees:
            choice = select(
                t("tui.entry.select_employee"),
                options=[
                    {"value": "new", "label": t("tui.entry.new_employee")},
                    {"value": "open", "label": t("tui.entry.open_admin")},
                    {"value": "retry", "label": t("tui.entry.retry")},
                ],
            )
            if is_cancel(choice):
                return None
            if choice == "open":
                webbrowser.open(get_base_url())
                continue
            if choice == "retry":
                owner_id = ensure_owner_via_gateway()
                if owner_id:
                    try:
                        employees = list_employees(owner_id) or []
                    except Exception:
                        pass
                continue
            # new
            name_val = text(
                t("tui.entry.new_employee_prompt"),
                placeholder=t("tui.entry.new_employee_name"),
            )
            if is_cancel(name_val):
                return None
            name = (name_val or "").strip() or "新员工"
            try:
                created = create_employee(owner_id, name)
                emp_id = created.get("id") or created["id"]
                emp_name = created.get("name") or emp_id
                return (emp_id, owner_id, emp_name)
            except Exception:
                outro(t("chat.gateway_error", error="创建失败", cmd="joytrunk gateway"))
                return None

        # 有员工列表：选项 = 员工 + 可选「新建」「打开管理页」「重试」
        options = [
            {"value": e["id"], "label": f"{e.get('name') or e['id']}  ({e['id']})"}
            for e in employees
        ]
        options.append({"value": "__new__", "label": t("tui.entry.new_employee")})
        options.append({"value": "__open__", "label": t("tui.entry.open_admin")})
        options.append({"value": "__retry__", "label": t("tui.entry.retry")})

        choice = select(t("tui.entry.select_employee"), options=options)
        if is_cancel(choice):
            return None
        if choice == "__open__":
            webbrowser.open(get_base_url())
            continue
        if choice == "__retry__":
            owner_id = ensure_owner_via_gateway()
            if owner_id:
                try:
                    employees = list_employees(owner_id) or []
                except Exception:
                    pass
            continue
        if choice == "__new__":
            name_val = text(
                t("tui.entry.new_employee_prompt"),
                placeholder=t("tui.entry.new_employee_name"),
            )
            if is_cancel(name_val):
                continue
            name = (name_val or "").strip() or "新员工"
            try:
                created = create_employee(owner_id, name)
                emp_id = created.get("id") or created["id"]
                emp_name = created.get("name") or emp_id
                return (emp_id, owner_id, emp_name)
            except Exception:
                outro(t("chat.gateway_error", error="创建失败", cmd="joytrunk gateway"))
                continue
        # choice is employee id
        emp = next((e for e in employees if e["id"] == choice), None)
        if emp:
            return (choice, owner_id, emp.get("name") or choice)
        return None
