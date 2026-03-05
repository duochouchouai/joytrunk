"""
A2A server entry: load config, create app with lifespan (worker), run uvicorn (plan 2.1方案 A).
Bind 127.0.0.1 only (plan 10.49).
"""

from __future__ import annotations

import logging
import sys

import uvicorn

from joytrunk.config_store import load_config
from joytrunk.gateway.a2a_http import create_app

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    config = load_config()
    gateway = config.get("gateway") or {}
    official = config.get("official") or {}
    a2a_port = int(gateway.get("a2a_port", 32900))
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
