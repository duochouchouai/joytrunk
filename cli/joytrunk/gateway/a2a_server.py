"""
A2A server entry: load config for non-port settings, create app with lifespan (worker), run uvicorn.
Port only from cli/.env JOYTRUNK_A2A_PORT (default 32900). Bind 127.0.0.1 only.
"""

from __future__ import annotations

import logging
import os
import sys

import uvicorn

from joytrunk import paths
from joytrunk.config_store import load_config
from joytrunk.env_loader import parse_dotenv
from joytrunk.gateway.a2a_http import create_app

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_A2A_PORT = 32900


def _get_a2a_port() -> int:
    """端口仅从 cli/.env 的 JOYTRUNK_A2A_PORT 读取，未设置或无效时返回 DEFAULT_A2A_PORT。"""
    raw = os.environ.get("JOYTRUNK_A2A_PORT", "").strip()
    if not raw:
        parsed = parse_dotenv(paths.get_cli_root() / ".env")
        raw = parsed.get("JOYTRUNK_A2A_PORT", "").strip()
    if not raw:
        return DEFAULT_A2A_PORT
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_A2A_PORT


def main() -> None:
    config = load_config()
    gateway = config.get("gateway") or {}
    official = config.get("official") or {}
    a2a_port = _get_a2a_port()
    worker_concurrency = int(gateway.get("worker_concurrency", 4))
    blocking_timeout = int(gateway.get("blocking_timeout_seconds", 300))
    ttl = int(gateway.get("task_store_ttl_seconds", 86400))
    cleanup_interval = int(gateway.get("task_store_cleanup_interval_seconds", 60))
    official_api_key = (official.get("api_key") or "").strip() or None
    official_url = (official.get("url") or "").strip() or None
    app = create_app(
        blocking_timeout_seconds=blocking_timeout,
        worker_concurrency=worker_concurrency,
        task_store_ttl_seconds=ttl,
        task_store_cleanup_interval_seconds=cleanup_interval,
        official_api_key=official_api_key,
        official_url=official_url,
    )
    logger.info("A2A Gateway listening on 127.0.0.1:%d (worker_concurrency=%d)", a2a_port, worker_concurrency)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=a2a_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
