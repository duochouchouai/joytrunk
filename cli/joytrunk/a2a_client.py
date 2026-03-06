"""
A2A Client (plan phase 2): call Gateway Send Message / Get Task.
Used by CLI and (phase 3) by agent tools.

端口仅从 cli/.env 的 JOYTRUNK_A2A_PORT 读取（默认 32900），不读 config.json。
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from joytrunk import paths
from joytrunk.config_store import load_config
from joytrunk.env_loader import parse_dotenv

DEFAULT_A2A_PORT = 32900


def _get_a2a_port() -> int:
    """端口仅从 cli/.env 或环境变量 JOYTRUNK_A2A_PORT 读取，未设置或无效时返回 DEFAULT_A2A_PORT。"""
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


def get_gateway_base_url() -> str:
    """Gateway base URL：端口仅从 cli/.env 的 JOYTRUNK_A2A_PORT 读取，默认 32900。"""
    port = _get_a2a_port()
    return f"http://127.0.0.1:{port}"


def gateway_available(timeout: float = 2.0) -> bool:
    """Return True if Gateway responds (e.g. Get Task 404 counts as available)."""
    base = get_gateway_base_url()
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(f"{base}/a2a/v1/tenants/__ping__/tasks/__ping__")
            return True
    except Exception:
        return False


def send_message(
    owner_id: str,
    employee_id: str,
    content: str,
    session_key: str | None = None,
    timeout_seconds: float | None = None,
    from_employee_id: str | None = None,
) -> tuple[str, dict[str, int] | None] | None:
    """
    A2A Send Message (blocking=true). Returns (reply, usage) or None if Gateway unavailable.
    usage: { "prompt_tokens", "completion_tokens" }; CLI may map to input_tokens/output_tokens for display.
    from_employee_id: optional, for Agent→Agent calls (plan 10.9).
    """
    base = get_gateway_base_url()
    c = load_config()
    timeout_seconds = timeout_seconds or (c.get("gateway") or {}).get("blocking_timeout_seconds") or 300
    url = f"{base}/a2a/v1/tenants/{owner_id}/employees/{employee_id}/message:send"
    metadata = {"channel": "cli", "chat_id": "direct"}
    if from_employee_id is not None:
        metadata["from_employee_id"] = from_employee_id
    body = {
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": content or ""}],
            **({"contextId": session_key} if session_key else {}),
        },
        "configuration": {"blocking": True},
        "metadata": metadata,
    }
    try:
        with httpx.Client(timeout=float(timeout_seconds)) as client:
            r = client.post(
                url,
                json=body,
                headers={"Content-Type": "application/json", "A2A-Version": "1.0"},
            )
            if not r.is_success:
                return None
            data = r.json()
    except Exception:
        return None
    reply = ""
    if isinstance(data.get("history"), list):
        for m in reversed(data["history"]):
            if m.get("role") == "agent" and m.get("parts"):
                reply = "".join(p.get("text", "") for p in m["parts"] if p.get("type") == "text")
                break
    usage = None
    if isinstance(data.get("metadata"), dict) and isinstance(data["metadata"].get("usage"), dict):
        u = data["metadata"]["usage"]
        usage = {"prompt_tokens": u.get("prompt_tokens", 0), "completion_tokens": u.get("completion_tokens", 0)}
    return (reply or "", usage)


def get_task(owner_id: str, task_id: str, timeout: float = 10.0) -> dict[str, Any] | None:
    """A2A Get Task. Returns task dict or None on error."""
    base = get_gateway_base_url()
    url = f"{base}/a2a/v1/tenants/{owner_id}/tasks/{task_id}"
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, headers={"A2A-Version": "1.0"})
            if not r.is_success:
                return None
            return r.json()
    except Exception:
        return None
