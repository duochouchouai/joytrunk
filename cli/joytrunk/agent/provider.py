"""OpenAI 兼容的 Chat Completions 调用（支持 tools / tool_calls）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ChatResponse:
    content: str
    usage: dict[str, int] | None
    tool_calls: list[ToolCall]
    reasoning_content: str | None = None

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


def _parse_response(data: dict) -> ChatResponse:
    choice = (data.get("choices") or [None])[0]
    if not choice:
        return ChatResponse(content="", usage=None, tool_calls=[])
    msg = choice.get("message") or {}
    content = msg.get("content") or ""
    usage = None
    if data.get("usage"):
        usage = {
            "prompt_tokens": data["usage"].get("prompt_tokens", 0),
            "completion_tokens": data["usage"].get("completion_tokens", 0),
        }
    tool_calls: list[ToolCall] = []
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function") or {}
        args = fn.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        if not isinstance(args, dict):
            args = {}
        tool_calls.append(
            ToolCall(
                id=tc.get("id") or "",
                name=fn.get("name") or "",
                arguments=args,
            )
        )
    return ChatResponse(
        content=content or "",
        usage=usage,
        tool_calls=tool_calls,
        reasoning_content=msg.get("reasoning_content"),
    )


async def chat(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.1,
) -> ChatResponse:
    """调用 OpenAI 兼容 POST /v1/chat/completions，支持 tools。"""
    url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    body: dict[str, Any] = {
        "model": model or "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = [{"type": "function", "function": t["function"]} for t in tools]

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {api_key}"} if api_key else {}),
            },
            json=body,
        )
        r.raise_for_status()
    return _parse_response(r.json())


async def chat_via_router(
    gateway_base_url: str,
    owner_id: str,
    model: str,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.1,
) -> ChatResponse:
    """通过 gateway 代理调用 JoyTrunk Router（未配置自有 LLM 时使用）。"""
    url = gateway_base_url.rstrip("/") + "/api/llm/chat/completions"
    body: dict[str, Any] = {
        "model": model or "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = [{"type": "function", "function": t["function"]} for t in tools]

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                "X-Owner-Id": owner_id,
            },
            json=body,
        )
        r.raise_for_status()
    return _parse_response(r.json())
