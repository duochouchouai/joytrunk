"""Web search tool (Brave Search API). Only registered when BRAVE_API_KEY is set."""

from __future__ import annotations

import os
from typing import Any

import httpx

from joytrunk.tools.base import Tool


class WebSearchTool(Tool):
    """Search the web using Brave Search API."""

    def __init__(self, api_key: str | None = None, max_results: int = 5):
        self._api_key = api_key or os.environ.get("BRAVE_API_KEY", "")
        self._max_results = max_results

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web. Returns titles, URLs, and snippets. Use when you need up-to-date or external information."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "count": {"type": "integer", "description": "Number of results (1-10)", "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
        }

    async def execute(self, query: str, count: int | None = None, **kwargs: Any) -> str:
        if not self._api_key:
            return (
                "Error: Brave Search API key not configured. "
                "Set BRAVE_API_KEY in environment (or in config) to enable web_search."
            )
        try:
            n = min(max(count or self._max_results, 1), 10)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": n},
                    headers={"Accept": "application/json", "X-Subscription-Token": self._api_key},
                )
                r.raise_for_status()
            data = r.json()
            results = data.get("web", {}).get("results", [])
            if not results:
                return f"No results for: {query}"
            lines = [f"Results for: {query}\n"]
            for i, item in enumerate(results[:n], 1):
                lines.append(f"{i}. {item.get('title', '')}\n   {item.get('url', '')}")
                if desc := item.get("description"):
                    lines.append(f"   {desc}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"
