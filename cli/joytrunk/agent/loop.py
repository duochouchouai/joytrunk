"""员工智能体循环：构建提示（意图+提示词+历史）→ 调用大模型 → 执行 tool_calls → 直至返回最终回复（参考 nanobot.agent.loop）。"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable

from joytrunk import paths
from joytrunk.agent.context import ContextBuilder
from joytrunk.agent.employee_config import get_llm_params
from joytrunk.agent.provider import chat as provider_chat, chat_via_router
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

    iteration = 0
    final_content = None
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0}

    while iteration < MAX_ITERATIONS:
        iteration += 1
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

        if response.has_tool_calls:
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
                context.add_tool_result(messages, tc.id, tc.name, result)
            if on_progress:
                hint = ", ".join(f'{tc.name}(...)' for tc in response.tool_calls)
                await _safe_progress(on_progress, f"[工具调用: {hint}]")
        else:
            final_content = (response.content or "").strip()
            break

    if final_content is None:
        final_content = (
            f"已达到最大工具调用轮数（{MAX_ITERATIONS}），任务未完成。可将任务拆成更小步骤重试。"
        )

    append_turn(employee_id, session_key, messages, skip_count)
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
