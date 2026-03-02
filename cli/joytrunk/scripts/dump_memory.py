"""
导出指定员工的 memory.db 内容为 JSON（供前端展示）。
用法：python -m joytrunk.scripts.dump_memory <employee_id>
输出：单行 JSON 到 stdout，含 categories / items / resources / category_item_relations / chat_messages（不含 embedding 向量）。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 确保可 import joytrunk（从 repo 根或 cli 运行时）
_cli_root = Path(__file__).resolve().parent.parent.parent
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))


def _no_embedding(obj: dict) -> dict:
    out = dict(obj)
    out.pop("embedding", None)
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "missing employee_id"}), flush=True)
        sys.exit(1)
    employee_id = sys.argv[1].strip()
    if not employee_id:
        print(json.dumps({"error": "empty employee_id"}), flush=True)
        sys.exit(1)
    try:
        from joytrunk import paths
        from joytrunk.agent.memory import get_store
    except ImportError as e:
        print(json.dumps({"error": f"import failed: {e}"}), flush=True)
        sys.exit(1)
    if os.environ.get("JOYTRUNK_ROOT"):
        # 由 Node server 传入，确保与 server 使用同一根目录
        pass  # paths 内部用 os.environ 或 Path.home()
    try:
        store = get_store(employee_id)
        store.load_existing()
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)
        sys.exit(1)
    categories = []
    for c in store.memory_category_repo.list_categories().values():
        categories.append(_no_embedding(c.model_dump(mode="json")))
    items = []
    for i in store.memory_item_repo.list_items().values():
        items.append(_no_embedding(i.model_dump(mode="json")))
    resources = []
    for r in store.resource_repo.list_resources().values():
        resources.append(_no_embedding(r.model_dump(mode="json")))
    relations = []
    for rel in store.category_item_repo.list_relations():
        relations.append(rel.model_dump(mode="json"))
    chat_messages = store.chat_message_repo.list_all_for_export()
    out = {
        "employee_id": employee_id,
        "categories": categories,
        "items": items,
        "resources": resources,
        "category_item_relations": relations,
        "chat_messages": chat_messages,
    }
    print(json.dumps(out, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
