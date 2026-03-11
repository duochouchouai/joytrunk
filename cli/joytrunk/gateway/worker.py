"""
Worker: consume MessageBus, call run_employee_loop, write TaskStore (plan 10.4, 10.14).
Runs N concurrent consumers (gateway.worker_concurrency).

与 joytrunk chat 共用同一聊天组件：本 worker 唯一执行入口为 run_employee_loop；
CLI chat 经 A2A 发到本 gateway 时也由此 run_employee_loop 处理，无其他聊天路径。
"""

from __future__ import annotations

import asyncio
import logging

from joytrunk.a2a.models import Message, Part
from joytrunk.agent.loop import run_employee_loop
from joytrunk.bus.events import InboundMessage
from joytrunk.bus.queue import MessageBus, get_default_bus
from joytrunk.gateway.task_store import TaskStore, get_default_task_store

logger = logging.getLogger(__name__)


async def _process_one(inbound: InboundMessage, store: TaskStore) -> None:
    """Run one InboundMessage: run_employee_loop then store.complete."""
    task_id = inbound.task_id
    on_agent_reply = None
    if inbound.channel == "official" and (inbound.chat_id or "").strip():
        from joytrunk.official_ws_client import send_agent_reply_to_official
        conv_id = (inbound.chat_id or "").strip()
        owner_id = inbound.owner_id or ""

        async def _on_reply(employee_id: str, content: str) -> None:
            await send_agent_reply_to_official(conv_id, owner_id, employee_id, content)

        on_agent_reply = _on_reply
    try:
        final_content, usage = await run_employee_loop(
            employee_id=inbound.target_employee_id,
            owner_id=inbound.owner_id,
            content=inbound.content,
            session_key=inbound.session_key,
            channel=inbound.channel,
            chat_id=inbound.chat_id,
            model_override=getattr(inbound, "model", None) or None,
            on_agent_reply=on_agent_reply,
        )
        agent_msg = Message(role="agent", parts=[Part(type="text", text=final_content or "")])
        await store.complete(task_id, "completed", agent_msg, usage=usage)
        if inbound.channel == "official":
            from joytrunk.official_ws_client import send_task_result
            await send_task_result(task_id, "completed", final_content or "", None, usage, inbound.chat_id)
        preview = (final_content or "")[:200]
        if len(final_content or "") > 200:
            preview += "..."
        logger.info("task_id=%s completed reply_len=%d preview=%s", task_id, len(final_content or ""), preview)
    except Exception as e:
        # 502 等 HTTP 错误时打出响应体，便于排查是 Node 还是上游 LLM 的问题
        if hasattr(e, 'response') and e.response is not None:
            try:
                r = e.response
                status = getattr(r, 'status_code', None)
                # 优先用 content，避免 encoding 或未消费 stream 导致 body 为空
                try:
                    body_bytes = getattr(r, 'content', None) or (r.read() if hasattr(r, 'read') else b'')
                except Exception:
                    body_bytes = b''
                if isinstance(body_bytes, bytes):
                    body_preview = body_bytes[:500].decode('utf-8', errors='replace')
                else:
                    body_preview = (getattr(r, 'text', None) or '')[:500]
                logger.error(
                    "Worker run_employee_loop failed task_id=%s status=%s body_len=%s body=%s",
                    task_id,
                    status,
                    len(body_bytes) if isinstance(body_bytes, bytes) else len(body_preview),
                    body_preview or '(empty)',
                )
            except Exception as log_err:
                logger.debug("Worker failed to log response: %s", log_err)
        logger.exception("Worker run_employee_loop failed for task_id=%s", task_id)
        agent_msg = Message(role="agent", parts=[Part(type="text", text="")])
        await store.complete(task_id, "failed", agent_msg, error=str(e))
        if inbound.channel == "official":
            from joytrunk.official_ws_client import send_task_result
            await send_task_result(task_id, "failed", "", str(e), None, inbound.chat_id)


async def run_worker_loop(
    bus: MessageBus | None = None,
    store: TaskStore | None = None,
    concurrency: int = 4,
) -> None:
    """
    Run N worker coroutines consuming from bus, calling run_employee_loop, updating store.
    Plan 10.15: FIFO; concurrency from gateway.worker_concurrency (≤0 -> 1).
    """
    bus = bus or get_default_bus()
    store = store or get_default_task_store()
    n = max(1, concurrency)

    async def consume() -> None:
        while True:
            try:
                inbound = await bus.get()
                await _process_one(inbound, store)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Worker consume error: %s", e)

    workers = [asyncio.create_task(consume()) for _ in range(n)]
    try:
        await asyncio.gather(*workers)
    finally:
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
