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
        """解析 embedding 响应。支持 OpenAI 格式 data[].embedding 与 MiniMax 等 data[] 为向量数组或 embeddings 键。"""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data).__name__}")
        # OpenAI: {"data": [{"embedding": [...]}, ...]}
        if "data" in data:
            raw = data["data"]
            if not isinstance(raw, list):
                raise ValueError(f"response['data'] must be a list, got {type(raw).__name__}")
            out: list[list[float]] = []
            for i, item in enumerate(raw):
                if isinstance(item, dict) and "embedding" in item:
                    out.append(list(item["embedding"]))
                elif isinstance(item, list) and item and isinstance(item[0], (int, float)):
                    out.append([float(x) for x in item])
                else:
                    raise ValueError(f"response['data'][{i}] must be {{'embedding': [...]}} or list of numbers, got {type(item).__name__}")
            return out
        # MiniMax 等可能用 "embeddings" 键：[[...], [...]]
        if "embeddings" in data:
            raw = data["embeddings"]
            if not isinstance(raw, list):
                raise ValueError(f"response['embeddings'] must be a list, got {type(raw).__name__}")
            return [list(vec) if isinstance(vec, list) else list(vec) for vec in raw]
        # 部分接口用 "vectors" 键
        if "vectors" in data:
            raw = data["vectors"]
            if not isinstance(raw, list):
                raise ValueError(f"response['vectors'] must be a list, got {type(raw).__name__}")
            return [list(vec) if isinstance(vec, list) else list(vec) for vec in raw]
        logger.warning(
            "Embedding response missing 'data'/'embeddings'/'vectors'; keys: %s",
            list(data.keys()),
        )
        raise KeyError(
            "Expected 'data', 'embeddings' or 'vectors' in embedding response; "
            f"got keys: {list(data.keys())}"
        )


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
