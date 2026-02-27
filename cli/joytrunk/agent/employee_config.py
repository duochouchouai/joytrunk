"""员工合并配置：主 config + 员工 config 覆盖（与 gateway lib/employeeConfig.js 一致）。"""

from __future__ import annotations

import json
from typing import Any

from joytrunk import paths
from joytrunk.config_schema import migrate_from_legacy


def _load_main_config() -> dict:
    p = paths.get_config_path()
    if not p.exists():
        return migrate_from_legacy(None)
    try:
        return migrate_from_legacy(json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        return migrate_from_legacy(None)


def _load_employee_config(employee_id: str) -> dict | None:
    emp_dir = paths.get_employee_dir(employee_id)
    p = emp_dir / "config.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _deep_merge(target: dict, source: dict) -> dict:
    out = dict(target)
    for key in source:
        if source[key] is None:
            continue
        if isinstance(source[key], dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], source[key])
        else:
            out[key] = source[key]
    return out


def get_merged_config_for_employee(employee_id: str) -> dict:
    """主 config 打底，员工 config 中仅 agents、providers 覆盖。"""
    main = _load_main_config()
    emp = _load_employee_config(employee_id)
    if not emp:
        return main
    filtered = {}
    if isinstance(emp.get("agents"), dict):
        filtered["agents"] = emp["agents"]
    if isinstance(emp.get("providers"), dict):
        filtered["providers"] = emp["providers"]
    if not filtered:
        return main
    import copy
    return _deep_merge(copy.deepcopy(main), filtered)


def has_custom_llm(config: dict, owner_id: str | None) -> bool:
    """是否已配置自有 LLM 且当前负责人匹配。"""
    if not owner_id or config.get("ownerId") != owner_id:
        return False
    custom = (config.get("providers") or {}).get("custom") or config.get("customLLM")
    if not isinstance(custom, dict):
        return False
    return bool(custom.get("apiKey") or custom.get("apiBase") or custom.get("baseUrl"))


def get_llm_params(employee_id: str, owner_id: str) -> dict[str, Any]:
    """
    返回当前员工使用的 LLM 参数：要么自有（custom），要么 JoyTrunk Router。
    员工必须使用 LLM（用户自己的或我们的），用于与大模型对话并执行返回结果。
    """
    config = get_merged_config_for_employee(employee_id)
    defaults = (config.get("agents") or {}).get("defaults") or {}
    max_tokens = defaults.get("maxTokens") or 2048
    temperature = float(defaults.get("temperature") or 0.1)
    default_model = defaults.get("model") or "gpt-3.5-turbo"

    if has_custom_llm(config, owner_id):
        custom = (config.get("providers") or {}).get("custom") or config.get("customLLM") or {}
        return {
            "source": "custom",
            "base_url": (custom.get("apiBase") or custom.get("baseUrl") or "https://api.openai.com/v1").rstrip("/"),
            "api_key": custom.get("apiKey") or "",
            "model": custom.get("model") or default_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
    # 使用 JoyTrunk Router（通过 gateway 代理）
    from joytrunk.api_client import get_base_url
    return {
        "source": "router",
        "gateway_base_url": get_base_url().rstrip("/"),
        "owner_id": owner_id,
        "model": default_model,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
