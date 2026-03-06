"""
对指定员工的 memory.db 执行单次 CRUD 操作（供 Node API 调用）。
从 stdin 读取一行 JSON：{ "employee_id", "operation", "id"?, "payload"? }
输出一行 JSON：创建/更新返回实体，删除返回 { "ok": true }，失败返回 { "error": "..." }
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_cli_root = Path(__file__).resolve().parent.parent.parent
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))


def _no_embedding(obj: dict) -> dict:
    out = dict(obj)
    out.pop("embedding", None)
    return out


def main() -> None:
    try:
        raw = sys.stdin.readline()
        if not raw or not raw.strip():
            print(json.dumps({"error": "missing stdin json"}), flush=True)
            sys.exit(1)
        req = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid json: {e}"}), flush=True)
        sys.exit(1)

    employee_id = req.get("employee_id")
    operation = req.get("operation")
    id_ = req.get("id")
    payload = req.get("payload") or {}

    if not employee_id or not operation:
        print(json.dumps({"error": "missing employee_id or operation"}), flush=True)
        sys.exit(1)

    try:
        from joytrunk.agent.memory import get_store
    except ImportError as e:
        print(json.dumps({"error": f"import failed: {e}"}), flush=True)
        sys.exit(1)

    try:
        store = get_store(employee_id)
        store.load_existing()
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)
        sys.exit(1)

    try:
        if operation == "create_category":
            name = payload.get("name") or ""
            description = payload.get("description") or ""
            summary = payload.get("summary")
            cat = store.memory_category_repo.get_or_create_category(
                name=name, description=description, summary=summary
            )
            print(json.dumps(_no_embedding(cat.model_dump(mode="json")), ensure_ascii=False), flush=True)
            return

        if operation == "update_category":
            if not id_:
                print(json.dumps({"error": "missing id for update_category"}), flush=True)
                sys.exit(1)
            cat = store.memory_category_repo.update_category(
                category_id=id_,
                name=payload.get("name"),
                description=payload.get("description"),
                summary=payload.get("summary"),
            )
            print(json.dumps(_no_embedding(cat.model_dump(mode="json")), ensure_ascii=False), flush=True)
            return

        if operation == "delete_category":
            if not id_:
                print(json.dumps({"error": "missing id for delete_category"}), flush=True)
                sys.exit(1)
            store.memory_category_repo.delete_category(id_)
            print(json.dumps({"ok": True}), flush=True)
            return

        if operation == "create_item":
            memory_type = payload.get("memory_type") or "profile"
            summary = payload.get("summary") or ""
            resource_id = payload.get("resource_id")
            category_ids = payload.get("category_ids") or []
            item = store.memory_item_repo.create_item(
                resource_id=resource_id,
                memory_type=memory_type,
                summary=summary,
                embedding=None,
            )
            for cid in category_ids:
                if cid:
                    store.category_item_repo.link_item_category(item.id, cid)
            print(json.dumps(_no_embedding(item.model_dump(mode="json")), ensure_ascii=False), flush=True)
            return

        if operation == "update_item":
            if not id_:
                print(json.dumps({"error": "missing id for update_item"}), flush=True)
                sys.exit(1)
            item = store.memory_item_repo.update_item(
                item_id=id_,
                summary=payload.get("summary"),
                memory_type=payload.get("memory_type"),
                resource_id=payload.get("resource_id"),
            )
            print(json.dumps(_no_embedding(item.model_dump(mode="json")), ensure_ascii=False), flush=True)
            return

        if operation == "delete_item":
            if not id_:
                print(json.dumps({"error": "missing id for delete_item"}), flush=True)
                sys.exit(1)
            store.memory_item_repo.delete_item(id_)
            print(json.dumps({"ok": True}), flush=True)
            return

        if operation == "create_resource":
            url = payload.get("url") or ""
            modality = payload.get("modality") or "conversation"
            local_path = payload.get("local_path") or ""
            caption = payload.get("caption")
            res = store.resource_repo.create_resource(
                url=url,
                modality=modality,
                local_path=local_path,
                caption=caption,
                embedding=None,
            )
            print(json.dumps(_no_embedding(res.model_dump(mode="json")), ensure_ascii=False), flush=True)
            return

        if operation == "update_resource":
            if not id_:
                print(json.dumps({"error": "missing id for update_resource"}), flush=True)
                sys.exit(1)
            res = store.resource_repo.update_resource(
                resource_id=id_,
                url=payload.get("url"),
                modality=payload.get("modality"),
                local_path=payload.get("local_path"),
                caption=payload.get("caption"),
            )
            print(json.dumps(_no_embedding(res.model_dump(mode="json")), ensure_ascii=False), flush=True)
            return

        if operation == "delete_resource":
            if not id_:
                print(json.dumps({"error": "missing id for delete_resource"}), flush=True)
                sys.exit(1)
            store.resource_repo.delete_resource(id_)
            print(json.dumps({"ok": True}), flush=True)
            return

        if operation == "create_relation":
            item_id = payload.get("item_id")
            category_id = payload.get("category_id")
            if not item_id or not category_id:
                print(json.dumps({"error": "missing item_id or category_id for create_relation"}), flush=True)
                sys.exit(1)
            rel = store.category_item_repo.link_item_category(item_id, category_id)
            print(json.dumps(rel.model_dump(mode="json"), ensure_ascii=False), flush=True)
            return

        if operation == "delete_relation":
            if not id_:
                print(json.dumps({"error": "missing id for delete_relation"}), flush=True)
                sys.exit(1)
            store.category_item_repo.delete_relation(id_)
            print(json.dumps({"ok": True}), flush=True)
            return

        print(json.dumps({"error": f"unknown operation: {operation}"}), flush=True)
        sys.exit(1)
    except KeyError as e:
        print(json.dumps({"error": str(e)}), flush=True)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
