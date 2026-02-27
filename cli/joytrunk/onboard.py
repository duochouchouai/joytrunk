"""joytrunk onboard：创建 ~/.joytrunk、config、workspace 及共享目录与模板。"""

import json
from pathlib import Path

from joytrunk import paths
from joytrunk.default_config import DEFAULT_CONFIG, migrate_from_legacy

BUNDLED_TEMPLATES = Path(__file__).resolve().parent / "templates"


def run_onboard(initial_locale: str | None = None) -> Path:
    """
    创建 JoyTrunk 根目录、config.json、workspace 及 workspace/skills、workspace/memory。
    若 initial_locale 为 "zh" 或 "en"，会写入 config 的 cli.locale（首次或未配置时由 CLI 传入）。
    模板仅存在于 joytrunk 包内（joytrunk/templates），不在 workspace 下创建 templates。
    员工目录（workspace/employees/<id>）在创建员工时由后端从包内/捆绑模板复制初始化。
    返回 JoyTrunk 根路径。
    """
    root = paths.get_joytrunk_root()
    root.mkdir(parents=True, exist_ok=True)

    config_path = paths.get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = migrate_from_legacy(json.load(f))
        config["joytrunkRoot"] = str(root.resolve())
        if initial_locale in ("zh", "en"):
            if "cli" not in config or not isinstance(config["cli"], dict):
                config["cli"] = {}
            config["cli"]["locale"] = initial_locale
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    else:
        config = migrate_from_legacy({})
        config["joytrunkRoot"] = str(root.resolve())
        if "cli" not in config or not isinstance(config["cli"], dict):
            config["cli"] = dict(DEFAULT_CONFIG.get("cli", {"locale": "zh"}))
        config["cli"]["locale"] = initial_locale if initial_locale in ("zh", "en") else "zh"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    paths.get_workspace_root().mkdir(parents=True, exist_ok=True)
    paths.get_workspace_skills().mkdir(parents=True, exist_ok=True)
    paths.get_workspace_memory().mkdir(parents=True, exist_ok=True)
    return root
