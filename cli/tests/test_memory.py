"""记忆模块测试：models、vector、SQLite store、memorize、retrieve（RAG/LLM）。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

# 每个测试前清空 store 缓存，保证使用当前 JOYTRUNK_ROOT
@pytest.fixture(autouse=True)
def clear_memory_store_cache():
    import joytrunk.agent.memory.store as memory_store
    memory_store._store_cache.clear()
    yield
    memory_store._store_cache.clear()


# ----- models -----
def test_compute_content_hash():
    from joytrunk.agent.memory.models import compute_content_hash
    h1 = compute_content_hash("user likes coffee", "profile")
    h2 = compute_content_hash("user likes coffee", "profile")
    h3 = compute_content_hash("user  likes  coffee", "profile")
    assert h1 == h2 == h3
    assert len(h1) == 16
    assert compute_content_hash("other", "profile") != h1
    assert compute_content_hash("user likes coffee", "event") != h1


# ----- vector -----
def test_cosine_topk():
    from joytrunk.agent.memory.vector import cosine_topk
    q = [1.0, 0.0, 0.0]
    corpus = [
        ("a", [1.0, 0.0, 0.0]),
        ("b", [0.9, 0.1, 0.0]),
        ("c", [0.0, 1.0, 0.0]),
    ]
    hits = cosine_topk(q, corpus, k=2)
    assert len(hits) == 2
    assert hits[0][0] == "a"
    assert hits[1][0] == "b"
    assert hits[0][1] >= hits[1][1] > 0


def test_cosine_topk_salience():
    from joytrunk.agent.memory.vector import cosine_topk_salience
    now = datetime.now(timezone.utc)
    q = [1.0, 0.0, 0.0]
    corpus = [
        ("a", [1.0, 0.0, 0.0], 2, now),
        ("b", [1.0, 0.0, 0.0], 1, now),
    ]
    hits = cosine_topk_salience(q, corpus, k=2)
    assert len(hits) == 2
    assert hits[0][0] == "a"
    assert hits[0][1] > hits[1][1]


def test_salience_score():
    from joytrunk.agent.memory.vector import salience_score
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    s1 = salience_score(0.8, 2, now, recency_decay_days=30.0)
    s2 = salience_score(0.8, 1, now, recency_decay_days=30.0)
    assert s1 > s2
    old = now - timedelta(days=60)
    s3 = salience_score(0.8, 2, old, recency_decay_days=30.0)
    assert s3 < s1


# ----- store + SQLite -----
def test_get_store_creates_db(employee_dir, joytrunk_root):
    from joytrunk.agent.memory import get_store
    store = get_store("emp-001")
    assert store is not None
    db_path = joytrunk_root / "workspace" / "employees" / "emp-001" / "memory.db"
    assert db_path.exists()


def test_ensure_categories_from_md(employee_dir):
    (employee_dir / "SOUL.md").write_text("我是人格", encoding="utf-8")
    (employee_dir / "USER.md").write_text("用户信息", encoding="utf-8")
    from joytrunk.agent.memory.store import get_store, ensure_categories_from_md
    store = get_store("emp-001")
    ensure_categories_from_md("emp-001", store)
    store.load_existing()
    cat_soul = store.memory_category_repo.get_category_by_name("soul")
    cat_user = store.memory_category_repo.get_category_by_name("user")
    assert cat_soul is not None and "我是人格" in (cat_soul.summary or "")
    assert cat_user is not None and "用户信息" in (cat_user.summary or "")


def test_store_resource_and_item(employee_dir):
    from joytrunk.agent.memory import get_store
    store = get_store("emp-001")
    store.load_existing()
    res = store.resource_repo.create_resource(
        url="conv:1",
        modality="conversation",
        local_path="",
        caption="对话摘要",
        embedding=[0.1] * 4,
    )
    assert res.id
    vec = [0.2] * 4
    item = store.memory_item_repo.create_item(
        resource_id=res.id,
        memory_type="profile",
        summary="用户喜欢咖啡",
        embedding=vec,
        reinforce=False,
    )
    assert item.id
    assert item.summary == "用户喜欢咖啡"
    got = store.memory_item_repo.get_item(item.id)
    assert got is not None and got.summary == item.summary


def test_vector_search_items(employee_dir):
    from joytrunk.agent.memory import get_store
    store = get_store("emp-001")
    store.load_existing()
    res = store.resource_repo.create_resource(
        url="u", modality="conversation", local_path="", caption=None, embedding=None
    )
    store.memory_item_repo.create_item(
        resource_id=res.id, memory_type="profile", summary="咖啡",
        embedding=[1.0, 0.0, 0.0], reinforce=False,
    )
    store.memory_item_repo.create_item(
        resource_id=res.id, memory_type="profile", summary="茶",
        embedding=[-1.0, 0.0, 0.0], reinforce=False,
    )
    hits = store.memory_item_repo.vector_search_items(
        [1.0, 0.0, 0.0], top_k=1, ranking="similarity"
    )
    assert len(hits) == 1
    item = store.memory_item_repo.get_item(hits[0][0])
    assert item is not None and "咖啡" in item.summary


# ----- memorize helpers -----
def test_format_messages_as_conversation():
    from joytrunk.agent.memory.memorize import format_messages_as_conversation
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
        {"role": "user", "content": "我喜欢喝咖啡"},
    ]
    text = format_messages_as_conversation(messages)
    assert "user: 你好" in text
    assert "assistant: 你好" in text
    assert "user: 我喜欢喝咖啡" in text


def test_parse_memory_xml():
    from joytrunk.agent.memory.memorize import _parse_memory_xml
    raw = """
    <item>
      <memory>
        <content>用户喜欢咖啡</content>
        <categories><category>user</category></categories>
      </memory>
      <memory>
        <content>用户是产品经理</content>
        <categories><category>user</category><category>agents</category></categories>
      </memory>
    </item>
    """
    entries = _parse_memory_xml(raw)
    assert len(entries) == 2
    assert entries[0][0] == "用户喜欢咖啡"
    assert "user" in entries[0][1]
    assert entries[1][0] == "用户是产品经理"
    assert "user" in entries[1][1] and "agents" in entries[1][1]
    assert _parse_memory_xml("") == []
    assert _parse_memory_xml("no xml") == []


@pytest.mark.asyncio
async def test_run_memorize_integration(employee_dir):
    from joytrunk.agent.memory.memorize import run_memorize
    (employee_dir / "SOUL.md").write_text("", encoding="utf-8")
    (employee_dir / "USER.md").write_text("", encoding="utf-8")
    xml_out = """
    <item>
      <memory><content>用户喜欢咖啡</content><categories><category>user</category></categories></memory>
    </item>
    """
    async def fake_llm(msgs):
        return xml_out
    class FakeEmbed:
        async def embed(self, inputs):
            return [[0.1] * 4 for _ in inputs]
    messages = [
        {"role": "user", "content": "我喜欢喝咖啡"},
        {"role": "assistant", "content": "好的，已记住。"},
    ]
    result = await run_memorize(
        "emp-001", messages, llm_chat=fake_llm, embed_client=FakeEmbed(),
        enable_reinforcement=False,
    )
    assert result is not None
    assert result["items_count"] == 1
    from joytrunk.agent.memory import get_store
    store = get_store("emp-001")
    store.load_existing()
    assert len(store.memory_item_repo.list_items()) >= 1
    assert len(store.resource_repo.list_resources()) >= 1


# ----- retrieve RAG -----
@pytest.mark.asyncio
async def test_retrieve_rag(employee_dir):
    from joytrunk.agent.memory import get_store
    from joytrunk.agent.memory.retrieve import retrieve_rag
    store = get_store("emp-001")
    store.load_existing()
    res = store.resource_repo.create_resource(
        url="r1", modality="conversation", local_path="", caption=None, embedding=None
    )
    store.memory_item_repo.create_item(
        resource_id=res.id, memory_type="profile", summary="用户喜欢咖啡",
        embedding=[1.0, 0.0, 0.0], reinforce=False,
    )
    class FakeEmbed:
        async def embed(self, inputs):
            return [[1.0, 0.0, 0.0] for _ in inputs]
    out = await retrieve_rag("emp-001", "咖啡", embed_client=FakeEmbed(), top_k_item=5)
    assert "items" in out
    assert len(out["items"]) >= 1
    assert any("咖啡" in (i.get("summary") or "") for i in out["items"])


# ----- retrieve LLM -----
@pytest.mark.asyncio
async def test_retrieve_llm(employee_dir):
    from joytrunk.agent.memory import get_store
    from joytrunk.agent.memory.retrieve import retrieve_llm
    store = get_store("emp-001")
    store.load_existing()
    cat = store.memory_category_repo.get_or_create_category(
        name="user", description="用户", summary="用户相关"
    )
    res = store.resource_repo.create_resource(
        url="r1", modality="conversation", local_path="", caption=None, embedding=None
    )
    item = store.memory_item_repo.create_item(
        resource_id=res.id, memory_type="profile", summary="用户喜欢咖啡",
        embedding=[0.0] * 4, reinforce=False,
    )
    store.category_item_repo.link_item_category(item.id, cat.id)
    async def fake_llm(msgs):
        if "categories" in (msgs[0].get("content") or ""):
            return json.dumps({"analysis": "ok", "categories": [cat.id]})
        if "items" in (msgs[0].get("content") or ""):
            return json.dumps({"analysis": "ok", "items": [item.id]})
        return json.dumps({"analysis": "ok", "resources": []})
    out = await retrieve_llm("emp-001", "咖啡", llm_chat=fake_llm, top_k_item=5)
    assert "categories" in out and "items" in out
    assert len(out["items"]) >= 1
    assert any(i.get("summary") == "用户喜欢咖啡" for i in out["items"])


# ----- retrieve 统一入口 -----
@pytest.mark.asyncio
async def test_retrieve_method_rag(employee_dir):
    from joytrunk.agent.memory.retrieve import retrieve
    class FakeEmbed:
        async def embed(self, inputs):
            return [[0.0] * 4 for _ in inputs]
    out = await retrieve("emp-001", "测试", method="rag", embed_client=FakeEmbed(), top_k_item=2)
    assert "items" in out and "categories" in out and "resources" in out


@pytest.mark.asyncio
async def test_retrieve_method_llm(employee_dir):
    from joytrunk.agent.memory.retrieve import retrieve
    async def fake_llm(_):
        return '{"categories":[],"items":[],"resources":[]}'
    out = await retrieve("emp-001", "测试", method="llm", llm_chat=fake_llm, top_k_item=2)
    assert "items" in out and "categories" in out and "resources" in out


# ----- 多员工隔离 -----
def test_memory_isolated_per_employee(workspace_root, joytrunk_root):
    from joytrunk.agent.memory import get_store
    emp1 = workspace_root / "employees" / "emp-A"
    emp2 = workspace_root / "employees" / "emp-B"
    emp1.mkdir(parents=True)
    emp2.mkdir(parents=True)
    store_a = get_store("emp-A")
    store_b = get_store("emp-B")
    store_a.load_existing()
    store_b.load_existing()
    res_a = store_a.resource_repo.create_resource(
        url="a", modality="conversation", local_path="", caption="只有A", embedding=None
    )
    item_a = store_a.memory_item_repo.create_item(
        resource_id=res_a.id, memory_type="profile", summary="A的记忆",
        embedding=[1.0, 0.0, 0.0], reinforce=False,
    )
    assert len(store_a.memory_item_repo.list_items()) == 1
    assert len(store_b.memory_item_repo.list_items()) == 0
    assert store_b.memory_item_repo.get_item(item_a.id) is None
    db_a = joytrunk_root / "workspace" / "employees" / "emp-A" / "memory.db"
    db_b = joytrunk_root / "workspace" / "employees" / "emp-B" / "memory.db"
    assert db_a.exists() and db_b.exists()


# ----- embedding client（mock 请求）-----
@pytest.mark.asyncio
async def test_embedding_client_embed():
    from joytrunk.agent.memory.embedding_client import HTTPEmbeddingClient
    vec = [0.1] * 1536
    async def mock_post(*args, **kwargs):
        class Resp:
            def raise_for_status(self): pass
            def json(self): return {"data": [{"embedding": vec}, {"embedding": vec}]}
        return Resp()
    with patch("httpx.AsyncClient.post", new=mock_post):
        client = HTTPEmbeddingClient(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            embed_model="text-embedding-3-small",
        )
        result = await client.embed(["hello", "world"])
    assert len(result) == 2
    assert result[0] == vec and result[1] == vec
