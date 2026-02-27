"""调用本地 gateway API（本地员工/聊天）。员工归属本地，无需「绑定负责人」；gateway 首次请求时自动创建本地上下文。"""

import json
from pathlib import Path

import httpx

from joytrunk import paths
from joytrunk.config_schema import migrate_from_legacy

DEFAULT_PORT = 32890


def _load_config():
    p = paths.get_config_path()
    if not p.exists():
        return migrate_from_legacy(None)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return migrate_from_legacy(raw)
    except Exception:
        return migrate_from_legacy(None)


def get_base_url():
    c = _load_config()
    g = c.get("gateway") or {}
    host = g.get("host") or "127.0.0.1"
    if host in ("localhost", "::1"):
        host = "127.0.0.1"
    port = g.get("port") or DEFAULT_PORT
    return f"http://{host}:{port}"


def get_owner_id():
    return _load_config().get("ownerId")


def ensure_owner_via_gateway() -> tuple[str | None, str | None]:
    """
    通过调用 gateway GET /api/owners/me 触发服务端创建本地默认上下文并写入 config，
    返回 (ownerId, None)；失败时返回 (None, 错误信息)。
    """
    try:
        api_get("/api/owners/me", owner_id=None)
    except Exception as e:
        return (None, str(e))
    return (_load_config().get("ownerId"), None)


def get_default_employee_id():
    c = _load_config()
    agents = c.get("agents") or {}
    defaults = agents.get("defaults") or {}
    return defaults.get("defaultEmployeeId")


def api_get(path: str, owner_id: str | None = None):
    headers = {}
    if owner_id:
        headers["X-Owner-Id"] = owner_id
    with httpx.Client(timeout=10.0) as client:
        r = client.get(get_base_url() + path, headers=headers)
        r.raise_for_status()
        return r.json()


def api_post(path: str, json_body: dict, owner_id: str | None = None):
    headers = {"Content-Type": "application/json"}
    if owner_id:
        headers["X-Owner-Id"] = owner_id
    with httpx.Client(timeout=30.0) as client:
        r = client.post(get_base_url() + path, json=json_body, headers=headers)
        r.raise_for_status()
        return r.json()


def list_employees(owner_id: str):
    return api_get("/api/employees", owner_id=owner_id)


def create_employee(owner_id: str, name: str, **kwargs):
    """POST /api/employees，创建员工。kwargs 可为 persona, role, specialty。"""
    body = {"name": name or "新员工", **kwargs}
    return api_post("/api/employees", body, owner_id=owner_id)


def chat(owner_id: str, employee_id: str, content: str):
    return api_post(f"/api/employees/{employee_id}/chat", {"content": content}, owner_id=owner_id)
