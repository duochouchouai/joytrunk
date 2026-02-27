"""测试 env_loader：解析 .env、有效判断、合并到 config。"""

from pathlib import Path

import pytest

from joytrunk.env_loader import (
    IMPORTABLE_KEYS,
    is_valid_importable_env,
    merge_env_into_config,
    parse_dotenv,
)


def test_parse_dotenv_missing_file(tmp_path: Path) -> None:
    assert parse_dotenv(tmp_path / "nonexistent") == {}


def test_parse_dotenv_empty_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("", encoding="utf-8")
    assert parse_dotenv(tmp_path / ".env") == {}


def test_parse_dotenv_comments_and_empty_lines(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "# comment\n\nFOO=bar\n  # inline\nBAR=baz\n",
        encoding="utf-8",
    )
    got = parse_dotenv(tmp_path / ".env")
    assert got == {"FOO": "bar", "BAR": "baz"}


def test_parse_dotenv_first_equals_only(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("KEY=value=with=equals\n", encoding="utf-8")
    got = parse_dotenv(tmp_path / ".env")
    assert got["KEY"] == "value=with=equals"


def test_parse_dotenv_strips_key_value(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("  OPENAI_API_KEY  =  sk-xxx  \n", encoding="utf-8")
    got = parse_dotenv(tmp_path / ".env")
    assert got == {"OPENAI_API_KEY": "sk-xxx"}


def test_parse_dotenv_no_equals_skipped(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("NOEQUALS\nKEY=yes\n", encoding="utf-8")
    got = parse_dotenv(tmp_path / ".env")
    assert got == {"KEY": "yes"}


def test_is_valid_importable_env_empty() -> None:
    assert is_valid_importable_env({}) is False


def test_is_valid_importable_env_key_empty_value() -> None:
    assert is_valid_importable_env({"OPENAI_API_KEY": ""}) is False
    assert is_valid_importable_env({"OPENAI_API_KEY": "   "}) is False


def test_is_valid_importable_env_key_with_value() -> None:
    assert is_valid_importable_env({"OPENAI_API_KEY": "sk-x"}) is True
    assert is_valid_importable_env({"JOYTRUNK_ROUTER_URL": "https://x/v1"}) is True
    assert is_valid_importable_env({"CUSTOM_LLM_MODEL": "gpt-4"}) is True


def test_merge_env_into_config_empty_parsed() -> None:
    config = {
        "providers": {
            "joytrunk": {},
            "custom": {"apiKey": "", "apiBase": None, "model": "gpt-3.5-turbo"},
        },
    }
    merge_env_into_config({}, config)
    assert config["providers"]["custom"]["apiKey"] == ""
    assert config["providers"]["custom"]["apiBase"] is None


def test_merge_env_into_config_custom_api_key() -> None:
    config = {
        "providers": {
            "joytrunk": {},
            "custom": {"apiKey": "", "apiBase": None, "model": "gpt-3.5-turbo"},
        },
    }
    merge_env_into_config({"OPENAI_API_KEY": "sk-imported"}, config)
    assert config["providers"]["custom"]["apiKey"] == "sk-imported"


def test_merge_env_into_config_custom_api_base_and_model() -> None:
    config = {
        "providers": {
            "joytrunk": {},
            "custom": {"apiKey": "", "apiBase": None, "model": "gpt-3.5-turbo"},
        },
    }
    merge_env_into_config(
        {
            "OPENAI_API_BASE_URL": "https://api.example.com/v1/",
            "OPENAI_MODEL": "gpt-4",
        },
        config,
    )
    assert config["providers"]["custom"]["apiBase"] == "https://api.example.com/v1"
    assert config["providers"]["custom"]["model"] == "gpt-4"


def test_merge_env_into_config_joytrunk_router() -> None:
    config = {
        "providers": {
            "joytrunk": {},
            "custom": {"apiKey": "", "apiBase": None, "model": "gpt-3.5-turbo"},
        },
    }
    merge_env_into_config({"JOYTRUNK_ROUTER_URL": "https://router.example/v1/"}, config)
    assert config["providers"]["joytrunk"]["apiBase"] == "https://router.example/v1"


def test_merge_env_into_config_creates_providers_if_missing() -> None:
    config: dict = {}
    merge_env_into_config({"OPENAI_API_KEY": "sk-x"}, config)
    assert "providers" in config
    assert config["providers"]["custom"]["apiKey"] == "sk-x"


def test_merge_env_into_config_custom_llm_vars_override() -> None:
    config = {
        "providers": {
            "joytrunk": {},
            "custom": {"apiKey": "existing", "apiBase": None, "model": "gpt-3.5-turbo"},
        },
    }
    merge_env_into_config(
        {"CUSTOM_LLM_API_KEY": "sk-new", "CUSTOM_LLM_BASE_URL": "https://new/v1", "CUSTOM_LLM_MODEL": "gpt-4"},
        config,
    )
    assert config["providers"]["custom"]["apiKey"] == "sk-new"
    assert config["providers"]["custom"]["apiBase"] == "https://new/v1"
    assert config["providers"]["custom"]["model"] == "gpt-4"


def test_importable_keys_defined() -> None:
    assert "OPENAI_API_KEY" in IMPORTABLE_KEYS
    assert "JOYTRUNK_ROUTER_URL" in IMPORTABLE_KEYS


def test_offer_import_env_from_cli_dotenv_when_confirmed(
    joytrunk_root: Path, tmp_path: Path
) -> None:
    """当 .env 存在且用户确认时，将配置导入到 config.json。"""
    from joytrunk import config_store
    from joytrunk.env_loader import offer_import_env_from_cli_dotenv

    cli_root = tmp_path / "cli_root"
    cli_root.mkdir()
    (cli_root / ".env").write_text("OPENAI_API_KEY=sk-imported\n", encoding="utf-8")

    did_import = offer_import_env_from_cli_dotenv(
        get_cli_root=lambda: cli_root,
        load_config=config_store.load_config,
        save_config=config_store.save_config,
        prompt_yes_no=lambda: True,
    )
    assert did_import is True
    config = config_store.load_config()
    assert config["providers"]["custom"]["apiKey"] == "sk-imported"


def test_offer_import_env_from_cli_dotenv_when_declined(
    joytrunk_root: Path, tmp_path: Path
) -> None:
    """当用户拒绝时，不修改 config。"""
    from joytrunk import config_store
    from joytrunk.env_loader import offer_import_env_from_cli_dotenv

    # 先写入已知的默认 config，确保 apiKey 为空
    initial = config_store.load_config()
    initial["providers"]["custom"]["apiKey"] = ""
    config_store.save_config(initial)

    cli_root = tmp_path / "cli_root"
    cli_root.mkdir()
    (cli_root / ".env").write_text("OPENAI_API_KEY=sk-would-import\n", encoding="utf-8")

    did_import = offer_import_env_from_cli_dotenv(
        get_cli_root=lambda: cli_root,
        load_config=config_store.load_config,
        save_config=config_store.save_config,
        prompt_yes_no=lambda: False,
    )
    assert did_import is False
    config = config_store.load_config()
    assert config["providers"]["custom"]["apiKey"] == ""


def test_offer_import_env_from_cli_dotenv_no_file(joytrunk_root: Path, tmp_path: Path) -> None:
    """当 .env 不存在时，不提示、不导入。"""
    from joytrunk import config_store
    from joytrunk.env_loader import offer_import_env_from_cli_dotenv

    cli_root = tmp_path / "cli_root"
    cli_root.mkdir()

    did_import = offer_import_env_from_cli_dotenv(
        get_cli_root=lambda: cli_root,
        load_config=config_store.load_config,
        save_config=config_store.save_config,
        prompt_yes_no=lambda: True,
    )
    assert did_import is False
