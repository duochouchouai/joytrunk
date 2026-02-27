"""员工智能体循环：构建提示（意图+提示词+历史）→ 调用大模型 → 执行 tool_calls → 直至返回最终回复（参考 nanobot.agent.loop）。"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Awaitable, Callable

from joytrunk import paths
from joytrunk.agent.context import ContextBuilder
from joytrunk.agent.employee_config import get_llm_params
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

    messages = context.build_messages(history, content.strip() or "请说你好。", channel=channel, chat_id=chat_id)
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
    return final_content, total_usage if total_usage["prompt_tokens"] or total_usage["completion_tokens"] else None


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
