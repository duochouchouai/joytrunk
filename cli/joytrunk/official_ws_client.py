"""
官方 WebSocket 客户端：连接官网 /ws/cli，鉴权、心跳、收任务入队、上报结果。
与 gateway 同进程运行时可作为任务来源之一；Worker 完成后通过 send_task_result 上报。
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from joytrunk.bus.events import InboundMessage
from joytrunk.bus.queue import get_default_bus

logger = logging.getLogger(__name__)

_ws = None
_lock = asyncio.Lock()
PING_INTERVAL = 30
PONG_TIMEOUT = 60
RECONNECT_BASE = 1
RECONNECT_MAX = 60


def _ws_url_from_base(base: str) -> str:
    base = (base or "").strip().rstrip("/")
    if base.startswith("https://"):
        return base.replace("https://", "wss://", 1) + "/ws/cli"
    if base.startswith("http://"):
        return base.replace("http://", "ws://", 1) + "/ws/cli"
    return "ws://" + base + "/ws/cli"


async def send_task_result(
    task_id: str,
    status: str,
    content: str = "",
    error: str | None = None,
    usage: dict[str, int] | None = None,
    conversation_id: str = "",
) -> None:
    """Worker 完成后调用，将结果发回官网（若已连接）。不依赖 ws.closed（websockets 无此属性），直接尝试发送并捕获异常。"""
    payload = {
        "type": "task_result",
        "task_id": task_id,
        "status": status,
        "content": content or "",
        "usage": usage,
        "conversation_id": conversation_id or "",
    }
    if error:
        payload["error"] = error
    async with _lock:
        if _ws is None:
            logger.warning("official_ws send_task_result skipped: no connection (task_id=%s)", task_id)
            return
        try:
            await _ws.send(json.dumps(payload))
            logger.info("official_ws send_task_result ok task_id=%s conv_id=%s", task_id, conversation_id)
        except Exception as e:
            logger.warning("official_ws send_task_result failed: %s", e)


async def send_agent_reply_to_official(
    conversation_id: str,
    owner_id: str,
    employee_id: str,
    content: str,
) -> None:
    """每次 send_message_to_employee 工具返回后调用，将 agent 回复同步到官网 IM（多 Agent 协作）。"""
    payload = {
        "type": "agent_reply",
        "conversation_id": conversation_id or "",
        "owner_id": owner_id or "",
        "employee_id": employee_id or "",
        "content": content or "",
    }
    async with _lock:
        if _ws is None:
            logger.warning("official_ws send_agent_reply skipped: no connection (conv_id=%s)", conversation_id)
            return
        try:
            await _ws.send(json.dumps(payload))
            logger.info("official_ws send_agent_reply ok conv_id=%s employee_id=%s", conversation_id, employee_id)
        except Exception as e:
            logger.warning("official_ws send_agent_reply failed: %s", e)


async def run_official_ws_client(
    api_key: str,
    base_url: str,
) -> None:
    """长期运行：连接、鉴权、心跳、收任务入队；断线指数退避重连。"""
    import websockets
    from websockets.exceptions import ConnectionClosed

    uri = _ws_url_from_base(base_url)
    bus = get_default_bus()
    backoff = RECONNECT_BASE
    global _ws

    while True:
        try:
            async with websockets.connect(
                uri,
                ping_interval=None,
                ping_timeout=None,
                close_timeout=5,
            ) as ws:
                async with _lock:
                    _ws = ws
                await ws.send(json.dumps({"type": "auth", "api_key": api_key}))
                auth_msg = await asyncio.wait_for(ws.recv(), timeout=15)
                auth_data = json.loads(auth_msg)
                if auth_data.get("type") != "auth_ok":
                    logger.warning("official_ws auth failed: %s", auth_data)
                    async with _lock:
                        _ws = None
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, RECONNECT_MAX)
                    continue
                backoff = RECONNECT_BASE
                logger.info("official_ws connected")
                # 同步当前 CLI 员工列表到云端，供 IM 获取并选择员工下发任务
                try:
                    from joytrunk.config_store import load_config, list_employees_from_config
                    config = load_config()
                    owner_id = (config.get("ownerId") or "").strip()
                    employees = list_employees_from_config(owner_id) if owner_id else []
                    payload = {
                        "type": "employees",
                        "employees": [
                            {"id": (e.get("id") or "").strip(), "name": (e.get("name") or "").strip()}
                            for e in employees
                            if isinstance(e, dict) and (e.get("id") or "").strip()
                        ],
                    }
                    await ws.send(json.dumps(payload))
                except Exception as e:
                    logger.warning("official_ws sync employees failed: %s", e)
                last_ping = time.monotonic()
                last_pong = last_ping

                async def send_ping() -> None:
                    await ws.send(json.dumps({"type": "ping", "ts": int(time.time() * 1000)}))

                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=min(PING_INTERVAL, PONG_TIMEOUT - (time.monotonic() - last_pong)))
                    except asyncio.TimeoutError:
                        if time.monotonic() - last_ping >= PING_INTERVAL:
                            await send_ping()
                            last_ping = time.monotonic()
                        if time.monotonic() - last_pong > PONG_TIMEOUT:
                            raise ConnectionClosed(None, None)
                        continue
                    data = json.loads(msg) if isinstance(msg, str) else json.loads(msg.decode("utf-8"))
                    if data.get("type") == "pong":
                        last_pong = time.monotonic()
                        continue
                    if data.get("type") == "task":
                        task_id = data.get("task_id") or ""
                        owner_id = str(data.get("owner_id", ""))
                        employee_id = str(data.get("employee_id", ""))
                        content = str(data.get("content", ""))
                        session_key = str(data.get("session_key", "owner"))
                        conversation_id = str(data.get("conversation_id", "direct"))
                        model = (data.get("model") or "").strip() or None
                        inbound = InboundMessage(
                            task_id=task_id,
                            target_employee_id=employee_id,
                            owner_id=owner_id,
                            content=content,
                            session_key=session_key,
                            channel="official",
                            chat_id=conversation_id,
                            model=model,
                        )
                        await bus.put(inbound)
                        logger.info("official_ws enqueued task %s", task_id)
        except (ConnectionClosed, ConnectionError, OSError) as e:
            logger.warning("official_ws disconnected: %s", e)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("official_ws error: %s", e)
        finally:
            async with _lock:
                _ws = None
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, RECONNECT_MAX)
