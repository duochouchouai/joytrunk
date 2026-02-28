"""
JoyTrunk 全局 config.json schema：仅保留全局配置（与 nodejs 约定一致）。
每位员工作为独立 agent，使用各自 workspace/employees/<id>/config.json 覆盖全局配置。
"""

# 默认全局 config 结构（不含员工列表；员工列表由各员工目录下的 config.json 构成）
DEFAULT_CONFIG = {
    "version": 1,
    "joytrunkRoot": None,
    "ownerId": None,
    "cli": {
        "locale": "zh",
    },
    "server": {
        "host": "127.0.0.1",
        "port": 32890,
    },
    "agents": {
        "defaults": {
            "defaultEmployeeId": None,
            "model": "gpt-3.5-turbo",
            "maxTokens": 2048,
            "temperature": 0.1,
        }
    },
    "memory": {
        "auto_extract": True,
        "types": ["profile", "event"],
        "retrieve_top_k": 10,
        "embedding": {
            "base_url": "https://api.minimaxi.com/v1",
            "api_key": "",
            "embed_model": "embo-01",
        },
        "retrieve": {
            "method": "rag",
            "category": {"enabled": True, "top_k": 3},
            "item": {"top_k": 10, "ranking": "similarity", "recency_decay_days": 30.0},
            "resource": {"enabled": True, "top_k": 5},
            "sufficiency_check": False,
        },
    },
    "channels": {
        "cli": {"enabled": True},
        "web": {"enabled": True},
        "feishu": {"enabled": False},
        "telegram": {"enabled": False},
        "qq": {"enabled": False},
    },
    "providers": {
        "joytrunk": {},
        "custom": {
            "apiKey": "",
            "apiBase": None,
            "model": "gpt-3.5-turbo",
        },
    },
    "tools": {
        "web": {
            "search": {"apiKey": ""},
        },
        "mcp_servers": {},
    },
}

# 兼容旧版：曾用 gatewayPort / defaultEmployeeId / customLLM 平铺在顶层
def migrate_from_legacy(data: dict) -> dict:
    """将旧版 config 迁移到新 schema；输出仅含 server（迁移时从 gateway/gatewayPort 填充）。"""
    if not isinstance(data, dict):
        return dict(DEFAULT_CONFIG)
    out = {}
    for k, v in DEFAULT_CONFIG.items():
        if k == "server":
            old_gw = data.get("gateway") if isinstance(data.get("gateway"), dict) else {}
            out["server"] = {
                "host": old_gw.get("host", "127.0.0.1") if old_gw else "127.0.0.1",
                "port": old_gw.get("port", data.get("gatewayPort", 32890)) if old_gw else data.get("gatewayPort", 32890),
            }
        elif k == "agents":
            agents = data.get("agents") or {}
            defaults = agents.get("defaults") if isinstance(agents, dict) else {}
            if not isinstance(defaults, dict):
                defaults = {}
            out["agents"] = {
                "defaults": {
                    "defaultEmployeeId": defaults.get("defaultEmployeeId") or data.get("defaultEmployeeId"),
                    "model": defaults.get("model", "gpt-3.5-turbo"),
                    "maxTokens": defaults.get("maxTokens", 2048),
                    "temperature": defaults.get("temperature", 0.1),
                }
            }
        elif k == "providers":
            custom = data.get("providers", {}).get("custom") if isinstance(data.get("providers"), dict) else None
            if not custom and data.get("customLLM"):
                custom = data["customLLM"]
            if not isinstance(custom, dict):
                custom = dict(DEFAULT_CONFIG["providers"]["custom"])
            out["providers"] = {
                "joytrunk": data.get("providers", {}).get("joytrunk") if isinstance(data.get("providers"), dict) else {},
                "custom": {
                    "apiKey": custom.get("apiKey", ""),
                    "apiBase": custom.get("apiBase") or custom.get("baseUrl"),
                    "model": custom.get("model", "gpt-3.5-turbo"),
                },
            }
        elif k == "channels":
            out["channels"] = data.get("channels") if isinstance(data.get("channels"), dict) else dict(DEFAULT_CONFIG["channels"])
        elif k == "cli":
            out["cli"] = data.get("cli") if isinstance(data.get("cli"), dict) else dict(DEFAULT_CONFIG["cli"])
            if "locale" not in out["cli"] or out["cli"]["locale"] not in ("zh", "en"):
                out["cli"]["locale"] = DEFAULT_CONFIG["cli"]["locale"]
        elif k == "tools":
            tools_data = data.get("tools")
            if isinstance(tools_data, dict):
                web = tools_data.get("web")
                out["tools"] = {
                    "web": {
                        "search": {
                            "apiKey": (web.get("search") or {}).get("apiKey", "")
                            if isinstance(web, dict) else ""
                        }
                    } if isinstance(web, dict) else dict(DEFAULT_CONFIG["tools"]["web"]),
                    "mcp_servers": tools_data.get("mcp_servers")
                    if isinstance(tools_data.get("mcp_servers"), dict)
                    else {},
                }
            else:
                out["tools"] = dict(DEFAULT_CONFIG["tools"])
        else:
            out[k] = data.get(k, v)
    return out
