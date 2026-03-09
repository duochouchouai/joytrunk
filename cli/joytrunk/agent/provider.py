"""OpenAI 兼容的 Chat Completions 调用（支持 tools / tool_calls）。"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import httpx


def _repair_json_arguments(s: str) -> dict[str, Any]:
    """Try to parse JSON; on failure, try stripping trailing commas and retry."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    repaired = re.sub(r",\s*([}\]])", r"\1", s.strip())
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        return {}


def _format_error_body(r: httpx.Response) -> str:
    """从响应中提取错误说明，便于排查 4xx/5xx。"""
    try:
        data = r.json()
        if isinstance(data, dict):
            for key in ("error", "message", "msg", "status_msg"):
                if key in data and data[key]:
                    return str(data[key])
            if "base_resp" in data and isinstance(data["base_resp"], dict):
                br = data["base_resp"]
                return f"status_code={br.get('status_code')} status_msg={br.get('status_msg', '')}"
    except Exception:
        pass
    return r.text[:500] if r.text else (r.reason_phrase or str(r.status_code))


def _sanitize_empty_content(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy messages and set assistant content to empty string when role is assistant and has tool_calls.
    Some backends (e.g. MiniMax) require content to be string, not null."""
    result: list[dict[str, Any]] = []
    for msg in messages:
        if (
            msg.get("role") == "assistant"
            and msg.get("tool_calls")
        ):
            clean = deepcopy(msg)
            clean["content"] = "" if clean.get("content") is None else clean["content"]
            result.append(clean)
        else:
            result.append(deepcopy(msg))
    return result


def _reorder_tool_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """把每条 tool 消息挪到其对应 assistant（含该 tool_call_id）之后，避免 API 2013。"""
    if not messages:
        return messages
    n = len(messages)
    ids_at: list[list[str]] = [[] for _ in range(n)]
    tools: list[tuple[int, str, dict]] = []
    for i, msg in enumerate(messages):
        role = msg.get("role")
        if role == "assistant":
            tcs = msg.get("tool_calls") or []
            ids_at[i] = [tc.get("id") for tc in tcs if isinstance(tc, dict) and tc.get("id")]
        elif role == "tool" and msg.get("tool_call_id"):
            tools.append((i, msg.get("tool_call_id"), msg))
    # tool_index -> 所属 assistant 下标（最后一个包含该 id 的 assistant）
    tool_to_ai: dict[int, int] = {}
    for ti, tid, _ in tools:
        for ai in range(n - 1, -1, -1):
            if tid in ids_at[ai]:
                tool_to_ai[ti] = ai
                break
    out: list[dict[str, Any]] = []
    used: set[int] = set()
    for i, msg in enumerate(messages):
        if msg.get("role") == "tool":
            continue
        out.append(deepcopy(msg))
        if msg.get("role") == "assistant" and ids_at[i]:
            for tid in ids_at[i]:
                for ti, t_tid, t_msg in tools:
                    if ti not in used and t_tid == tid and tool_to_ai.get(ti) == i:
                        out.append(deepcopy(t_msg))
                        used.add(ti)
                        break
    return out


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
            args = _repair_json_arguments(args)
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
        body["tool_choice"] = "auto"
    body["messages"] = _sanitize_empty_content(_reorder_tool_messages(body["messages"]))

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {api_key}"} if api_key else {}),
            },
            json=body,
        )
        if not r.is_success:
            err_detail = _format_error_body(r)
            raise httpx.HTTPStatusError(
                f"API 返回 {r.status_code}: {err_detail}",
                request=r.request,
                response=r,
            )
    return _parse_response(r.json())


async def chat_via_router(
    server_base_url: str,
    owner_id: str,
    model: str,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.1,
    router_api_key: str | None = None,
) -> ChatResponse:
    """通过 server 代理调用 JoyTrunk Router（未配置自有 LLM 时使用）。
    若提供 router_api_key 则发送 Authorization: Bearer，否则仅发送 X-Owner-Id（统一 SK 优先）。
    """
    url = server_base_url.rstrip("/") + "/api/llm/chat/completions"
    body: dict[str, Any] = {
        "model": model or "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = [{"type": "function", "function": t["function"]} for t in tools]
        body["tool_choice"] = "auto"
    body["messages"] = _sanitize_empty_content(_reorder_tool_messages(body["messages"]))

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if router_api_key and router_api_key.strip():
        headers["Authorization"] = f"Bearer {router_api_key.strip()}"
    else:
        headers["X-Owner-Id"] = owner_id

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=body)
        if not r.is_success:
            err_detail = _format_error_body(r)
            raise httpx.HTTPStatusError(
                f"API 返回 {r.status_code}: {err_detail}",
                request=r.request,
                response=r,
            )
    return _parse_response(r.json())
