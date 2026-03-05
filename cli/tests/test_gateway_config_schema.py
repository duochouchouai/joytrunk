# -*- coding: utf-8 -*-
"""Gateway 配置：Python schema 与 Node configSchema 中 gateway 段（方案 2.2、11.2）。"""

import json

import pytest

from joytrunk.config_schema import DEFAULT_CONFIG, migrate_from_legacy


def test_default_config_has_gateway_section():
    assert "gateway" in DEFAULT_CONFIG
    gw = DEFAULT_CONFIG["gateway"]
    assert gw["a2a_port"] == 32900
    assert gw.get("a2a_backend_url") is None
    assert gw["worker_concurrency"] == 4
    assert gw["blocking_timeout_seconds"] == 300
    assert gw["task_store_ttl_seconds"] == 86400
    assert gw["task_store_cleanup_interval_seconds"] == 60
    assert gw["max_body_size_bytes"] == 10485760


def test_migrate_from_legacy_preserves_gateway():
    raw = {"version": 1, "ownerId": "o1", "gateway": {"a2a_port": 32892, "a2a_backend_url": "http://localhost:32892"}}
    out = migrate_from_legacy(raw)
    assert "gateway" in out
    assert out["gateway"]["a2a_port"] == 32892
    assert out["gateway"]["a2a_backend_url"] == "http://localhost:32892"


def test_migrate_from_legacy_no_gateway_uses_defaults():
    raw = {"version": 1, "ownerId": "o1"}
    out = migrate_from_legacy(raw)
    assert out["gateway"]["a2a_port"] == 32900
    assert out["gateway"]["worker_concurrency"] == 4


def test_migrate_from_legacy_none_returns_full_default():
    out = migrate_from_legacy(None)
    assert "gateway" in out
    assert out["gateway"]["a2a_port"] == 32900
