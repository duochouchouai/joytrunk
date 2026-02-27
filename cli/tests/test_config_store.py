# -*- coding: utf-8 -*-
"""测试 config_store：ensure_owner_id、list/create/update 员工（config.json）。"""

import json

import pytest


def test_ensure_owner_id_creates_and_writes(joytrunk_root):
    from joytrunk.config_store import ensure_owner_id, load_config

    oid = ensure_owner_id()
    assert oid
    assert len(oid) == 36  # uuid4
    config = load_config()
    assert config.get("ownerId") == oid


def test_ensure_owner_id_returns_existing(joytrunk_root):
    from joytrunk.config_store import ensure_owner_id, load_config, save_config

    (joytrunk_root / "config.json").write_text(
        json.dumps({"version": 1, "ownerId": "existing-owner", "employees": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    oid = ensure_owner_id()
    assert oid == "existing-owner"


def test_list_employees_from_config_empty(joytrunk_root):
    from joytrunk.config_store import ensure_owner_id, list_employees_from_config

    ensure_owner_id()
    employees = list_employees_from_config()
    assert employees == []


def test_create_employee_in_config(joytrunk_root):
    from joytrunk.config_store import (
        ensure_owner_id,
        create_employee_in_config,
        list_employees_from_config,
    )

    owner_id = ensure_owner_id()
    emp = create_employee_in_config(owner_id, "测试员工")
    assert emp.get("id")
    assert emp.get("name") == "测试员工"
    assert emp.get("ownerId") == owner_id
    employees = list_employees_from_config(owner_id)
    assert len(employees) == 1
    assert employees[0]["name"] == "测试员工"
    assert (joytrunk_root / "workspace" / "employees" / emp["id"]).exists()


def test_update_employee_in_config(joytrunk_root):
    from joytrunk.config_store import (
        ensure_owner_id,
        create_employee_in_config,
        update_employee_in_config,
        list_employees_from_config,
    )

    owner_id = ensure_owner_id()
    emp = create_employee_in_config(owner_id, "原名")
    eid = emp["id"]
    updated = update_employee_in_config(eid, owner_id, name="新名")
    assert updated is not None
    assert updated["name"] == "新名"
    employees = list_employees_from_config(owner_id)
    assert employees[0]["name"] == "新名"
