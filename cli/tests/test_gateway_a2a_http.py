# -*- coding: utf-8 -*-
"""A2A HTTP 边界层（方案 10.1、10.6、10.16、10.24）：入站解析、路径、错误码、Get Task。"""

import asyncio
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from joytrunk.gateway.a2a_http import (
    _check_employee_in_owner,
    _parse_send_body,
    app,
    create_app,
)


def test_parse_send_body_valid():
    body = {
        "message": {"role": "user", "parts": [{"type": "text", "text": "hello"}], "contextId": "ctx-1"},
        "configuration": {"blocking": True},
        "metadata": {"channel": "cli"},
    }
    req = _parse_send_body(body)
    assert req.message.role == "user"
    assert len(req.message.parts) == 1
    assert req.message.parts[0].text == "hello"
    assert req.message.context_id == "ctx-1"
    assert req.configuration.blocking is True
    assert req.metadata["channel"] == "cli"


def test_parse_send_body_missing_message_raises():
    with pytest.raises(ValueError, match="message required"):
        _parse_send_body({})
    with pytest.raises(ValueError, match="message required"):
        _parse_send_body({"message": None})


def test_parse_send_body_non_text_part_raises():
    body = {"message": {"role": "user", "parts": [{"type": "file", "url": "x"}]}}
    with pytest.raises(ValueError, match="Only text parts supported"):
        _parse_send_body(body)


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_check_employee_in_owner_empty_returns_false(mock_list):
    mock_list.return_value = []
    assert _check_employee_in_owner("o1", "e1") is False


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_check_employee_in_owner_not_in_list_returns_false(mock_list):
    mock_list.return_value = [{"id": "e2", "name": "B"}]
    assert _check_employee_in_owner("o1", "e1") is False


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_check_employee_in_owner_in_list_returns_true(mock_list):
    mock_list.return_value = [{"id": "e1", "name": "A"}]
    assert _check_employee_in_owner("o1", "e1") is True


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_employees():
    return [{"id": "emp-1", "name": "Employee 1", "ownerId": "owner-1"}]


def test_message_send_invalid_json(client):
    r = client.post(
        "/a2a/v1/tenants/owner-1/employees/emp-1/message:send",
        content="not json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400
    assert "error" in r.json()


def test_message_send_missing_message(client):
    r = client.post(
        "/a2a/v1/tenants/owner-1/employees/emp-1/message:send",
        json={},
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_message_send_employee_not_found_404(mock_list, client):
    mock_list.return_value = []
    r = client.post(
        "/a2a/v1/tenants/owner-1/employees/emp-1/message:send",
        json={"message": {"role": "user", "parts": [{"type": "text", "text": "hi"}]}, "configuration": {"blocking": False}},
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 404
    assert "TaskNotFoundError" in str(r.json())


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_message_send_role_not_user_400(mock_list, client):
    mock_list.return_value = [{"id": "emp-1"}]
    r = client.post(
        "/a2a/v1/tenants/owner-1/employees/emp-1/message:send",
        json={"message": {"role": "agent", "parts": [{"type": "text", "text": "hi"}]}, "configuration": {"blocking": False}},
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400
    assert "role" in str(r.json().get("error", "")).lower()


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_get_task_not_found_404(mock_list, client):
    mock_list.return_value = []
    r = client.get("/a2a/v1/tenants/owner-1/tasks/nonexistent-task-id")
    assert r.status_code == 404
    assert "TaskNotFoundError" in str(r.json())


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_message_send_non_blocking_returns_working_task(mock_list, client):
    """Send Message blocking=false：入队后立即返回 working 的 Task（无 worker 时保持 working）。"""
    mock_list.return_value = [{"id": "emp-1"}]
    r = client.post(
        "/a2a/v1/tenants/owner-1/employees/emp-1/message:send",
        json={
            "message": {"role": "user", "parts": [{"type": "text", "text": "hello"}]},
            "configuration": {"blocking": False},
        },
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "working"
    assert "id" in data
    assert data["contextId"]  # 有 contextId（或服务端生成的）
    assert len(data["history"]) == 1
    assert data["history"][0]["role"] == "user"


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_get_task_wrong_owner_404(mock_list, client):
    """Get Task 时 task.owner_id 与 path 的 tenant 不一致 → 404（10.24）。"""
    mock_list.return_value = [{"id": "emp-1"}]
    send_r = client.post(
        "/a2a/v1/tenants/owner-A/employees/emp-1/message:send",
        json={"message": {"role": "user", "parts": [{"type": "text", "text": "x"}]}, "configuration": {"blocking": False}},
        headers={"Content-Type": "application/json"},
    )
    assert send_r.status_code == 200
    task_id = send_r.json()["id"]
    r = client.get(f"/a2a/v1/tenants/owner-B/tasks/{task_id}")
    assert r.status_code == 404


@patch("joytrunk.gateway.a2a_http.list_employees_from_config")
def test_message_send_from_employee_id_not_in_tenant_403(mock_list, client):
    """from_employee_id 与 target 不同属同一 owner → 403（10.9）。"""
    def side_effect(owner_id):
        if owner_id == "owner-1":
            return [{"id": "emp-1"}]
        return []
    mock_list.side_effect = side_effect
    r = client.post(
        "/a2a/v1/tenants/owner-1/employees/emp-1/message:send",
        json={
            "message": {"role": "user", "parts": [{"type": "text", "text": "hi"}]},
            "configuration": {"blocking": False},
            "metadata": {"from_employee_id": "other-emp"},
        },
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 403
    assert "from_employee_id" in str(r.json().get("error", ""))
