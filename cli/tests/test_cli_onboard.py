# -*- coding: utf-8 -*-
"""测试 joytrunk onboard 命令：无语言配置时提示选择并写入，有配置时直接 onboard。"""

from pathlib import Path
from unittest.mock import patch

import pytest


def test_onboard_cmd_prompts_language_when_no_config(joytrunk_root):
    """当 has_language_config() 为 False 时，调用 run_language_picker，选择后传入 run_onboard(initial_locale=...)。"""
    from joytrunk.cli import onboard_cmd
    from joytrunk.i18n import reset_locale_cache

    reset_locale_cache()
    with patch("joytrunk.cli.has_language_config", return_value=False) as m_has:
        with patch("joytrunk.tui.clack_flows.run_language_picker", return_value="en") as m_picker:
            with patch("joytrunk.onboard.run_onboard", return_value=Path(joytrunk_root)) as m_onboard:
                onboard_cmd()
    m_has.assert_called_once()
    m_picker.assert_called_once()
    m_onboard.assert_called_once_with(initial_locale="en")


def test_onboard_cmd_no_prompt_when_has_language_config(joytrunk_root):
    """当 has_language_config() 为 True 时，不提示输入，run_onboard(initial_locale=None)。"""
    (joytrunk_root / "config.json").write_text('{"cli": {"locale": "zh"}}', encoding="utf-8")
    from joytrunk.cli import onboard_cmd
    from joytrunk.i18n import reset_locale_cache

    reset_locale_cache()
    with patch("joytrunk.cli.has_language_config", return_value=True) as m_has:
        with patch("joytrunk.onboard.run_onboard", return_value=Path(joytrunk_root)) as m_onboard:
            onboard_cmd()
    m_has.assert_called_once()
    m_onboard.assert_called_once_with(initial_locale=None)


def test_onboard_cmd_invalid_input_defaults_to_zh(joytrunk_root):
    """run_language_picker 返回非 zh/en 或 None 时使用默认 zh。"""
    from joytrunk.cli import onboard_cmd
    from joytrunk.i18n import reset_locale_cache

    reset_locale_cache()
    with patch("joytrunk.cli.has_language_config", return_value=False):
        with patch("joytrunk.tui.clack_flows.run_language_picker", return_value=None):
            with patch("joytrunk.onboard.run_onboard", return_value=Path(joytrunk_root)) as m_onboard:
                onboard_cmd()
    m_onboard.assert_called_once_with(initial_locale="zh")
