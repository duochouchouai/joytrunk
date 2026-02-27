"""测试 joytrunk.agent.employee_config。"""

import json

import pytest

from joytrunk.agent.employee_config import (
    get_llm_params,
    get_merged_config_for_employee,
    has_custom_llm,
)


def test_get_merged_config_main_only(config_with_custom_llm):
    c = get_merged_config_for_employee("emp-001")
    assert c["ownerId"] == "owner-1"
    assert c["providers"]["custom"]["apiKey"] == "sk-test"
    assert c["providers"]["custom"]["apiBase"] == "https://api.example.com/v1"


def test_has_custom_llm_true(config_with_custom_llm):
    c = get_merged_config_for_employee("emp-001")
    assert has_custom_llm(c, "owner-1") is True


def test_has_custom_llm_false_wrong_owner(config_with_custom_llm):
    c = get_merged_config_for_employee("emp-001")
    assert has_custom_llm(c, "other-owner") is False


def test_has_custom_llm_false_empty_custom(config_without_custom_llm):
    c = get_merged_config_for_employee("emp-001")
    assert has_custom_llm(c, "owner-1") is False


def test_get_llm_params_custom(config_with_custom_llm, employee_dir):
    (employee_dir / "config.json").write_text("{}", encoding="utf-8")
    params = get_llm_params("emp-001", "owner-1")
    assert params["source"] == "custom"
    assert params["base_url"] == "https://api.example.com/v1"
    assert params["api_key"] == "sk-test"
    assert params["model"] == "gpt-3.5-turbo"
    assert "max_tokens" in params
    assert "temperature" in params


def test_get_llm_params_router(config_without_custom_llm, joytrunk_root):
    params = get_llm_params("emp-001", "owner-1")
    assert params["source"] == "router"
    assert "gateway_base_url" in params
    assert params["owner_id"] == "owner-1"
    assert params["model"] == "gpt-3.5-turbo"


def test_get_llm_params_employee_overrides_model(config_with_custom_llm, employee_dir):
    (employee_dir / "config.json").write_text(
        json.dumps({"agents": {"defaults": {"model": "gpt-4", "maxTokens": 4096}}}),
        encoding="utf-8",
    )
    params = get_llm_params("emp-001", "owner-1")
    assert params["source"] == "custom"
    assert params["max_tokens"] == 4096
