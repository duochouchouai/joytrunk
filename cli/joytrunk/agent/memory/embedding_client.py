"""Embedding 客户端（OpenAI 兼容 /embeddings）。"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class EmbeddingBackend:
    """单一样本：OpenAI 兼容。"""

    embedding_endpoint = "/embeddings"

    def build_payload(self, *, inputs: list[str], embed_model: str) -> dict[str, Any]:
        return {"model": embed_model, "input": inputs}

    def parse_response(self, data: dict[str, Any]) -> list[list[float]]:
        return [list(d["embedding"]) for d in data["data"]]


class HTTPEmbeddingClient:
    """调用 OpenAI 兼容 POST /embeddings。"""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        embed_model: str,
        timeout: int = 60,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/") + "/"
        self.api_key = api_key or ""
        self.embed_model = embed_model
        self.timeout = timeout
        self._backend = EmbeddingBackend()

    async def embed(self, inputs: list[str]) -> list[list[float]]:
        if not inputs:
            return []
        payload = self._backend.build_payload(inputs=inputs, embed_model=self.embed_model)
        endpoint = self._backend.embedding_endpoint.lstrip("/")
        url = self.base_url + endpoint
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
        return self._backend.parse_response(r.json())


__all__ = ["HTTPEmbeddingClient", "EmbeddingBackend"]
