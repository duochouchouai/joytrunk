"""
全局 config.json 仅保留全局配置；每位员工作为独立 agent，使用各自
workspace/employees/<employee_id>/config.json（覆盖全局配置）。
员工列表由扫描 workspace/employees/ 下各目录的 config.json 得到。
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timezone

from joytrunk import paths
from joytrunk.config_schema import migrate_from_legacy, DEFAULT_CONFIG

BUNDLED_TEMPLATES = Path(__file__).resolve().parent / "templates"


def load_config() -> dict:
    """加载全局 config.json 并迁移；若存在旧版 employees 数组则迁移到各员工 config.json。"""
    p = paths.get_config_path()
    if not p.exists():
        return migrate_from_legacy(None)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        config = migrate_from_legacy(raw)
        if isinstance(raw.get("employees"), list) and len(raw["employees"]) > 0:
            _migrate_employees_to_per_agent_config(raw["employees"])
            save_config(config)
        return config
    except Exception:
        return migrate_from_legacy(None)


def _migrate_employees_to_per_agent_config(employees: list[dict]) -> None:
    """将旧版全局 employees 数组的每项写入对应员工目录的 config.json。"""
    workspace_employees = paths.get_workspace_root() / "employees"
    workspace_employees.mkdir(parents=True, exist_ok=True)
    for e in employees:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        eid = e["id"]
        emp_dir = paths.get_employee_dir(eid)
        cfg_path = emp_dir / "config.json"
        if cfg_path.exists():
            continue
        emp_dir.mkdir(parents=True, exist_ok=True)
        emp_cfg = {k: v for k, v in e.items()}
        if "agents" not in emp_cfg:
            emp_cfg["agents"] = {}
        if "providers" not in emp_cfg:
            emp_cfg["providers"] = {}
        cfg_path.write_text(json.dumps(emp_cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        if not (emp_dir / "memory").exists():
            (emp_dir / "memory").mkdir(parents=True, exist_ok=True)
        if not (emp_dir / "skills").exists():
            (emp_dir / "skills").mkdir(parents=True, exist_ok=True)


def save_config(config: dict) -> None:
    """写回全局 config.json（仅全局配置）。"""
    root = paths.get_joytrunk_root()
    root.mkdir(parents=True, exist_ok=True)
    p = paths.get_config_path()
    out = {k: v for k, v in config.items() if k in DEFAULT_CONFIG}
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_owner_id() -> str:
    """若全局 config 中无 ownerId，则生成并写入；返回当前 ownerId。"""
    config = load_config()
    oid = config.get("ownerId")
    if oid and isinstance(oid, str) and oid.strip():
        return oid.strip()
    oid = str(uuid.uuid4())
    config["ownerId"] = oid
    if not config.get("joytrunkRoot"):
        config["joytrunkRoot"] = str(paths.get_joytrunk_root().resolve())
    save_config(config)
    return oid


def list_employees_from_config(owner_id: str | None = None) -> list[dict]:
    """从各员工目录的 config.json 读取员工列表；若传 owner_id 则只返回该负责人的员工。"""
    emp_root = paths.get_workspace_root() / "employees"
    if not emp_root.exists():
        return []
    result = []
    for d in emp_root.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        cfg_path = d / "config.json"
        if not cfg_path.exists():
            continue
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if owner_id and data.get("ownerId") != owner_id:
            continue
        result.append({"id": data.get("id") or d.name, **data})
    return result


def _copy_templates_to_employee(employee_id: str) -> None:
    """将包内 templates 复制到员工目录。"""
    emp_dir = paths.get_employee_dir(employee_id)
    if not BUNDLED_TEMPLATES.exists():
        emp_dir.mkdir(parents=True, exist_ok=True)
        (emp_dir / "memory").mkdir(parents=True, exist_ok=True)
        (emp_dir / "skills").mkdir(parents=True, exist_ok=True)
        return
    emp_dir.mkdir(parents=True, exist_ok=True)
    for item in BUNDLED_TEMPLATES.iterdir():
        if item.name.startswith("."):
            continue
        dest = emp_dir / item.name
        if item.is_file() and item.suffix == ".md":
            if not dest.exists():
                shutil.copy2(item, dest)
        elif item.is_dir() and item.name == "memory":
            mem_dest = emp_dir / "memory"
            mem_dest.mkdir(parents=True, exist_ok=True)
            for sub in item.iterdir():
                if sub.is_file() and not (mem_dest / sub.name).exists():
                    shutil.copy2(sub, mem_dest / sub.name)
    (emp_dir / "skills").mkdir(parents=True, exist_ok=True)


def create_employee_in_config(owner_id: str, name: str, **kwargs) -> dict:
    """
    创建员工：在 workspace/employees/<id>/ 下写入 config.json（身份 + 可选 agents/providers 覆盖），
    并复制模板。不写入全局 config。
    """
    eid = str(uuid.uuid4())
    emp_dir = paths.get_employee_dir(eid)
    emp_dir.mkdir(parents=True, exist_ok=True)
    emp_cfg = {
        "id": eid,
        "ownerId": owner_id,
        "name": name or "新员工",
        "persona": kwargs.get("persona"),
        "role": kwargs.get("role"),
        "specialty": kwargs.get("specialty"),
        "businessModule": kwargs.get("businessModule"),
        "focus": kwargs.get("focus"),
        "status": "active",
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "agents": kwargs.get("agents") or {},
        "providers": kwargs.get("providers") or {},
    }
    cfg_path = emp_dir / "config.json"
    cfg_path.write_text(json.dumps(emp_cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    _copy_templates_to_employee(eid)
    return emp_cfg


def update_employee_in_config(employee_id: str, owner_id: str, **kwargs) -> dict | None:
    """更新该员工目录下的 config.json。允许的键：name, persona, role, specialty, businessModule, focus, status；以及 agents、providers 用于覆盖全局。"""
    emp_dir = paths.get_employee_dir(employee_id)
    cfg_path = emp_dir / "config.json"
    if not cfg_path.exists():
        return None
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict) or data.get("ownerId") != owner_id:
        return None
    allowed = {"name", "persona", "role", "specialty", "businessModule", "focus", "status", "agents", "providers"}
    for k, v in kwargs.items():
        if k in allowed:
            data[k] = v
    cfg_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def find_employee_in_config(employee_id: str, owner_id: str | None = None) -> dict | None:
    """从该员工目录的 config.json 读取；若传 owner_id 则需匹配。"""
    emp_dir = paths.get_employee_dir(employee_id)
    cfg_path = emp_dir / "config.json"
    if not cfg_path.exists():
        return None
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    if owner_id and data.get("ownerId") != owner_id:
        return None
    return data
