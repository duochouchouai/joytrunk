"""
解析 cli/.env 并将可导入变量合并到 config。
用于 onboard 时可选将 API Key 等导入到 ~/.joytrunk/config.json。
"""

from pathlib import Path

# 可导入的 .env 键（至少有一个非空即视为“有效”）
IMPORTABLE_KEYS = frozenset({
    "OPENAI_API_KEY",
    "OPENAI_API_BASE_URL",
    "OPENAI_MODEL",
    "CUSTOM_LLM_API_KEY",
    "CUSTOM_LLM_BASE_URL",
    "CUSTOM_LLM_MODEL",
    "JOYTRUNK_ROUTER_URL",
})


def parse_dotenv(path: Path) -> dict[str, str]:
    """
    解析 .env 文件：按行读取，忽略空行和 # 注释；
    每行按第一个 = 拆成 key/value，strip 后返回 dict。
    """
    out: dict[str, str] = {}
    if not path.exists() or not path.is_file():
        return out
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key:
            out[key] = value
    return out


def is_valid_importable_env(parsed: dict[str, str]) -> bool:
    """解析结果中至少有一个可导入键且值非空即视为有效。"""
    for k in IMPORTABLE_KEYS:
        if k in parsed and parsed[k].strip():
            return True
    return False


def merge_env_into_config(parsed: dict[str, str], config: dict) -> dict:
    """
    将 .env 解析结果合并到 config 的 providers.custom 与 providers.joytrunk。
    仅当 .env 中该键有非空值时才覆盖。不写文件，返回修改后的 config（原地也会改）。
    """
    if "providers" not in config or not isinstance(config["providers"], dict):
        config["providers"] = {"joytrunk": {}, "custom": {"apiKey": "", "apiBase": None, "model": "gpt-3.5-turbo"}}
    providers = config["providers"]
    if "custom" not in providers or not isinstance(providers["custom"], dict):
        providers["custom"] = {"apiKey": "", "apiBase": None, "model": "gpt-3.5-turbo"}
    if "joytrunk" not in providers or not isinstance(providers["joytrunk"], dict):
        providers["joytrunk"] = {}

    custom = providers["custom"]
    joytrunk = providers["joytrunk"]

    # custom LLM
    api_key = (
        parsed.get("OPENAI_API_KEY", "").strip()
        or parsed.get("CUSTOM_LLM_API_KEY", "").strip()
    )
    if api_key:
        custom["apiKey"] = api_key
    api_base = (
        parsed.get("OPENAI_API_BASE_URL", "").strip()
        or parsed.get("CUSTOM_LLM_BASE_URL", "").strip()
    )
    if api_base:
        custom["apiBase"] = api_base.rstrip("/")
    model = (
        parsed.get("OPENAI_MODEL", "").strip()
        or parsed.get("CUSTOM_LLM_MODEL", "").strip()
    )
    if model:
        custom["model"] = model

    # JoyTrunk Router
    router_url = parsed.get("JOYTRUNK_ROUTER_URL", "").strip()
    if router_url:
        joytrunk["apiBase"] = router_url.rstrip("/")

    return config


def offer_import_env_from_cli_dotenv(
    get_cli_root,
    load_config,
    save_config,
    prompt_yes_no,
) -> bool:
    """
    若 cli 根目录下存在有效 .env，则通过 prompt_yes_no() 询问用户；
    若返回 True，则将 .env 中可导入变量合并到 config 并写回。
    get_cli_root: () -> Path, load_config: () -> dict, save_config: (dict) -> None,
    prompt_yes_no: () -> bool. 返回是否执行了导入。
    """
    env_path = get_cli_root() / ".env"
    if not env_path.exists():
        return False
    parsed = parse_dotenv(env_path)
    if not is_valid_importable_env(parsed):
        return False
    if not prompt_yes_no():
        return False
    config = load_config()
    merge_env_into_config(parsed, config)
    save_config(config)
    return True
