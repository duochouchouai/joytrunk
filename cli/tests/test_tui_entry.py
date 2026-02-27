# -*- coding: utf-8 -*-
"""
对话入口 TUI 界面测试：确保不黑屏，各状态（无网关/无员工/员工列表）有可见内容。
使用 Textual run_test() + Pilot，mock API 控制状态。
"""

from unittest.mock import patch

import pytest

from textual.widgets import Static

from joytrunk.tui.entry_app import ChatEntryTuiApp


def _panel_text(app, node_id: str = "#entry-panel-top"):
    """获取入口面板 Static 的可见文案，用于断言非空、避免黑屏。"""
    w = app.query_one(node_id, Static)
    r = getattr(w, "renderable", None)
    if r is None:
        return ""
    if hasattr(r, "plain"):
        return r.plain
    return str(r)


@pytest.fixture(autouse=True)
def _reset_i18n(joytrunk_root):
    """确保测试使用一致语言与配置。"""
    from joytrunk.i18n import reset_locale_cache

    (joytrunk_root / "config.json").write_text('{"cli": {"locale": "zh"}}', encoding="utf-8")
    reset_locale_cache()
    yield


async def test_entry_tui_has_visible_content_no_gateway():
    """无网关时：界面有 #entry-content、#entry-panel-top 非空、且有「打开管理页」「重试」按钮，避免黑屏。"""
    with patch("joytrunk.tui.entry_app.ensure_owner_via_gateway", return_value=None):
        with patch("joytrunk.tui.entry_app.get_base_url", side_effect=Exception("no gateway")):
            app = ChatEntryTuiApp()
            async with app.run_test() as pilot:
                await pilot.pause(delay=0.15)
                content = app.query_one("#entry-content")
                assert content is not None
                text = _panel_text(app)
                assert text
                buttons = app.query("Button")
                assert len(buttons) >= 2
                button_labels = [getattr(b.label, "plain", str(b.label)) for b in buttons]
                combined = "".join(button_labels)
                assert "打开管理页" in combined or "重试" in combined


async def test_entry_tui_has_visible_content_no_employees():
    """无员工时：有「新建员工」「打开管理页」「重试」等可见内容，避免黑屏。"""
    with patch("joytrunk.tui.entry_app.ensure_owner_via_gateway", return_value="owner-1"):
        with patch("joytrunk.tui.entry_app.get_owner_id", return_value="owner-1"):
            with patch("joytrunk.tui.entry_app.list_employees", return_value=[]):
                app = ChatEntryTuiApp()
                async with app.run_test() as pilot:
                    await pilot.pause(delay=0.15)
                    content = app.query_one("#entry-content")
                    assert content is not None
                    text = _panel_text(app)
                    assert text
                    buttons = app.query("Button")
                    assert len(buttons) >= 3
                    button_labels = [getattr(b.label, "plain", str(b.label)) for b in buttons]
                    combined = "".join(button_labels)
                    assert "新建员工" in combined


async def test_entry_tui_has_visible_content_employee_list():
    """有员工列表时：有 OptionList 与选项、且有「打开管理页」「重试」，避免黑屏。"""
    with patch("joytrunk.tui.entry_app.ensure_owner_via_gateway", return_value="owner-1"):
        with patch("joytrunk.tui.entry_app.get_owner_id", return_value="owner-1"):
            with patch(
                "joytrunk.tui.entry_app.list_employees",
                return_value=[{"id": "emp-1", "name": "测试员工"}],
            ):
                app = ChatEntryTuiApp()
                async with app.run_test() as pilot:
                    await pilot.pause(delay=0.15)
                    content = app.query_one("#entry-content")
                    assert content is not None
                    text = _panel_text(app)
                    assert "选择员工" in text or "select" in text.lower()
                    opt_list = app.query("#employee-option-list")
                    assert len(opt_list) == 1
                    buttons = app.query("Button")
                    assert len(buttons) >= 2


async def test_entry_tui_initial_shows_loading():
    """启动首帧应有「正在连接…」等 loading 文案，随后被 _refresh 结果替换。"""
    with patch("joytrunk.tui.entry_app.ensure_owner_via_gateway", return_value=None):
        app = ChatEntryTuiApp()
        async with app.run_test() as pilot:
            await pilot.pause(delay=0.05)
            panel = app.query_one("#entry-panel-top", Static)
            assert panel is not None
            text = _panel_text(app)
            assert "正在连接" in text or "连接" in text or "gateway" in text.lower() or "joytrunk" in text.lower()
