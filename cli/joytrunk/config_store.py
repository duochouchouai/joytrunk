"""
本地 config.json 读写：员工与负责人均存于 config.json，不使用 store.json。
供 chat / employee 命令直接读写，gateway 也可共用同一文件。
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from joytrunk import paths
from joytrunk.config_schema import migrate_from_legacy

BUNDLED_TEMPLATES = Path(__file__).resolve().parent / "templates"


def load_config() -> dict:
    """加载并迁移 config.json。"""
    p = paths.get_config_path()
    if not p.exists():
        return migrate_from_legacy(None)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return migrate_from_legacy(raw)
    except Exception:
        return migrate_from_legacy(None)


def save_config(config: dict) -> None:
    """写回 config.json。"""
    root = paths.get_joytrunk_root()
    root.mkdir(parents=True, exist_ok=True)
    p = paths.get_config_path()
    p.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_owner_id() -> str:
    """
    若 config 中无 ownerId，则生成并写入；返回当前 ownerId。
    不调用 gateway。
    """
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
    """从 config 读取员工列表；若传 owner_id 则只返回该负责人的员工。"""
    config = load_config()
    employees = config.get("employees") or []
    if not isinstance(employees, list):
        return []
    if owner_id:
        return [e for e in employees if isinstance(e, dict) and e.get("ownerId") == owner_id]
    return employees


def _copy_templates_to_employee(employee_id: str) -> None:
    """将包内 templates 复制到员工目录（与 gateway employeeWorkspace 行为一致）。"""
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
    在 config 中新增员工并写回；创建员工 workspace 目录并复制模板。
    返回新建员工对象 { id, ownerId, name, ... }。
    """
    config = load_config()
    employees = config.get("employees") or []
    if not isinstance(employees, list):
        employees = []
    eid = str(uuid.uuid4())
    emp = {
        "id": eid,
        "ownerId": owner_id,
        "name": name or "新员工",
        "persona": kwargs.get("persona"),
        "role": kwargs.get("role"),
        "specialty": kwargs.get("specialty"),
        "businessModule": kwargs.get("businessModule"),
        "focus": kwargs.get("focus"),
        "status": "active",
        "createdAt": None,
    }
    employees.append(emp)
    config["employees"] = employees
    save_config(config)
    _copy_templates_to_employee(eid)
    return emp


def update_employee_in_config(employee_id: str, owner_id: str, **kwargs) -> dict | None:
    """更新 config 中某员工字段并写回。允许的键：name, persona, role, specialty, businessModule, focus, status。"""
    config = load_config()
    employees = config.get("employees") or []
    allowed = {"name", "persona", "role", "specialty", "businessModule", "focus", "status"}
    for i, e in enumerate(employees):
        if isinstance(e, dict) and e.get("id") == employee_id and e.get("ownerId") == owner_id:
            for k, v in kwargs.items():
                if k in allowed:
                    employees[i][k] = v
            config["employees"] = employees
            save_config(config)
            return employees[i]
    return None


def find_employee_in_config(employee_id: str, owner_id: str | None = None) -> dict | None:
    """从 config 中按 id 查找员工；若传 owner_id 则需匹配 ownerId。"""
    employees = list_employees_from_config(owner_id) if owner_id else list_employees_from_config()
    for e in employees:
        if isinstance(e, dict) and e.get("id") == employee_id:
            return e
    return None
