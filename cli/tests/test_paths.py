"""测试 joytrunk.paths。"""

import os

import pytest

from joytrunk import paths


def test_get_cli_root_is_parent_of_joytrunk_package():
    """get_cli_root() 返回 joytrunk 包目录的上一级。"""
    cli_root = paths.get_cli_root()
    assert cli_root is not None
    assert hasattr(cli_root, "resolve")
    # 可编辑安装时 cli_root 下应有 joytrunk 包
    assert (cli_root / "joytrunk" / "paths.py").exists()


def test_get_joytrunk_root_uses_env(monkeypatch, tmp_path):
    monkeypatch.setenv("JOYTRUNK_ROOT", str(tmp_path / "custom"))
    root = paths.get_joytrunk_root()
    assert "custom" in str(root)
    assert root == (tmp_path / "custom").resolve()


def test_get_config_path(joytrunk_root):
    p = paths.get_config_path()
    assert p == joytrunk_root / "config.json"


def test_get_workspace_root(joytrunk_root):
    p = paths.get_workspace_root()
    assert p == joytrunk_root / "workspace"


def test_get_employee_dir(joytrunk_root):
    p = paths.get_employee_dir("emp-001")
    assert p == joytrunk_root / "workspace" / "employees" / "emp-001"


def test_get_workspace_memory(joytrunk_root):
    p = paths.get_workspace_memory()
    assert p == joytrunk_root / "workspace" / "memory"


def test_get_workspace_skills(joytrunk_root):
    p = paths.get_workspace_skills()
    assert p == joytrunk_root / "workspace" / "skills"
