"""测试记忆相关：Embedding 响应解析、memorize 在 embed 失败时的兜底。"""

from __future__ import annotations

import pytest

from joytrunk.agent.memory.embedding_client import EmbeddingBackend, HTTPEmbeddingClient


# ---------- HTTPEmbeddingClient MiniMax group_id ----------


def test_embedding_client_minimax_stores_group_id():
    """MiniMax 模式下传入 group_id 时客户端保存并在请求 URL 中使用。"""
    client = HTTPEmbeddingClient(
        base_url="https://api.minimaxi.com/v1",
        api_key="key",
        embed_model="embo-01",
        group_id="my-group-id",
    )
    assert client._input_key == "texts"
    assert client._group_id == "my-group-id"


def test_embedding_client_openai_ignores_group_id():
    """非 MiniMax 模式下 group_id 不改变 input_key，URL 不加 GroupId。"""
    client = HTTPEmbeddingClient(
        base_url="https://api.openai.com/v1",
        api_key="key",
        embed_model="text-embedding-3-small",
        group_id="ignored",
    )
    assert client._input_key == "input"
    assert client._group_id == "ignored"


# ---------- EmbeddingBackend.parse_response 各类响应格式 ----------


def test_parse_response_openai_format():
    """OpenAI 格式：data[].embedding"""
    backend = EmbeddingBackend()
    data = {
        "data": [
            {"embedding": [0.1, 0.2, 0.3]},
            {"embedding": [0.4, 0.5, 0.6]},
        ]
    }
    out = backend.parse_response(data)
    assert out == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_parse_response_openai_format_list_item():
    """OpenAI data 中元素为直接向量列表"""
    backend = EmbeddingBackend()
    data = {"data": [[0.1, 0.2], [0.3, 0.4]]}
    out = backend.parse_response(data)
    assert out == [[0.1, 0.2], [0.3, 0.4]]


def test_parse_response_embeddings_key():
    """MiniMax 等：embeddings 键"""
    backend = EmbeddingBackend()
    data = {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}
    out = backend.parse_response(data)
    assert out == [[0.1, 0.2], [0.3, 0.4]]


def test_parse_response_vectors_key():
    """vectors 键非 null"""
    backend = EmbeddingBackend()
    data = {"vectors": [[0.1, 0.2], [0.3, 0.4]]}
    out = backend.parse_response(data)
    assert out == [[0.1, 0.2], [0.3, 0.4]]


def test_parse_response_vectors_null_base_resp_with_data():
    """vectors 为 null 时从 base_resp 解析（base_resp 含 data）"""
    backend = EmbeddingBackend()
    data = {
        "vectors": None,
        "base_resp": {
            "data": [
                {"embedding": [0.1, 0.2]},
                {"embedding": [0.3, 0.4]},
            ]
        },
    }
    out = backend.parse_response(data)
    assert out == [[0.1, 0.2], [0.3, 0.4]]


def test_parse_response_vectors_null_base_resp_with_embeddings():
    """vectors 为 null 时从 base_resp 解析（base_resp 含 embeddings）"""
    backend = EmbeddingBackend()
    data = {
        "vectors": None,
        "base_resp": {"embeddings": [[0.1, 0.2], [0.3, 0.4]]},
    }
    out = backend.parse_response(data)
    assert out == [[0.1, 0.2], [0.3, 0.4]]


def test_parse_response_vectors_null_base_resp_unparseable_raises():
    """vectors 为 null 且 base_resp 无法解析时抛出明确 ValueError"""
    backend = EmbeddingBackend()
    data = {
        "vectors": None,
        "base_resp": {"status_code": 400, "status_msg": "bad request"},
    }
    with pytest.raises(ValueError) as exc_info:
        backend.parse_response(data)
    assert "base_resp" in str(exc_info.value)
    assert "embedding" in str(exc_info.value).lower()


def test_parse_response_status_code_status_msg_raises_clear_message():
    """仅有 status_code/status_msg 时抛出包含接口错误信息的 ValueError，不报 missing data"""
    backend = EmbeddingBackend()
    data = {"status_code": 401, "status_msg": "invalid api key"}
    with pytest.raises(ValueError) as exc_info:
        backend.parse_response(data)
    msg = str(exc_info.value)
    assert "invalid api key" in msg
    assert "401" in msg
    assert "Embedding API returned an error" in msg
    assert "missing" not in msg.lower() or "expected" in msg.lower()


def test_parse_response_data_null_raises():
    """data 为 null 时抛出"""
    backend = EmbeddingBackend()
    data = {"data": None}
    with pytest.raises(ValueError) as exc_info:
        backend.parse_response(data)
    assert "data" in str(exc_info.value)


def test_parse_response_vectors_null_no_base_resp_raises():
    """vectors 为 null 且无 base_resp 时抛出"""
    backend = EmbeddingBackend()
    data = {"vectors": None}
    with pytest.raises(ValueError) as exc_info:
        backend.parse_response(data)
    assert "vectors" in str(exc_info.value)


def test_parse_response_empty_data_returns_empty_list():
    """data 为空列表时返回空列表"""
    backend = EmbeddingBackend()
    data = {"data": []}
    out = backend.parse_response(data)
    assert out == []


# ---------- Memorize 在 embed 失败时的兜底（记忆工具可用性） ----------


@pytest.mark.asyncio
async def test_memorize_embed_failure_uses_fallback(employee_dir):
    """embed 抛错时 memorize 不崩溃，使用零向量兜底并正常返回。"""
    from joytrunk.agent.memory.memorize import run_memorize

    class FailingEmbedClient:
        async def embed(self, inputs, embed_type=None):
            raise ValueError("response['vectors'] is null and response['base_resp'] could not be parsed")

    messages = [
        {"role": "user", "content": "我叫李太白"},
        {"role": "assistant", "content": "好的，我记住了。"},
    ]

    async def fake_llm(messages_list):
        return """<item>
  <memory><content>用户名叫李太白</content><categories><category>user</category></categories></memory>
</item>"""

    result = await run_memorize(
        "emp-001",
        messages,
        llm_chat=fake_llm,
        embed_client=FailingEmbedClient(),
        memory_types=["profile"],
        enable_reinforcement=False,
    )
    assert result is not None
    assert result.get("items_count") == 1
    assert result.get("resource_id")
    assert result.get("categories_updated") >= 0


@pytest.mark.asyncio
async def test_memorize_embed_returns_empty_list_handled(employee_dir):
    """embed 返回空列表时 memorize 不崩溃。"""
    from joytrunk.agent.memory.memorize import run_memorize

    class EmptyEmbedClient:
        async def embed(self, inputs, embed_type=None):
            return []

    async def fake_llm(messages_list):
        return """<item>
  <memory><content>用户说喜欢喝茶</content><categories><category>preferences</category></categories></memory>
</item>"""

    result = await run_memorize(
        "emp-001",
        [{"role": "user", "content": "我喜欢喝茶"}, {"role": "assistant", "content": "好的"}],
        llm_chat=fake_llm,
        embed_client=EmptyEmbedClient(),
        memory_types=["profile"],
        enable_reinforcement=False,
    )
    assert result is not None
    assert "items_count" in result


# ---------- SaveMemoryTool 可用性（Dummy embed 路径） ----------


@pytest.mark.asyncio
async def test_save_memory_tool_success_with_dummy_embed(employee_dir, joytrunk_root):
    """无 embedding base_url 时使用 Dummy embed，save_memory 能正常写入并返回成功文案。"""
    import json
    from joytrunk.tools.memory_tools import SaveMemoryTool, MSG_MEMORY_SAVE_UNAVAILABLE
    from joytrunk.agent.memory import get_store

    config_path = joytrunk_root / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps({
            "version": 1,
            "ownerId": "owner-1",
            "server": {"host": "127.0.0.1", "port": 32890},
            "agents": {"defaults": {"model": "gpt-3.5-turbo", "maxTokens": 2048, "temperature": 0.1}},
            "memory": {"embedding": {"base_url": ""}, "retrieve": {"method": "rag"}},
            "providers": {"joytrunk": {}, "custom": {"apiKey": "", "apiBase": None, "model": "gpt-3.5-turbo"}},
        }),
        encoding="utf-8",
    )
    emp_config = employee_dir / "config.json"
    emp_config.parent.mkdir(parents=True, exist_ok=True)
    emp_config.write_text(json.dumps({"version": 1}), encoding="utf-8")

    tool = SaveMemoryTool(
        workspace=employee_dir,
        allowed_dir=employee_dir,
        employee_id="emp-001",
    )
    result = await tool.execute("用户叫李太白", category="user")
    assert result != MSG_MEMORY_SAVE_UNAVAILABLE, f"save_memory should succeed, got: {result}"
    assert "Saved to memory" in result

    store = get_store("emp-001")
    store.load_existing()
    items = list(store.memory_item_repo.list_items().values())
    assert len(items) >= 1
    assert any("李太白" in (it.summary or "") for it in items)
