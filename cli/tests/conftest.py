"""Pytest 配置与公共 fixture。"""

import os

import pytest


@pytest.fixture(autouse=True)
def joytrunk_root(tmp_path, monkeypatch):
    """将 JoyTrunk 根目录指向临时目录，便于测试 paths/context/session/config 等。"""
    root = tmp_path / "joytrunk"
    root.mkdir()
    monkeypatch.setenv("JOYTRUNK_ROOT", str(root))
    yield root
    monkeypatch.delenv("JOYTRUNK_ROOT", raising=False)


@pytest.fixture
def workspace_root(joytrunk_root):
    """~/.joytrunk/workspace"""
    d = joytrunk_root / "workspace"
    d.mkdir()
    return d


@pytest.fixture
def employee_dir(workspace_root):
    """某员工的 workspace 子目录。"""
    d = workspace_root / "employees" / "emp-001"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def config_with_custom_llm(joytrunk_root):
    """主 config：含 ownerId 与自有 LLM。"""
    import json
    c = {
        "version": 1,
        "ownerId": "owner-1",
        "server": {"host": "localhost", "port": 32890},
        "agents": {"defaults": {"model": "gpt-3.5-turbo", "maxTokens": 2048, "temperature": 0.1}},
        "providers": {
            "joytrunk": {},
            "custom": {"apiKey": "sk-test", "apiBase": "https://api.example.com/v1", "model": "gpt-3.5-turbo"},
        },
    }
    (joytrunk_root / "config.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    return c


@pytest.fixture
def config_without_custom_llm(joytrunk_root):
    """主 config：无自有 LLM（走 Router）。"""
    import json
    c = {
        "version": 1,
        "ownerId": "owner-1",
        "server": {"host": "localhost", "port": 32890},
        "agents": {"defaults": {"model": "gpt-3.5-turbo", "maxTokens": 2048}},
        "providers": {"joytrunk": {}, "custom": {"apiKey": "", "apiBase": None, "model": "gpt-3.5-turbo"}},
    }
    (joytrunk_root / "config.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    return c
