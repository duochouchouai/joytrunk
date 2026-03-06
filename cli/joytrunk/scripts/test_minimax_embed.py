"""
本地测试：用当前 config 调用 MiniMax embedding API。
用法：在 cli 目录下执行  python -m joytrunk.scripts.test_minimax_embed
会读取 ~/.joytrunk/config.json 的 memory.embedding 与 providers.custom，发一条 embedding 请求并打印结果。
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# 确保能 import joytrunk（从 repo 根或 cli 运行时）
_cli_root = Path(__file__).resolve().parent.parent.parent
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))

from joytrunk import paths
from joytrunk.agent.memory.embedding_client import HTTPEmbeddingClient


def load_embed_config() -> tuple[str, str, str, str]:
    """从 config 读取 base_url, api_key, embed_model, group_id。"""
    config_path = paths.get_config_path()
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    mem = config.get("memory") or {}
    emb = mem.get("embedding") or {}
    custom = (config.get("providers") or {}).get("custom") or {}
    base_url = (emb.get("base_url") or custom.get("apiBase") or custom.get("baseUrl") or "").strip().rstrip("/")
    api_key = (emb.get("api_key") or custom.get("apiKey") or "").strip()
    embed_model = (emb.get("embed_model") or "embo-01").strip()
    group_id = (emb.get("group_id") or "").strip()
    return base_url, api_key, embed_model, group_id


async def main() -> None:
    base_url, api_key, embed_model, group_id = load_embed_config()
    if not base_url:
        print("ERROR: base_url is empty. Set memory.embedding.base_url or providers.custom.apiBase in config.")
        sys.exit(1)
    if not api_key:
        print("ERROR: api_key is empty. Set memory.embedding.api_key or providers.custom.apiKey in config.")
        sys.exit(1)
    print(f"base_url: {base_url}")
    print(f"embed_model: {embed_model}")
    print(f"group_id: {group_id or '(empty)'}")
    print("Calling POST /embeddings with texts=['测试'], type='query' ...")
    client = HTTPEmbeddingClient(
        base_url=base_url,
        api_key=api_key,
        embed_model=embed_model,
        group_id=group_id or None,
    )
    try:
        vectors = await client.embed(["测试"], embed_type="query")
        print(f"OK: got {len(vectors)} vector(s), dim={len(vectors[0]) if vectors else 0}")
        if vectors:
            print(f"First 5 dims: {vectors[0][:5]}")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
