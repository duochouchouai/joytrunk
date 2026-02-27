# -*- coding: utf-8 -*-
"""测试 python-clack 流程：run_language_picker、run_chat_entry。"""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_i18n(joytrunk_root):
    from joytrunk.i18n import reset_locale_cache
    (joytrunk_root / "config.json").write_text('{"cli": {"locale": "zh"}}', encoding="utf-8")
    reset_locale_cache()
    yield


def test_run_language_picker_returns_zh():
    """run_language_picker 在用户选择 zh 时返回 'zh'。"""
    from joytrunk.tui.clack_flows import run_language_picker

    with patch("joytrunk.tui.clack_flows.intro"):
        with patch("joytrunk.tui.clack_flows.select", return_value="zh"):
            with patch("joytrunk.tui.clack_flows.is_cancel", return_value=False):
                with patch("joytrunk.tui.clack_flows.cancel"):
                    result = run_language_picker()
    assert result == "zh"


def test_run_language_picker_returns_none_on_cancel():
    """run_language_picker 在用户取消时返回 None。"""
    from joytrunk.tui.clack_flows import run_language_picker

    with patch("joytrunk.tui.clack_flows.intro"):
        with patch("joytrunk.tui.clack_flows.select", return_value=None):
            with patch("joytrunk.tui.clack_flows.is_cancel", return_value=True):
                with patch("joytrunk.tui.clack_flows.cancel"):
                    result = run_language_picker()
    assert result is None


def test_run_chat_entry_returns_none_when_no_gateway():
    """run_chat_entry 在 ensure_owner_via_gateway 返回 None 时返回 None。"""
    from joytrunk.tui.clack_flows import run_chat_entry

    with patch("joytrunk.tui.clack_flows.intro"):
        with patch("joytrunk.tui.clack_flows.outro"):
            with patch("joytrunk.tui.clack_flows.ensure_owner_via_gateway", return_value=None):
                with patch("joytrunk.tui.clack_flows.get_base_url", side_effect=Exception()):
                    result = run_chat_entry()
    assert result is None


def test_run_chat_entry_returns_triple_when_employee_selected():
    """run_chat_entry 在用户选择员工时返回 (employee_id, owner_id, employee_name)。"""
    from joytrunk.tui.clack_flows import run_chat_entry

    with patch("joytrunk.tui.clack_flows.intro"):
        with patch("joytrunk.tui.clack_flows.ensure_owner_via_gateway", return_value="owner-1"):
            with patch("joytrunk.tui.clack_flows.get_owner_id", return_value="owner-1"):
                with patch(
                    "joytrunk.tui.clack_flows.list_employees",
                    return_value=[{"id": "emp-1", "name": "测试员工"}],
                ):
                    with patch("joytrunk.tui.clack_flows.select", return_value="emp-1"):
                        with patch("joytrunk.tui.clack_flows.is_cancel", return_value=False):
                            result = run_chat_entry()
    assert result == ("emp-1", "owner-1", "测试员工")
