# -*- coding: utf-8 -*-
"""
语言选择 TUI：OpenClaw 风格框线（┌ │ ◇ ├ └ ─ ╮ ╯），○/● 选项，↑↓ 移动、Enter 确定。
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static

from joytrunk.i18n import t
from joytrunk.tui.panel_style import LANG_OPTIONS, build_language_screen, PANEL_WIDTH


class LanguagePickerApp(App[str | None]):
    """独立运行的语言选择 TUI，run() 返回 zh 或 en（Esc 返回 None）。"""

    TITLE = "JoyTrunk"
    SUB_TITLE = ""

    BINDINGS = [
        Binding("up", "cursor_up", "↑", show=False),
        Binding("down", "cursor_down", "↓", show=False),
        Binding("enter", "confirm", "Enter", show=False),
        Binding("escape", "exit_none", "Esc", show=False),
    ]

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

    #lang-panel {
        width: auto;
        min-width: 74;
        height: auto;
        padding: 0;
        margin: 0;
        align-horizontal: left;
        align-vertical: top;
        background: transparent;
    }

    #lang-content {
        width: auto;
        height: auto;
        padding: 0;
        margin: 0;
        color: $text;
        background: transparent;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._selected_index = 0

    def compose(self) -> ComposeResult:
        with Container(id="lang-panel"):
            yield Static("", id="lang-content")

    def on_mount(self) -> None:
        self._update_content()

    def _update_content(self) -> None:
        title = t("tui.lang_picker.title")
        hint = t("tui.lang_picker.hint")
        text = build_language_screen(self._selected_index, title, hint, width=PANEL_WIDTH)
        self.query_one("#lang-content", Static).update(text)

    def action_cursor_up(self) -> None:
        self._selected_index = max(0, self._selected_index - 1)
        self._update_content()

    def action_cursor_down(self) -> None:
        self._selected_index = min(len(LANG_OPTIONS) - 1, self._selected_index + 1)
        self._update_content()

    def action_confirm(self) -> None:
        code = LANG_OPTIONS[self._selected_index][0]
        self.exit(code)

    def action_exit_none(self) -> None:
        self.exit(None)
