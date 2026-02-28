"""员工智能体循环：构建提示（意图+提示词+历史）→ 调用大模型 → 执行 tool_calls → 直至返回最终回复（参考 nanobot.agent.loop）。"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Awaitable, Callable

from joytrunk import paths
from joytrunk.agent.context import ContextBuilder
from joytrunk.agent.employee_config import get_llm_params, get_memory_config
from joytrunk.agent.provider import chat as provider_chat, chat_via_router
from joytrunk.agent.run_log import (
    EVENT_APPEND_TURN_DONE,
    EVENT_FINAL_REPLY,
    EVENT_ITERATION,
    EVENT_LLM_REQUEST,
    EVENT_LLM_RESPONSE,
    EVENT_LOOP_DONE,
    EVENT_LOOP_START,
    EVENT_MAX_ITERATIONS,
    EVENT_TOOL_CALLS,
    EVENT_TOOL_RESULT,
    MAX_RESPONSE_CONTENT_LEN,
    MAX_TOOL_RESULT_LEN,
    log as run_log,
    prepare_messages_for_log,
    truncate_str,
)
from joytrunk.agent.session import append_turn, load_history
from joytrunk.tools import create_default_registry

MAX_ITERATIONS = 40
MEMORY_WINDOW = 50


async def run_employee_loop(
    employee_id: str,
    owner_id: str,
    content: str,
    session_key: str = "cli:direct",
    channel: str = "cli",
    chat_id: str = "direct",
    on_progress: Callable[[str], Awaitable[None]] | None = None,
) -> tuple[str, dict[str, int] | None]:
    """
    运行员工智能体循环：意图 + 自身提示词 + 历史 → 大模型（自有或 JoyTrunk Router）→ 对返回的 tool_calls 执行 → 再问大模型直至无 tool_calls。
    返回 (最终回复文本, usage 或 None)。
    """
    params = get_llm_params(employee_id, owner_id)
    model = params["model"]
    max_tokens = params["max_tokens"]
    temperature = params["temperature"]

    workspace = paths.get_employee_dir(employee_id)
    context = ContextBuilder(employee_id)
    tools_reg = create_default_registry(workspace, employee_id, restrict_to_workspace=True)

    history = load_history(employee_id, session_key)
    history = history[-MEMORY_WINDOW:] if len(history) > MEMORY_WINDOW else history

    memory_cfg = get_memory_config(employee_id)
    embed_client, llm_chat_fn = _memory_clients(employee_id, owner_id, params, memory_cfg)
    if embed_client or llm_chat_fn:
        messages = await context.build_messages_with_memory(
            history, content.strip() or "请说你好。", channel=channel, chat_id=chat_id,
            embed_client=embed_client, llm_chat=llm_chat_fn,
        )
    else:
        messages = context.build_messages(
            history, content.strip() or "请说你好。", channel=channel, chat_id=chat_id,
        )
    # 本轮要落盘的消息从「当前 turn 的第一个 user（runtime）消息」开始
    skip_count = 1 + len(history)

    run_id = uuid.uuid4().hex
    run_log(
        employee_id,
        EVENT_LOOP_START,
        {
            "session_key": session_key,
            "channel": channel,
            "chat_id": chat_id,
            "history_len": len(history),
            "user_message_preview": (content.strip() or "")[:300],
        },
        run_id=run_id,
    )

    iteration = 0
    final_content = None
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0}

    while iteration < MAX_ITERATIONS:
        iteration += 1
        run_log(
            employee_id,
            EVENT_ITERATION,
            {"iteration": iteration, "model": model, "messages_count": len(messages)},
            run_id=run_id,
        )
        run_log(
            employee_id,
            EVENT_LLM_REQUEST,
            {
                "iteration": iteration,
                "model": model,
                "messages_count": len(messages),
                "messages": prepare_messages_for_log(messages),
            },
            run_id=run_id,
        )
        if params["source"] == "custom":
            response = await provider_chat(
                params["base_url"],
                params["api_key"],
                model,
                messages,
                tools=tools_reg.get_definitions(),
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            response = await chat_via_router(
                params["gateway_base_url"],
                params["owner_id"],
                model,
                messages,
                tools=tools_reg.get_definitions(),
                max_tokens=max_tokens,
                temperature=temperature,
            )
        if response.usage:
            total_usage["prompt_tokens"] += response.usage.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += response.usage.get("completion_tokens", 0)

        run_log(
            employee_id,
            EVENT_LLM_RESPONSE,
            {
                "iteration": iteration,
                "content": truncate_str(response.content or "", MAX_RESPONSE_CONTENT_LEN),
                "content_len": len(response.content or ""),
                "tool_calls": [
                    {"name": tc.name, "arguments": tc.arguments}
                    for tc in response.tool_calls
                ],
                "usage": dict(response.usage) if response.usage else None,
            },
            run_id=run_id,
        )

        if response.has_tool_calls:
            run_log(
                employee_id,
                EVENT_TOOL_CALLS,
                {"iteration": iteration, "tool_names": [tc.name for tc in response.tool_calls]},
                run_id=run_id,
            )
            if on_progress and response.content:
                await _safe_progress(on_progress, response.content.strip())
            tool_call_dicts = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                }
                for tc in response.tool_calls
            ]
            context.add_assistant_message(messages, response.content, tool_call_dicts)
            for tc in response.tool_calls:
                result = await tools_reg.execute(tc.name, tc.arguments)
                run_log(
                    employee_id,
                    EVENT_TOOL_RESULT,
                    {
                        "tool_name": tc.name,
                        "result_len": len(result),
                        "result": truncate_str(result, MAX_TOOL_RESULT_LEN),
                    },
                    run_id=run_id,
                )
                context.add_tool_result(messages, tc.id, tc.name, result)
            if on_progress:
                hint = ", ".join(f'{tc.name}(...)' for tc in response.tool_calls)
                await _safe_progress(on_progress, f"[工具调用: {hint}]")
        else:
            final_content = (response.content or "").strip()
            run_log(
                employee_id,
                EVENT_FINAL_REPLY,
                {
                    "reply_len": len(final_content),
                    "content": truncate_str(final_content, MAX_RESPONSE_CONTENT_LEN),
                },
                run_id=run_id,
            )
            break

    if final_content is None:
        final_content = (
            f"已达到最大工具调用轮数（{MAX_ITERATIONS}），任务未完成。可将任务拆成更小步骤重试。"
        )
        run_log(employee_id, EVENT_MAX_ITERATIONS, {"reason": "max_iterations_reached"}, run_id=run_id)

    run_log(
        employee_id,
        EVENT_LOOP_DONE,
        {
            "reply_len": len(final_content or ""),
            "content": truncate_str(final_content or "", MAX_RESPONSE_CONTENT_LEN),
            "usage": {
                "prompt_tokens": total_usage["prompt_tokens"],
                "completion_tokens": total_usage["completion_tokens"],
            },
        },
        run_id=run_id,
    )
    append_turn(employee_id, session_key, messages, skip_count)
    run_log(employee_id, EVENT_APPEND_TURN_DONE, {}, run_id=run_id)
    if memory_cfg.get("auto_extract") and (embed_client or llm_chat_fn):
        try:
            from joytrunk.agent.memory.memorize import run_memorize
            await run_memorize(
                employee_id,
                messages[skip_count:],
                llm_chat=llm_chat_fn,
                embed_client=embed_client or _dummy_embed_client(),
                memory_types=memory_cfg.get("types") or ["profile", "event"],
                enable_reinforcement=True,
            )
        except Exception as e:
            run_log(employee_id, "memory_memorize_error", {"error": str(e)}, run_id=run_id)
    return final_content, total_usage if total_usage["prompt_tokens"] or total_usage["completion_tokens"] else None


def _dummy_embed_client() -> Any:
    """占位 embed：返回零向量，避免 memorize 因无 embed 报错。"""
    class Dummy:
        async def embed(self, inputs: list[str]) -> list[list[float]]:
            return [[0.0] * 384 for _ in inputs]
    return Dummy()


def _memory_clients(employee_id: str, owner_id: str, llm_params: dict, memory_cfg: dict) -> tuple[Any, Any]:
    embed_client = None
    emb = (memory_cfg.get("embedding") or {})
    base_url = emb.get("base_url") or llm_params.get("base_url")
    api_key = emb.get("api_key") or llm_params.get("api_key")
    embed_model = emb.get("embed_model") or "embo-01"
    if base_url and embed_model:
        from joytrunk.agent.memory.embedding_client import HTTPEmbeddingClient
        embed_client = HTTPEmbeddingClient(
            base_url=base_url, api_key=api_key or "", embed_model=embed_model,
        )
    async def llm_chat(messages: list[dict]) -> str:
        from joytrunk.agent.provider import chat as provider_chat, chat_via_router
        if llm_params["source"] == "custom":
            r = await provider_chat(
                llm_params["base_url"], llm_params["api_key"], llm_params["model"], messages,
                max_tokens=llm_params.get("max_tokens", 2048), temperature=llm_params.get("temperature", 0.1),
            )
        else:
            r = await chat_via_router(
                llm_params["gateway_base_url"], llm_params["owner_id"], llm_params["model"], messages,
                max_tokens=llm_params.get("max_tokens", 2048), temperature=llm_params.get("temperature", 0.1),
            )
        return (r.content or "").strip()
    return embed_client, llm_chat


async def _safe_progress(
    fn: Callable[[str], Awaitable[None]] | None, text: str
) -> None:
    if not fn:
        return
    try:
        if asyncio.iscoroutinefunction(fn):
            await fn(text)
        else:
            fn(text)
    except Exception:
        pass
