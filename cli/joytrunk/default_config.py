"""JoyTrunk 默认配置与 schema 约定（与 nodejs 一致，仿 nanobot 结构）。"""

from joytrunk.config_schema import DEFAULT_CONFIG, migrate_from_legacy

__all__ = ["DEFAULT_CONFIG", "migrate_from_legacy"]
