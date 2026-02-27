# -*- coding: utf-8 -*-
"""
互动式对话 TUI：可滚动对话区 + 底部输入框，后台 worker 调用员工智能体。
ChatScreen 可作为 Screen 被 push；ChatTuiApp 为独立运行时的入口。
"""

from __future__ import annotations

from typing import Any

from rich.markdown import Markdown
from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual.widgets import Input, RichLog, Static
from textual.worker import Worker, WorkerState

from joytrunk.agent.loop import run_employee_loop
from joytrunk.i18n import t

CHAT_CSS = """
#header {
    height: auto;
    padding: 0 1 0 1;
    background: $surface;
    border-bottom: solid $primary;
}

#messages-container {
    height: 1fr;
    overflow-y: auto;
    padding: 1 2;
    scrollbar-gutter: stable;
}

#messages {
    width: 100%;
    min-height: 100%;
}

#input-container {
    height: auto;
    padding: 0 1 1 1;
    border-top: solid $primary-darken-1;
    background: $surface;
}

#input {
    width: 100%;
}
"""


class ChatScreen(Screen[None]):
    """单员工对话界面：对话记录 + 输入框。可被 push_screen 使用。"""

    def __init__(
        self,
        employee_id: str,
        owner_id: str,
        employee_name: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.employee_id = employee_id
        self.owner_id = owner_id
        self.employee_name = employee_name

    def compose(self) -> ComposeResult:
        with Container(id="header"):
            yield Static(
                t("tui.chat_with", name=self.employee_name) + "  [dim]" + t("tui.hint") + "[/dim]  [dim]Esc 返回[/dim]",
                id="header-text",
            )
        with VerticalScroll(id="messages-container"):
            yield RichLog(id="messages", markup=True, highlight=True, auto_scroll=True)
        with Container(id="input-container"):
            yield Input(
                placeholder=t("tui.input_placeholder"),
                id="input",
            )

    def on_mount(self) -> None:
        self.query_one("#input", Input).focus()
        self.sub_title = self.employee_name

    def _append_user(self, text: str) -> None:
        log = self.query_one("#messages", RichLog)
        prefix = Text()
        prefix.append(t("chat.you") + " ", style="bold green")
        prefix.append(text)
        log.write(prefix)

    def _append_employee(self, text: str, usage: dict | None = None) -> None:
        log = self.query_one("#messages", RichLog)
        prefix = Text()
        prefix.append(t("chat.employee") + " ", style="bold blue")
        log.write(prefix)
        try:
            log.write(Markdown(text))
        except Exception:
            log.write(text)
        if usage and (usage.get("prompt_tokens") or usage.get("completion_tokens")):
            log.write(
                "[dim]"
                + t(
                    "chat.usage",
                    input=usage.get("prompt_tokens", 0),
                    output=usage.get("completion_tokens", 0),
                )
                + "[/dim]"
            )

    def _append_error(self, err: str) -> None:
        log = self.query_one("#messages", RichLog)
        log.write("[red]" + t("chat.send_failed", error=err) + "[/red]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = (event.value or "").strip()
        event.input.value = ""
        if not value:
            return
        if value.lower() in ("/exit", "/quit", "exit", "quit"):
            self.app.pop_screen()
            return
        self._append_user(value)
        self._send_message(value)

    @work(exclusive=True, exit_on_error=False)
    async def _send_message(self, text: str) -> tuple[str | None, dict | None, str | None]:
        try:
            reply, usage = await run_employee_loop(
                self.employee_id,
                self.owner_id,
                text,
                session_key="cli:direct",
                on_progress=None,
            )
            return (reply, usage, None)
        except Exception as e:  # noqa: BLE001
            return (None, None, str(e))

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        worker = event.worker
        if worker.state == WorkerState.SUCCESS:
            result = worker.result
            if result and isinstance(result, (list, tuple)) and len(result) == 3:
                reply, usage, err = result
                if err:
                    self._append_error(err)
                elif reply is not None:
                    self._append_employee(reply, usage)
        elif worker.state == WorkerState.ERROR and worker.error:
            self._append_error(str(worker.error))

    def on_key(self, event):
        if event.key == "escape":
            self.app.pop_screen()
            return
        return super().on_key(event)


class ChatTuiApp(App[None]):
    """独立运行时的对话 TUI：仅包含 ChatScreen。"""

    TITLE = "JoyTrunk"
    SUB_TITLE = ""
    CSS = "Screen { layout: vertical; }\n" + CHAT_CSS

    def __init__(
        self,
        employee_id: str,
        owner_id: str,
        employee_name: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.employee_id = employee_id
        self.owner_id = owner_id
        self.employee_name = employee_name

    def compose(self) -> ComposeResult:
        yield ChatScreen(
            employee_id=self.employee_id,
            owner_id=self.owner_id,
            employee_name=self.employee_name,
        )
