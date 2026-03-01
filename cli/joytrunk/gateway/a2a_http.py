"""
A2A HTTP boundary (plan §7): parse A2A requests, enqueue to bus, return A2A responses.
Paths: POST .../tenants/{owner_id}/employees/{employee_id}/message:send, GET .../tenants/{owner_id}/tasks/{task_id}.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from joytrunk.a2a.models import (
    Message,
    Part,
    SendMessageConfiguration,
    SendMessageRequest,
    Task,
    part_to_text,
    task_to_dict,
)
from joytrunk.bus.events import InboundMessage
from joytrunk.bus.queue import get_default_bus
from joytrunk.config_store import list_employees_from_config
from joytrunk.gateway.task_store import get_default_task_store
from joytrunk.gateway.worker import run_worker_loop

# Config defaults (set by create_app or a2a_server)
BLOCKING_TIMEOUT_SECONDS = 300
WORKER_CONCURRENCY = 4

app = FastAPI(title="JoyTrunk A2A Gateway", version="0.1.0")


def create_app(
    blocking_timeout_seconds: int = 300,
    worker_concurrency: int = 4,
    task_store_ttl_seconds: int = 86400,
    task_store_cleanup_interval_seconds: int = 60,
) -> FastAPI:
    """Create FastAPI app with lifespan that starts the worker (plan 2.1)."""
    global BLOCKING_TIMEOUT_SECONDS, WORKER_CONCURRENCY
    BLOCKING_TIMEOUT_SECONDS = blocking_timeout_seconds
    WORKER_CONCURRENCY = max(1, worker_concurrency)
    store = get_default_task_store(
        ttl_seconds=task_store_ttl_seconds,
        cleanup_interval_seconds=task_store_cleanup_interval_seconds,
    )
    bus = get_default_bus()
    worker_task: asyncio.Task | None = None

    @asynccontextmanager
    async def lifespan(fastapi_app: FastAPI):
        nonlocal worker_task
        worker_task = asyncio.create_task(
            run_worker_loop(bus=bus, store=store, concurrency=WORKER_CONCURRENCY)
        )
        yield
        if worker_task:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

    out = FastAPI(title="JoyTrunk A2A Gateway", version="0.1.0", lifespan=lifespan)
    out.post("/a2a/v1/tenants/{owner_id}/employees/{employee_id}/message:send")(message_send)
    out.get("/a2a/v1/tenants/{owner_id}/tasks/{task_id}")(get_task)
    return out


def _parse_send_body(body: dict) -> SendMessageRequest:
    """Build SendMessageRequest from JSON body."""
    msg = body.get("message")
    if not msg or not isinstance(msg, dict):
        raise ValueError("message required")
    role = msg.get("role", "user")
    parts_raw = msg.get("parts") or []
    parts = []
    for p in parts_raw:
        if not isinstance(p, dict):
            continue
        t = p.get("type", "text")
        if t != "text":
            raise ValueError("Only text parts supported")
        parts.append(Part(type="text", text=p.get("text") or ""))
    configuration = None
    if body.get("configuration") and isinstance(body["configuration"], dict):
        cfg = body["configuration"]
        configuration = SendMessageConfiguration(
            blocking=cfg.get("blocking", False),
            history_length=cfg.get("historyLength"),
        )
    metadata = body.get("metadata") or {}
    return SendMessageRequest(
        message=Message(role=role, parts=parts, context_id=msg.get("contextId")),
        configuration=configuration,
        metadata=metadata,
    )


def _check_employee_in_owner(owner_id: str, employee_id: str) -> bool:
    """Plan 10.24: list_employees_from_config(owner_id) empty -> 404; employee not in list -> 404."""
    employees = list_employees_from_config(owner_id)
    if not employees:
        return False
    return any(e.get("id") == employee_id for e in employees)


@app.post("/a2a/v1/tenants/{owner_id}/employees/{employee_id}/message:send")
async def message_send(
    owner_id: str,
    employee_id: str,
    request: Request,
) -> Response:
    """A2A Send Message. Plan 10.6 path; 10.1 conversion; 10.4 blocking."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    try:
        req = _parse_send_body(body)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    if not _check_employee_in_owner(owner_id, employee_id):
        return JSONResponse(status_code=404, content={"error": "TaskNotFoundError"})
    from_employee_id = req.metadata.get("from_employee_id")
    if from_employee_id is not None and not _check_employee_in_owner(owner_id, from_employee_id):
        return JSONResponse(status_code=403, content={"error": "from_employee_id not in same tenant"})
    if req.message.role != "user":
        return JSONResponse(status_code=400, content={"error": "message.role must be user"})
    content = part_to_text(req.message.parts)
    context_id = req.message.context_id or str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    blocking = req.configuration.blocking if req.configuration else False
    store = get_default_task_store()
    bus = get_default_bus()
    user_message = Message(
        role="user",
        parts=req.message.parts,
        context_id=context_id,
    )
    task = await store.create(task_id, owner_id, context_id, user_message)
    inbound = InboundMessage(
        task_id=task_id,
        target_employee_id=employee_id,
        owner_id=owner_id,
        content=content,
        session_key=context_id,
        channel=req.metadata.get("channel", "web"),
        chat_id=req.metadata.get("chat_id", "direct"),
        from_employee_id=from_employee_id,
    )
    await bus.put(inbound)
    timeout = BLOCKING_TIMEOUT_SECONDS
    if blocking and timeout > 0:
        result = await store.wait_done(task_id, float(timeout))
        if result:
            task = result
    else:
        task = await store.get(task_id) or task
    return JSONResponse(content=task_to_dict(task))


@app.get("/a2a/v1/tenants/{owner_id}/tasks/{task_id}")
async def get_task(owner_id: str, task_id: str) -> Response:
    """A2A Get Task. Plan 10.5, 10.24: task.owner_id must match request tenant."""
    store = get_default_task_store()
    task = await store.get(task_id)
    if not task:
        return JSONResponse(status_code=404, content={"error": "TaskNotFoundError"})
    if task.owner_id != owner_id:
        return JSONResponse(status_code=404, content={"error": "TaskNotFoundError"})
    return JSONResponse(content=task_to_dict(task))
