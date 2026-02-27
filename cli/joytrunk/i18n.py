# -*- coding: utf-8 -*-
"""
CLI 多语言（i18n）：根据 config.cli.locale 或环境变量 JOYTRUNK_LANG 返回对应文案。

用法:
  from joytrunk.i18n import t, get_locale, set_locale
  print(t("onboard.ready"))
  print(t("status.root", path="/tmp"))
"""

from __future__ import annotations

import json
import os
from typing import Any

from joytrunk import paths
from joytrunk.config_schema import migrate_from_legacy
from joytrunk.locales import DEFAULT_LOCALE, SUPPORTED, TRANSLATIONS

_CACHE: str | None = None


def get_locale() -> str:
    """当前 CLI 语言：zh 或 en。优先环境变量 JOYTRUNK_LANG，其次 config.json 的 cli.locale。"""
    global _CACHE
    env = os.environ.get("JOYTRUNK_LANG", "").strip().lower()
    if env in SUPPORTED:
        return env
    if _CACHE is not None:
        return _CACHE
    p = paths.get_config_path()
    if not p.exists():
        _CACHE = DEFAULT_LOCALE
        return _CACHE
    try:
        data = migrate_from_legacy(json.loads(p.read_text(encoding="utf-8")))
        loc = (data.get("cli") or {}).get("locale") or DEFAULT_LOCALE
        if loc not in SUPPORTED:
            loc = DEFAULT_LOCALE
        _CACHE = loc
        return _CACHE
    except Exception:
        _CACHE = DEFAULT_LOCALE
        return _CACHE


def set_locale(locale: str) -> str:
    """设置当前语言并写回 config.json，返回实际使用的 locale。"""
    global _CACHE
    locale = (locale or "").strip().lower()
    if locale not in SUPPORTED:
        locale = DEFAULT_LOCALE
    _CACHE = locale
    p = paths.get_config_path()
    root = paths.get_joytrunk_root()
    root.mkdir(parents=True, exist_ok=True)
    if p.exists():
        data = migrate_from_legacy(json.loads(p.read_text(encoding="utf-8")))
    else:
        data = migrate_from_legacy({})
    if "cli" not in data or not isinstance(data["cli"], dict):
        data["cli"] = {}
    data["cli"]["locale"] = locale
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return locale


def t(key: str, **kwargs: Any) -> str:
    """根据当前语言返回文案；支持 {placeholder} 插值。"""
    loc = get_locale()
    messages = TRANSLATIONS.get(loc) or TRANSLATIONS[DEFAULT_LOCALE]
    msg = messages.get(key)
    if msg is None:
        msg = TRANSLATIONS[DEFAULT_LOCALE].get(key) or key
    if kwargs:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg
    return msg


def locale_display_name(code: str) -> str:
    """语言代码的显示名。"""
    return "中文" if code == "zh" else "English"


def reset_locale_cache() -> None:
    """清除语言缓存，下次 get_locale() 会重新从 config 读取。"""
    global _CACHE
    _CACHE = None


def has_language_config() -> bool:
    """本地是否已有语言配置（config 存在且 cli.locale 为 zh 或 en）。"""
    p = paths.get_config_path()
    if not p.exists():
        return False
    try:
        data = migrate_from_legacy(json.loads(p.read_text(encoding="utf-8")))
        return (data.get("cli") or {}).get("locale") in ("zh", "en")
    except Exception:
        return False
