# -*- coding: utf-8 -*-
"""测试 joytrunk.i18n：get_locale、set_locale、t、reset_locale_cache、locale_display_name。"""

import json
from unittest.mock import patch

import pytest

from joytrunk.i18n import (
    get_locale,
    has_language_config,
    locale_display_name,
    reset_locale_cache,
    set_locale,
    t,
)


@pytest.fixture(autouse=True)
def clear_locale_cache():
    """每个测试后清缓存，避免影响其他测试。"""
    yield
    reset_locale_cache()


def test_get_locale_default_when_no_config(joytrunk_root):
    """无 config 时返回默认 zh。"""
    assert get_locale() == "zh"


def test_get_locale_from_config(joytrunk_root):
    """从 config.cli.locale 读取。"""
    config_path = joytrunk_root / "config.json"
    config_path.write_text('{"cli": {"locale": "en"}}', encoding="utf-8")
    reset_locale_cache()
    assert get_locale() == "en"


def test_get_locale_env_overrides(joytrunk_root, monkeypatch):
    """环境变量 JOYTRUNK_LANG 优先于 config。"""
    (joytrunk_root / "config.json").write_text('{"cli": {"locale": "zh"}}', encoding="utf-8")
    reset_locale_cache()
    monkeypatch.setenv("JOYTRUNK_LANG", "en")
    assert get_locale() == "en"
    monkeypatch.setenv("JOYTRUNK_LANG", "zh")
    reset_locale_cache()
    assert get_locale() == "zh"


def test_set_locale_writes_config(joytrunk_root):
    """set_locale 写入 config 并返回合法 locale。"""
    (joytrunk_root / "config.json").write_text("{}", encoding="utf-8")
    reset_locale_cache()
    out = set_locale("en")
    assert out == "en"
    data = json.loads((joytrunk_root / "config.json").read_text(encoding="utf-8"))
    assert (data.get("cli") or {}).get("locale") == "en"


def test_set_locale_invalid_falls_back_to_zh(joytrunk_root):
    """无效 locale 时使用默认 zh。"""
    joytrunk_root.mkdir(parents=True, exist_ok=True)
    out = set_locale("fr")
    assert out == "zh"
    data = json.loads((joytrunk_root / "config.json").read_text(encoding="utf-8"))
    assert (data.get("cli") or {}).get("locale") == "zh"


def test_t_returns_translation(joytrunk_root):
    """t(key) 按当前 locale 返回文案。"""
    (joytrunk_root / "config.json").write_text('{"cli": {"locale": "zh"}}', encoding="utf-8")
    reset_locale_cache()
    assert "工作区" in t("onboard.ready") or "就绪" in t("onboard.ready")
    set_locale("en")
    assert "ready" in t("onboard.ready").lower()


def test_t_interpolation(joytrunk_root):
    """t(key, **kwargs) 支持占位符插值。"""
    (joytrunk_root / "config.json").write_text('{"cli": {"locale": "zh"}}', encoding="utf-8")
    reset_locale_cache()
    s = t("onboard.root", path="/tmp/joytrunk")
    assert "/tmp/joytrunk" in s


def test_t_unknown_key_returns_key_or_default(joytrunk_root):
    """未知 key 时返回默认语言文案或 key。"""
    reset_locale_cache()
    s = t("nonexistent.key")
    assert s == "nonexistent.key" or "nonexistent" in s


def test_reset_locale_cache(joytrunk_root):
    """reset 后 get_locale 重新读 config。"""
    (joytrunk_root / "config.json").write_text('{"cli": {"locale": "en"}}', encoding="utf-8")
    reset_locale_cache()
    assert get_locale() == "en"
    (joytrunk_root / "config.json").write_text('{"cli": {"locale": "zh"}}', encoding="utf-8")
    assert get_locale() == "en"  # 仍缓存
    reset_locale_cache()
    assert get_locale() == "zh"


def test_locale_display_name():
    """locale_display_name 返回中文/English。"""
    assert locale_display_name("zh") == "中文"
    assert locale_display_name("en") == "English"


def test_has_language_config_no_config(joytrunk_root):
    """无 config 时 has_language_config 为 False。"""
    assert has_language_config() is False
