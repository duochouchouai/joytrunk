"""Embedding 客户端（OpenAI 兼容 /embeddings）。"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class EmbeddingBackend:
    """单一样本：OpenAI 兼容。"""

    embedding_endpoint = "/embeddings"

    # base_resp 或非标准响应中可能出现的向量列表键（按优先级尝试）
    _VECTOR_LIST_KEYS = ("data", "embeddings", "vectors", "embedding_sentences", "result", "output", "outputs")

    # 常见错误信息键（顶层或 base_resp 内）
    _ERROR_KEYS = ("status_msg", "message", "error", "msg", "err_msg")

    @staticmethod
    def _extract_api_error(data: dict[str, Any], prefix: str = "") -> str:
        """从响应中提取 API 返回的错误信息，用于拼到异常文案。"""
        if not isinstance(data, dict):
            return ""
        parts: list[str] = []
        code = data.get("status_code")
        if code is not None and code != 0 and code != 200:
            parts.append(f"status_code={code}")
        for key in EmbeddingBackend._ERROR_KEYS:
            val = data.get(key)
            if val is not None and isinstance(val, str) and val.strip():
                parts.append(val.strip())
                break
        if not parts:
            err = data.get("error")
            if isinstance(err, dict) and err.get("message"):
                parts.append(str(err.get("message", "")))
        return f"{prefix}{'; '.join(parts)}" if parts else ""

    def _try_parse_vector_list(self, raw: Any) -> list[list[float]] | None:
        """若 raw 为「向量列表」或 data 格式则返回 list[list[float]]，否则返回 None。"""
        if raw is None or not isinstance(raw, list):
            return None
        out: list[list[float]] = []
        for i, item in enumerate(raw):
            if isinstance(item, list) and item and isinstance(item[0], (int, float)):
                out.append([float(x) for x in item])
            elif isinstance(item, dict) and "embedding" in item:
                out.append(list(item["embedding"]))
            else:
                return None
        return out if out else None

    def build_payload(
        self,
        *,
        inputs: list[str],
        embed_model: str,
        input_key: str = "input",
        embed_type: str | None = None,
    ) -> dict[str, Any]:
        """请求体：model + 文本列表。MiniMax 还需 type：query（检索）或 db（入库）。"""
        payload: dict[str, Any] = {"model": embed_model, input_key: inputs}
        if embed_type in ("query", "db"):
            payload["type"] = embed_type
        return payload

    def parse_response(self, data: dict[str, Any]) -> list[list[float]]:
        """解析 embedding 响应。支持 OpenAI 格式 data[].embedding 与 MiniMax 等 data[] 为向量数组或 embeddings 键。"""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data).__name__}")
        # OpenAI: {"data": [{"embedding": [...]}, ...]}
        if "data" in data:
            raw = data["data"]
            if raw is None:
                raise ValueError(
                    "response['data'] is null; the embedding API may have returned an error or unsupported format. "
                    "Check the embedding endpoint and model (e.g. embed_model in memory config)."
                )
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
            if raw is None:
                raise ValueError(
                    "response['embeddings'] is null; check the embedding endpoint and model."
                )
            if not isinstance(raw, list):
                raise ValueError(f"response['embeddings'] must be a list, got {type(raw).__name__}")
            return [list(vec) if isinstance(vec, list) else list(vec) for vec in raw]
        # 部分接口用 "vectors" 键；若为 null 则尝试从 base_resp 解析（如部分国产 API）
        if "vectors" in data:
            raw = data["vectors"]
            if raw is not None:
                if not isinstance(raw, list):
                    raise ValueError(f"response['vectors'] must be a list, got {type(raw).__name__}")
                return [list(vec) if isinstance(vec, list) else list(vec) for vec in raw]
            if "base_resp" in data and isinstance(data.get("base_resp"), dict):
                base = data["base_resp"]
                try:
                    return self.parse_response(base)
                except (ValueError, KeyError):
                    pass
                # base_resp 可能用其他键存放向量列表
                for key in self._VECTOR_LIST_KEYS:
                    if key in base:
                        parsed = self._try_parse_vector_list(base[key])
                        if parsed is None and key == "data" and isinstance(base.get("data"), list):
                            # data 可能是 [{"embedding": [...]}, ...]
                            parsed = self._try_parse_vector_list(
                                [x.get("embedding") if isinstance(x, dict) else x for x in base["data"]]
                            )
                        if parsed:
                            return parsed
                api_err = self._extract_api_error(base, "base_resp: ") or self._extract_api_error(data, "")
                hint = f" {api_err}" if api_err else ""
                raise ValueError(
                    "response['vectors'] is null and response['base_resp'] could not be parsed as embedding result."
                    + hint
                    + " Check the embedding endpoint and model (e.g. embed_model in memory config)."
                )
            api_err = self._extract_api_error(data, "") or self._extract_api_error(
                data.get("base_resp") if isinstance(data.get("base_resp"), dict) else {}, "base_resp: "
            )
            hint = f" API returned: {api_err}" if api_err else ""
            logger.warning(
                "Embedding response has 'vectors' key but value is null. Keys: %s%s",
                list(data.keys()),
                f"; {api_err}" if api_err else "",
            )
            raise ValueError(
                "response['vectors'] is null; the embedding API may not support this model or returned an error."
                + hint
                + " Check the embedding endpoint and model name (e.g. embed_model in memory config)."
            )
        # 无标准 embedding 字段时，先识别错误响应（status_code/status_msg），再报缺字段
        if "status_code" in data or "status_msg" in data:
            code = data.get("status_code", "")
            msg = data.get("status_msg", "")
            raise ValueError(
                f"Embedding API returned an error: {msg or 'unknown'} (status_code: {code}). "
                "Check the embedding endpoint, model name (embed_model), and API key."
            )
        logger.warning(
            "Embedding response missing 'data'/'embeddings'/'vectors'; keys: %s",
            list(data.keys()),
        )
        raise KeyError(
            "Expected 'data', 'embeddings' or 'vectors' in embedding response; "
            f"got keys: {list(data.keys())}"
        )


class HTTPEmbeddingClient:
    """调用 OpenAI 兼容 POST /embeddings；MiniMax 需请求体 texts、type 及 URL 参数 GroupId。"""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        embed_model: str,
        timeout: int = 60,
        input_key: str | None = None,
        group_id: str | None = None,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/") + "/"
        self.api_key = api_key or ""
        self.embed_model = embed_model
        self.timeout = timeout
        self._group_id = (group_id or "").strip()
        self._backend = EmbeddingBackend()
        # MiniMax 要求请求体为 texts；未指定时按 base_url / model 推断
        if input_key is not None:
            self._input_key = input_key
        elif embed_model == "embo-01" or "minimax" in (base_url or "").lower():
            self._input_key = "texts"
        else:
            self._input_key = "input"
        if self._input_key == "texts" and not self._group_id:
            logger.warning(
                "MiniMax embedding mode but group_id is not set; API may return 2013. "
                "Set memory.embedding.group_id in config or MINIMAX_GROUP_ID env."
            )

    async def embed(
        self, inputs: list[str], embed_type: str | None = None
    ) -> list[list[float]]:
        if not inputs:
            return []
        # MiniMax 要求 type；未传时检索场景默认 query，入库场景由调用方传 db
        if self._input_key == "texts" and embed_type is None:
            embed_type = "query"
        payload = self._backend.build_payload(
            inputs=inputs,
            embed_model=self.embed_model,
            input_key=self._input_key,
            embed_type=embed_type,
        )
        endpoint = self._backend.embedding_endpoint.lstrip("/")
        url = self.base_url + endpoint
        if self._input_key == "texts" and self._group_id:
            from urllib.parse import urlencode
            url = url + "?" + urlencode({"GroupId": self._group_id})
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=headers)
            try:
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                body = (e.response.text or "")[:500]
                logger.warning(
                    "Embedding API HTTP error %s: %s",
                    e.response.status_code,
                    body or "(empty body)",
                )
                raise
            data = r.json()
        try:
            return self._backend.parse_response(data)
        except (ValueError, KeyError) as e:
            logger.debug(
                "Embedding parse_response failed; response keys: %s, error: %s",
                list(data.keys()) if isinstance(data, dict) else type(data).__name__,
                e,
            )
            raise


__all__ = ["HTTPEmbeddingClient", "EmbeddingBackend"]
