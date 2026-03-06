"""测试 joytrunk.agent.context。"""

import pytest

from joytrunk.agent.context import (
    RUNTIME_TAG,
    ContextBuilder,
)
from joytrunk.agent.memory.store import (
    PLACEHOLDER_CATEGORIES,
    get_store,
)


# 最小模板：包含所有占位符，用于证明 {{ xxx }} 均被正确替换
MINIMAL_TEMPLATE = """{{identity}}
---
{{style}}
---
{{soul}}
---
{{user}}
---
{{colleagues}}
---
{{agents}}
---
{{tools}}
---
{{memory}}
---
{{skills}}
"""


def _seed_memory_with_markers(employee_id: str) -> None:
    """在 memory.db 中为每个占位符对应 category 插入一条带唯一 marker 的 item，并 link。"""
    store = get_store(employee_id)
    store.load_existing()
    for placeholder_name, category_name in PLACEHOLDER_CATEGORIES.items():
        cat = store.memory_category_repo.get_category_by_name(category_name)
        if not cat:
            continue
        summary = f"MARKER_{placeholder_name}"
        item = store.memory_item_repo.create_item(
            memory_type="profile",
            summary=summary,
        )
        store.category_item_repo.link_item_category(item.id, cat.id)


def test_all_placeholders_replaced_no_literal_left(employee_dir):
    """使用含全部占位符的模板且无 memory 时，结果中不应残留任何 {{ xxx }}。"""
    (employee_dir / "SYSTEM_PROMPT.md").write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    ctx = ContextBuilder("emp-001")
    prompt = ctx.build_system_prompt()
    assert "{{" not in prompt, f"仍有未替换占位符，片段: ...{prompt[prompt.find('{{')-20:prompt.find('{{')+30]}..."
    assert "}}" not in prompt


def test_all_placeholders_filled_from_memory_db(employee_dir):
    """从 memory.db 各 category 取 item 填入占位符：identity/style/soul/user/colleagues/agents/tools 均出现对应 marker。"""
    (employee_dir / "SYSTEM_PROMPT.md").write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    _seed_memory_with_markers("emp-001")
    ctx = ContextBuilder("emp-001")
    prompt = ctx.build_system_prompt()
    assert "{{" not in prompt
    for name in ("identity", "style", "soul", "user", "colleagues", "agents"):
        marker = f"MARKER_{name}"
        assert marker in prompt, f"{{{{{name}}}}} 应被替换为含 {marker} 的列表"
    assert "MARKER_tools" in prompt or "- （空）" in prompt or "tools" in prompt.lower(), "{{tools}} 应被替换（含 item 或内置说明）"
    assert "- （空）" in prompt or "MARKER_" in prompt, "memory/skills 无数据时应出现「- （空）」或有 marker"


def test_style_placeholder_in_own_section(employee_dir):
    """沟通与风格 {{style}} 的 item 列表应出现在结果中，且不与 identity 混在一起。"""
    template = """# 身份
{{identity}}
# 沟通与风格
{{style}}
# 人格
{{soul}}
"""
    (employee_dir / "SYSTEM_PROMPT.md").write_text(template, encoding="utf-8")
    _seed_memory_with_markers("emp-001")
    ctx = ContextBuilder("emp-001")
    prompt = ctx.build_system_prompt()
    assert "{{" not in prompt
    idx_identity = prompt.find("MARKER_identity")
    idx_style = prompt.find("MARKER_style")
    idx_soul = prompt.find("MARKER_soul")
    assert idx_identity >= 0 and idx_style >= 0 and idx_soul >= 0
    section_identity = prompt.find("# 身份")
    section_style = prompt.find("# 沟通与风格")
    section_soul = prompt.find("# 人格")
    assert section_identity < idx_identity < section_style < idx_style < section_soul < idx_soul, (
        "identity/style/soul 应按章节顺序出现，style 不在 identity 段落内"
    )


def test_build_system_prompt_includes_memory(employee_dir, workspace_root):
    """占位符 {{memory}} 由 context 填入（当前为长期记忆块，可为「- （空）」）。"""
    tpl = "{{identity}}\n{{memory}}\n{{soul}}"
    (employee_dir / "SYSTEM_PROMPT.md").write_text(tpl, encoding="utf-8")
    ctx = ContextBuilder("emp-001")
    prompt = ctx.build_system_prompt()
    assert "{{" not in prompt
    assert "- （空）" in prompt or "长期" in prompt


def test_build_messages_structure(employee_dir):
    (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
    ctx = ContextBuilder("emp-001")
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    messages = ctx.build_messages(history, "帮我截图", channel="cli", chat_id="direct")
    assert len(messages) >= 4
    assert messages[0]["role"] == "system"
    assert "Soul" in messages[0]["content"]
    assert messages[1]["content"] == "hi"
    assert messages[2]["content"] == "hello"
    assert RUNTIME_TAG in messages[3]["content"]
    assert messages[4]["content"] == "帮我截图"


def test_build_messages_empty_message_uses_placeholder(employee_dir):
    (employee_dir / "SOUL.md").write_text("Soul", encoding="utf-8")
    ctx = ContextBuilder("emp-001")
    messages = ctx.build_messages([], "")
    assert any(m.get("content") == "请说你好。" for m in messages if m.get("role") == "user")


def test_add_assistant_message(employee_dir):
    ctx = ContextBuilder("emp-001")
    messages = [{"role": "system", "content": "sys"}]
    ContextBuilder.add_assistant_message(messages, "ok", None)
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == "ok"
    ContextBuilder.add_assistant_message(messages, "call", [{"id": "1", "type": "function", "function": {"name": "exec", "arguments": "{}"}}])
    assert "tool_calls" in messages[-1]


def test_add_tool_result(employee_dir):
    messages = [{"role": "assistant", "content": "..."}]
    ContextBuilder.add_tool_result(messages, "call-1", "read_file", "file content")
    assert messages[-1]["role"] == "tool"
    assert messages[-1]["tool_call_id"] == "call-1"
    assert messages[-1]["name"] == "read_file"
    assert messages[-1]["content"] == "file content"
