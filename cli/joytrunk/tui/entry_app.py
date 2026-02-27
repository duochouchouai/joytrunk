# -*- coding: utf-8 -*-
"""
对话入口 TUI：OpenClaw 风格框线（┌ │ ◇ ├ └ ─ ╮ ╯），员工列表或新建引导。
"""

from __future__ import annotations

import re
import webbrowser
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Input, OptionList, Static
from textual.widgets.option_list import Option

from joytrunk.api_client import (
    create_employee,
    ensure_owner_via_gateway,
    get_base_url,
    get_owner_id,
    list_employees,
)
from joytrunk.i18n import t
from joytrunk.tui.chat_app import ChatScreen
from joytrunk.tui.panel_style import build_entry_bottom, build_entry_message_block, PANEL_WIDTH


def _strip_markup(text: str) -> str:
    """去掉 Rich/Textual 标记如 [yellow]、[/]、[cyan] 等。"""
    return re.sub(r"\[/?[^\]]*\]", "", text)


class ChatEntryTuiApp(App[None]):
    """对话入口 TUI：显示本地员工列表或引导新建；选择/新建后进入对话。"""

    TITLE = "JoyTrunk"
    SUB_TITLE = ""

    CSS = """
    Screen {
        layout: vertical;
        align: left top;
        padding: 0;
        background: transparent;
    }

    Screen:inline {
        align: left top;
        padding: 0;
        background: transparent;
    }

    #entry-content {
        width: auto;
        min-width: 76;
        height: auto;
        min-height: 16;
        layout: vertical;
        padding: 0;
        margin: 0;
        align-horizontal: left;
        align-vertical: top;
        background: transparent;
    }

    #entry-panel-top {
        width: 100%;
        height: auto;
        padding: 0;
        margin: 0;
        background: transparent;
    }

    #entry-actions {
        width: 100%;
        height: auto;
        layout: horizontal;
        padding: 0 0 1 0;
    }

    #entry-actions > Button {
        margin-right: 1;
    }

    #entry-list-container {
        width: 100%;
        height: auto;
        min-height: 6;
        padding: 0 0 1 0;
    }

    #entry-list-container OptionList {
        width: 100%;
        height: auto;
        min-height: 6;
    }

    #entry-new-row {
        width: 100%;
        height: auto;
        layout: vertical;
        padding: 1 0 0 0;
    }

    #entry-panel-bottom {
        width: 100%;
        height: auto;
        padding: 0;
        margin: 0;
        background: transparent;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._owner_id: str | None = None
        self._employees: list[dict] = []
        self._state: str = "loading"  # loading | no_gateway | no_employees | list
        self._gateway_error: str | None = None
        self._show_new_input = False
        self._new_name_input: Input | None = None

    def compose(self) -> ComposeResult:
        with Container(id="entry-content"):
            yield Static("", id="entry-panel-top")
            yield Container(id="entry-actions")
            yield VerticalScroll(id="entry-list-container")
            yield Container(id="entry-new-row")
            yield Static("", id="entry-panel-bottom")

    def on_mount(self) -> None:
        self.call_later(self._refresh)

    def _focus_after_render(self) -> None:
        if self._state == "list":
            opt_list = self.query("#employee-option-list")
            if opt_list:
                opt_list.first().focus()
        elif self._state in ("no_gateway", "no_employees"):
            buttons = self.query("Button")
            if buttons:
                buttons.first().focus()

    def _refresh(self) -> None:
        self._gateway_error = None
        self._owner_id = ensure_owner_via_gateway()
        if self._owner_id is None:
            try:
                get_base_url()
            except Exception:
                pass
            self._state = "no_gateway"
            self._employees = []
            self._render()
            return
        self._owner_id = get_owner_id()
        if not self._owner_id:
            self._state = "no_gateway"
            self._employees = []
            self._render()
            return
        try:
            self._employees = list_employees(self._owner_id) or []
        except Exception as e:
            self._gateway_error = str(e)
            self._state = "no_gateway"
            self._employees = []
            self._render()
            return
        if not self._employees:
            self._state = "no_employees"
        else:
            self._state = "list"
        self._render()

    def _render(self) -> None:
        panel_top = self.query_one("#entry-panel-top", Static)
        panel_bottom = self.query_one("#entry-panel-bottom", Static)
        actions = self.query_one("#entry-actions", Container)
        list_container = self.query_one("#entry-list-container", VerticalScroll)
        new_row = self.query_one("#entry-new-row", Container)

        list_container.remove_children()
        actions.remove_children()
        new_row.remove_children()

        if self._state == "loading":
            header = "连接中"
            body = t("tui.entry.loading")
            panel_top.update(build_entry_message_block(header, body, width=PANEL_WIDTH))
            panel_bottom.update(build_entry_bottom(t("tui.lang_picker.hint")))
            self.call_later(self._focus_after_render)
            return

        if self._state == "no_gateway":
            header = "无法连接"
            raw = (
                t("chat.gateway_error", error=self._gateway_error or "连接失败", cmd="joytrunk gateway")
                + "\n\n"
                + t("tui.entry.open_then_refresh")
            )
            panel_top.update(build_entry_message_block(header, _strip_markup(raw), width=PANEL_WIDTH))
            panel_bottom.update(build_entry_bottom(t("tui.entry.open_admin") + "  ·  " + t("tui.entry.retry")))
            actions.mount(Button(t("tui.entry.open_admin"), id="btn-open"))
            actions.mount(Button(t("tui.entry.retry"), id="btn-retry"))
            self.call_later(self._focus_after_render)
            return

        if self._state == "no_employees":
            header = "无员工"
            raw = t("chat.no_employees") + "\n\n" + t("tui.entry.create_or_open")
            panel_top.update(build_entry_message_block(header, _strip_markup(raw), width=PANEL_WIDTH))
            panel_bottom.update(
                build_entry_bottom(t("tui.entry.new_employee") + "  ·  " + t("tui.entry.open_admin") + "  ·  " + t("tui.entry.retry"))
            )
            actions.mount(Button(t("tui.entry.new_employee"), id="btn-new"))
            actions.mount(Button(t("tui.entry.open_admin"), id="btn-open"))
            actions.mount(Button(t("tui.entry.retry"), id="btn-retry"))
            self.call_later(self._focus_after_render)
            return

        # list
        header = "选择员工"
        body = t("tui.entry.select_employee")
        panel_top.update(build_entry_message_block(header, body, width=PANEL_WIDTH))
        panel_bottom.update(build_entry_bottom(t("tui.entry.open_admin") + "  ·  " + t("tui.entry.retry")))
        opts = [Option(f"{e.get('name') or e['id']}  [dim]({e['id']})[/dim]", id=e["id"]) for e in self._employees]
        opt_list = OptionList(*opts)
        opt_list.id = "employee-option-list"
        list_container.mount(opt_list)
        actions.mount(Button(t("tui.entry.open_admin"), id="btn-open"))
        actions.mount(Button(t("tui.entry.retry"), id="btn-retry"))
        self.call_later(self._focus_after_render)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        opt = event.option
        oid = getattr(opt, "id", None)
        if not oid or self._state != "list" or not self._owner_id:
            return
        emp = next((e for e in self._employees if e["id"] == oid), None)
        if not emp:
            return
        name = emp.get("name") or emp["id"]
        self.push_screen(ChatScreen(employee_id=emp["id"], owner_id=self._owner_id, employee_name=name))

    def _show_new_employee_input(self) -> None:
        self._show_new_input = True
        new_row = self.query_one("#entry-new-row", Container)
        new_row.remove_children()
        self._new_name_input = Input(placeholder=t("tui.entry.new_employee_name"), id="new-employee-name")
        new_row.mount(Static(t("tui.entry.new_employee_prompt")))
        new_row.mount(self._new_name_input)
        new_row.mount(Button(t("tui.entry.create_btn"), id="btn-create-do"))
        new_row.mount(Button(t("tui.entry.cancel"), id="btn-create-cancel"))
        self._new_name_input.focus()

    def _do_create_employee(self, name: str) -> None:
        if not name.strip() or not self._owner_id:
            return
        try:
            created = create_employee(self._owner_id, name.strip())
        except Exception:
            return
        self._show_new_input = False
        self._new_name_input = None
        emp_id = created.get("id") or created["id"]
        emp_name = created.get("name") or emp_id
        self.push_screen(
            ChatScreen(employee_id=emp_id, owner_id=self._owner_id, employee_name=emp_name)
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-open":
            webbrowser.open(get_base_url())
        elif bid == "btn-retry":
            self._refresh()
        elif bid == "btn-new":
            self._show_new_employee_input()
        elif bid == "btn-create-do":
            if self._new_name_input:
                self._do_create_employee(self._new_name_input.value or "")
        elif bid == "btn-create-cancel":
            self._show_new_input = False
            inp = self.query("#new-employee-name")
            if inp:
                inp.first().remove()
            for w in self.query_one("#entry-new-row", Container).query(Button):
                w.remove()
            self._new_name_input = None
            self._refresh()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "new-employee-name":
            self._do_create_employee(event.input.value or "")
