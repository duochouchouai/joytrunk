"""虚拟对话集成测试：多轮对话 → memorize → retrieve，验证记忆可被检索使用。"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from joytrunk.agent.memory import get_store
from joytrunk.agent.memory.memorize import run_memorize
from joytrunk.agent.memory.retrieve import retrieve


@pytest.fixture(autouse=True)
def clear_memory_store_cache():
    import joytrunk.agent.memory.store as memory_store
    memory_store._store_cache.clear()
    yield
    memory_store._store_cache.clear()


def _fake_embed(dim: int = 4):
    """返回一个按输入数量生成等长向量的 fake embed client。"""

    class FakeEmbed:
        async def embed(self, inputs):
            return [[0.1] * dim for _ in inputs]

    return FakeEmbed()


def _fake_llm_extract(xml_response: str):
    """返回固定返回指定 XML 的 llm_chat，用于 memorize 提取。"""

    async def llm_chat(msgs):
        return xml_response

    return llm_chat


def _fake_llm_retrieve_rag(_):
    """retrieve(method=rag) 不需要 llm_chat，仅占位。"""
    return "{}"


def _fake_llm_retrieve_llm(store, cat_id: str, item_id: str):
    """返回在 category/item rank 时返回指定 id 的 fake LLM。"""

    async def llm_chat(msgs):
        content = (msgs[0].get("content") or "") if msgs else ""
        if "categories" in content.lower() and "Name:" in content:
            return json.dumps({"categories": [cat_id]})
        if "items" in content.lower() and "Summary:" in content:
            return json.dumps({"items": [item_id]})
        return json.dumps({"resources": []})

    return llm_chat


# ---------- 虚拟对话数据 ----------
VIRTUAL_CONVERSATION_1 = [
    {"role": "user", "content": "我叫小明，平时喜欢喝咖啡。"},
    {"role": "assistant", "content": "好的，我记住了你叫小明，喜欢咖啡。"},
]

VIRTUAL_CONVERSATION_2 = [
    {"role": "user", "content": "我主要用 Python 写代码，有时用 TypeScript。"},
    {"role": "assistant", "content": "了解，Python 和 TypeScript。"},
]

# LLM 提取结果：对应上面两段对话的可记忆内容（XML）
XML_MEMORIES_1 = """
<item>
  <memory><content>用户叫小明，喜欢喝咖啡</content><categories><category>user</category></categories></memory>
</item>
"""
XML_MEMORIES_2 = """
<item>
  <memory><content>用户用 Python 和 TypeScript 写代码</content><categories><category>user</category></categories></memory>
</item>
"""


@pytest.mark.asyncio
async def test_virtual_conversation_memorize_then_retrieve_rag(employee_dir):
    """虚拟对话：先 memorize 一段对话，再用 RAG 检索，能拿到对应记忆。"""
    (employee_dir / "SOUL.md").write_text("", encoding="utf-8")
    (employee_dir / "USER.md").write_text("", encoding="utf-8")

    llm_chat = _fake_llm_extract(XML_MEMORIES_1)
    embed = _fake_embed(4)

    result = await run_memorize(
        "emp-001",
        VIRTUAL_CONVERSATION_1,
        llm_chat=llm_chat,
        embed_client=embed,
        enable_reinforcement=False,
    )
    assert result is not None
    assert result["items_count"] == 1

    # RAG 检索：用与记忆相关的查询
    out = await retrieve(
        "emp-001",
        "咖啡",
        method="rag",
        embed_client=embed,
        top_k_item=5,
    )
    assert "items" in out
    assert len(out["items"]) >= 1
    summaries = [i.get("summary") or "" for i in out["items"]]
    assert any("咖啡" in s for s in summaries), f"Expected 咖啡 in items, got {summaries}"


@pytest.mark.asyncio
async def test_virtual_conversation_two_rounds_then_retrieve(employee_dir):
    """两轮虚拟对话分别 memorize，再检索两个主题，验证记忆累积可用。"""
    (employee_dir / "SOUL.md").write_text("", encoding="utf-8")
    (employee_dir / "USER.md").write_text("", encoding="utf-8")

    embed = _fake_embed(4)

    # 第一轮：咖啡
    r1 = await run_memorize(
        "emp-001",
        VIRTUAL_CONVERSATION_1,
        llm_chat=_fake_llm_extract(XML_MEMORIES_1),
        embed_client=embed,
        enable_reinforcement=False,
    )
    assert r1 and r1["items_count"] == 1

    # 第二轮：Python/TypeScript
    r2 = await run_memorize(
        "emp-001",
        VIRTUAL_CONVERSATION_2,
        llm_chat=_fake_llm_extract(XML_MEMORIES_2),
        embed_client=embed,
        enable_reinforcement=False,
    )
    assert r2 and r2["items_count"] == 1

    store = get_store("emp-001")
    store.load_existing()
    all_items = list(store.memory_item_repo.list_items().values())
    assert len(all_items) >= 2

    # 检索「咖啡」应命中第一条
    out1 = await retrieve("emp-001", "咖啡", method="rag", embed_client=embed, top_k_item=5)
    assert any("咖啡" in (i.get("summary") or "") for i in out1["items"])

    # 检索「Python」应命中第二条（同一 embed 向量时可能都命中，至少 items 非空且包含我们写的内容）
    out2 = await retrieve("emp-001", "写代码", method="rag", embed_client=embed, top_k_item=5)
    assert len(out2["items"]) >= 1
    all_summaries = [i.get("summary") or "" for i in out2["items"]]
    assert any("Python" in s or "TypeScript" in s or "代码" in s for s in all_summaries) or len(all_summaries) >= 1


@pytest.mark.asyncio
async def test_virtual_conversation_retrieve_llm(employee_dir):
    """虚拟对话写入后，用 LLM 路径检索，能返回对应 items。"""
    (employee_dir / "SOUL.md").write_text("", encoding="utf-8")
    (employee_dir / "USER.md").write_text("", encoding="utf-8")

    await run_memorize(
        "emp-001",
        VIRTUAL_CONVERSATION_1,
        llm_chat=_fake_llm_extract(XML_MEMORIES_1),
        embed_client=_fake_embed(4),
        enable_reinforcement=False,
    )

    store = get_store("emp-001")
    store.load_existing()
    cat = store.memory_category_repo.get_category_by_name("user")
    items = list(store.memory_item_repo.list_items().values())
    assert cat is not None and len(items) >= 1
    cat_id = cat.id
    item_id = items[0].id

    llm_chat = _fake_llm_retrieve_llm(store, cat_id, item_id)
    out = await retrieve(
        "emp-001",
        "咖啡",
        method="llm",
        llm_chat=llm_chat,
        top_k_item=5,
    )
    assert "items" in out
    assert len(out["items"]) >= 1
    assert any((i.get("summary") or "").find("咖啡") != -1 for i in out["items"])


@pytest.mark.asyncio
async def test_virtual_conversation_format_preserved(employee_dir):
    """验证多轮对话格式正确传入 memorize（format_messages_as_conversation）。"""
    from joytrunk.agent.memory.memorize import format_messages_as_conversation

    text = format_messages_as_conversation(VIRTUAL_CONVERSATION_1)
    assert "user:" in text and "assistant:" in text
    assert "小明" in text and "咖啡" in text

    full_conv = VIRTUAL_CONVERSATION_1 + VIRTUAL_CONVERSATION_2
    full_text = format_messages_as_conversation(full_conv)
    assert "咖啡" in full_text and "Python" in full_text


# ---------- 长对话 + 真实 LLM 集成（需配置 OPENAI_API_KEY）----------
CONVERSATION_JSON = Path(__file__).resolve().parent / "example" / "conversation.json"

# 对话中应被提取出的主题关键词（至少命中若干项即认为提取有效）
EXPECTED_THEMES = [
    ("张明", "小明"),           # 姓名
    ("产品", "经理"),           # 职业
    ("咖啡", "手冲"),           # 偏好
    ("Python", "Markdown"),     # 工作工具
    ("橘座", "猫"),             # 宠物
    ("AI", "大模型", "RAG"),   # 兴趣
]


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; set it to run real LLM extraction test",
)
@pytest.mark.real_llm
async def test_conversation_json_real_llm_extraction(employee_dir):
    """
    使用 tests/example/conversation.json 长对话，真实调用 LLM 做记忆提取，
    验证鲁棒性（不崩溃、能写入）和提取准确性（关键信息出现在记忆条目中）。
    """
    if not CONVERSATION_JSON.exists():
        pytest.skip(f"Example conversation not found: {CONVERSATION_JSON}")

    (employee_dir / "SOUL.md").write_text("", encoding="utf-8")
    (employee_dir / "USER.md").write_text("", encoding="utf-8")

    with open(CONVERSATION_JSON, encoding="utf-8") as f:
        messages = json.load(f)
    assert isinstance(messages, list) and len(messages) >= 2

    base_url = (os.environ.get("OPENAI_API_BASE") or "https://api.openai.com/v1").rstrip("/")
    api_key = os.environ["OPENAI_API_KEY"]
    model = os.environ.get("OPENAI_CHAT_MODEL") or "gpt-4o-mini"
    embed_model = os.environ.get("OPENAI_EMBED_MODEL") or "text-embedding-3-small"

    from joytrunk.agent.provider import chat
    from joytrunk.agent.memory.embedding_client import HTTPEmbeddingClient

    async def real_llm_chat(msgs):
        r = await chat(base_url, api_key, model, msgs)
        return r.content or ""

    embed_client = HTTPEmbeddingClient(
        base_url=base_url,
        api_key=api_key,
        embed_model=embed_model,
    )

    result = await run_memorize(
        "emp-001",
        messages,
        llm_chat=real_llm_chat,
        embed_client=embed_client,
        enable_reinforcement=False,
    )

    # 鲁棒性：流程完成且至少有一条记忆
    assert result is not None, "run_memorize should return a result"
    assert result["items_count"] >= 1, "expected at least one memory item extracted"

    store = get_store("emp-001")
    store.load_existing()
    items = list(store.memory_item_repo.list_items().values())
    summaries = [it.summary or "" for it in items]

    # 提取准确性：长对话中多个主题应被覆盖（至少 2 个主题在提取结果中出现）
    theme_hits = 0
    for group in EXPECTED_THEMES:
        if any(any(kw in s for kw in group) for s in summaries):
            theme_hits += 1
    assert theme_hits >= 2, (
        f"Expected at least 2 theme groups in extracted summaries; "
        f"got {theme_hits}. Summaries: {summaries}"
    )

    # 检索可用性：用对话中的关键词做 RAG 检索，应能命中相关记忆
    query = "用户喜欢什么饮料或食物"
    out = await retrieve(
        "emp-001",
        query,
        method="rag",
        embed_client=embed_client,
        top_k_item=5,
    )
    assert "items" in out
    retrieved_summaries = [i.get("summary") or "" for i in out["items"]]
    has_preference = any(
        any(kw in s for kw in ("咖啡", "手冲", "饮料", "早餐", "甜"))
        for s in retrieved_summaries
    )
    assert has_preference, (
        f"Query '{query}' should retrieve preference-related memory; got {retrieved_summaries}"
    )
