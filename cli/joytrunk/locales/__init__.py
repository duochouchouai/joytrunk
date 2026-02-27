# -*- coding: utf-8 -*-
"""CLI 多语言文案包。"""

from joytrunk.locales.zh import MESSAGES as ZH
from joytrunk.locales.en import MESSAGES as EN

TRANSLATIONS = {"zh": ZH, "en": EN}
DEFAULT_LOCALE = "zh"
SUPPORTED = ("zh", "en")

__all__ = ["TRANSLATIONS", "DEFAULT_LOCALE", "SUPPORTED"]
