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


def test_run_chat_entry_returns_none_when_no_server():
    """run_chat_entry 在无员工且用户取消选择时返回 None。"""
    from joytrunk.tui.clack_flows import run_chat_entry

    with patch("joytrunk.tui.clack_flows.intro"):
        with patch("joytrunk.tui.clack_flows.ensure_owner_id", return_value="owner-1"):
            with patch("joytrunk.tui.clack_flows.list_employees_from_config", return_value=[]):
                with patch("joytrunk.tui.clack_flows.select", return_value=None):
                    with patch("joytrunk.tui.clack_flows.is_cancel", return_value=True):
                        result = run_chat_entry()
    assert result is None


def test_run_chat_entry_returns_triple_when_employee_selected():
    """run_chat_entry 在用户选择员工时返回 (employee_id, owner_id, employee_name)。"""
    from joytrunk.tui.clack_flows import run_chat_entry

    with patch("joytrunk.tui.clack_flows.intro"):
        with patch("joytrunk.tui.clack_flows.ensure_owner_id", return_value="owner-1"):
            with patch(
                "joytrunk.tui.clack_flows.list_employees_from_config",
                return_value=[{"id": "emp-1", "name": "测试员工"}],
            ):
                with patch("joytrunk.tui.clack_flows.select", return_value="emp-1"):
                    with patch("joytrunk.tui.clack_flows.is_cancel", return_value=False):
                        result = run_chat_entry()
    assert result == ("emp-1", "owner-1", "测试员工")


def test_run_new_employee_returns_triple():
    """run_new_employee 在输入名称并创建成功时返回 (employee_id, owner_id, employee_name)。"""
    from joytrunk.tui.clack_flows import run_new_employee

    with patch("joytrunk.tui.clack_flows.intro"):
        with patch("joytrunk.tui.clack_flows.text", return_value="新员工A"):
            with patch("joytrunk.tui.clack_flows.is_cancel", return_value=False):
                with patch("joytrunk.tui.clack_flows.cancel"):
                    with patch(
                        "joytrunk.tui.clack_flows.create_employee_in_config",
                        return_value={"id": "emp-new", "name": "新员工A"},
                    ):
                        with patch("joytrunk.tui.clack_flows.log"):
                            result = run_new_employee("owner-1", skip_intro=False)
    assert result == ("emp-new", "owner-1", "新员工A")
