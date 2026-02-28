"""测试路径与 onboard：平台无关根目录、onboard 创建目录与 config。"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from joytrunk import paths
from joytrunk.paths import (
    get_config_path,
    get_employee_dir,
    get_joytrunk_root,
    get_workspace_root,
    get_workspace_skills,
)
from joytrunk.onboard import run_onboard
from joytrunk.i18n import has_language_config


def test_get_joytrunk_root_uses_home(monkeypatch) -> None:
    monkeypatch.delenv("JOYTRUNK_ROOT", raising=False)
    home = Path.home()
    assert get_joytrunk_root() == home / ".joytrunk"


def test_get_config_path() -> None:
    assert get_config_path() == get_joytrunk_root() / "config.json"


def test_get_workspace_paths() -> None:
    root = get_joytrunk_root()
    assert get_workspace_root() == root / "workspace"
    assert get_workspace_skills() == root / "workspace" / "skills"
    assert get_employee_dir("emp-1") == root / "workspace" / "employees" / "emp-1"


def test_run_onboard_creates_dirs_and_config() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with patch.object(paths, "get_joytrunk_root", return_value=tmp_path):
            root = run_onboard()
        assert root == tmp_path
        assert (tmp_path / "config.json").exists()
        assert (tmp_path / "workspace").is_dir()
        assert (tmp_path / "workspace" / "skills").is_dir()
        assert (tmp_path / "workspace" / "memory").is_dir()
        with open(tmp_path / "config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        assert config["joytrunkRoot"] == str(tmp_path.resolve())
        assert config.get("server", {}).get("port") == 32890
        assert config.get("cli", {}).get("locale") == "zh"


def test_run_onboard_with_initial_locale() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with patch.object(paths, "get_joytrunk_root", return_value=tmp_path):
            root = run_onboard(initial_locale="en")
        assert root == tmp_path
        with open(tmp_path / "config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        assert config.get("cli", {}).get("locale") == "en"


def test_has_language_config(joytrunk_root) -> None:
    assert has_language_config() is False
    config_path = paths.get_config_path()
    config_path.write_text('{"cli": {"locale": "zh"}}', encoding="utf-8")
    assert has_language_config() is True
    config_path.write_text('{"cli": {"locale": "en"}}', encoding="utf-8")
    assert has_language_config() is True
