"""将员工长期记忆导出为 Markdown，便于查看与备份。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from joytrunk import paths
from joytrunk.agent.memory import get_store
from joytrunk.agent.memory.store import CATEGORY_NAMES, CATEGORY_DESCRIPTIONS

# 导出时类别顺序与显示名（与 store 的 14 类一致）
CATEGORY_ORDER = CATEGORY_NAMES
CATEGORY_LABELS = dict(CATEGORY_DESCRIPTIONS)


def export_memory_to_md(
    employee_id: str,
    output_path: Path | None = None,
) -> Path:
    """
    将指定员工的记忆库导出为 Markdown 文件。

    - output_path 未指定时，写入员工目录下的 outputs/memory_export.md。
    - 若 output_path 为文件路径，其父目录不存在时会自动创建。
    - 返回实际写入的文件路径。
    """
    if output_path is None:
        out_dir = paths.get_employee_outputs_dir(employee_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / "memory_export.md"
    else:
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

    store = get_store(employee_id)
    store.load_existing()

    categories = store.memory_category_repo.list_categories()
    items = store.memory_item_repo.list_items()
    relations = store.category_item_repo.list_relations()

    # item_id -> [category_name]
    item_to_cats: dict[str, list[str]] = {}
    cat_id_to_name = {c.id: c.name for c in categories.values()}
    for rel in relations:
        cname = cat_id_to_name.get(rel.category_id)
        if cname:
            item_to_cats.setdefault(rel.item_id, []).append(cname)

    lines: list[str] = []
    lines.append("# 长期记忆导出")
    lines.append("")
    lines.append(f"员工: `{employee_id}`  |  导出时间: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 一、类别摘要
    lines.append("## 类别摘要")
    lines.append("")
    for name in CATEGORY_ORDER:
        cat = next((c for c in categories.values() if c.name == name), None)
        if not cat:
            continue
        label = CATEGORY_LABELS.get(name, name)
        lines.append(f"### {label}（{name}）")
        lines.append("")
        if cat.summary and cat.summary.strip():
            lines.append(cat.summary.strip())
        else:
            lines.append("*（暂无摘要）*")
        lines.append("")
        lines.append("")

    # 二、记忆条目（按类别分组）
    lines.append("---")
    lines.append("")
    lines.append("## 记忆条目")
    lines.append("")

    for cat_name in CATEGORY_ORDER:
        label = CATEGORY_LABELS.get(cat_name, cat_name)
        item_list = [
            (item_id, items[item_id])
            for item_id, cats in item_to_cats.items()
            if cat_name in cats and item_id in items
        ]
        if not item_list:
            continue
        lines.append(f"### {label}")
        lines.append("")
        for item_id, item in sorted(item_list, key=lambda x: x[1].created_at or datetime.min):
            created = (item.created_at or "").isoformat()[:19] if item.created_at else ""
            summary = item.summary.strip()
            lines.append(f"- **{summary[:200]}{'…' if len(summary) > 200 else ''}**")
            meta = []
            if item.memory_type:
                meta.append(f"类型: {item.memory_type}")
            if created:
                meta.append(f"记录于: {created}")
            if meta:
                lines.append(f"  - {', '.join(meta)}")
            lines.append("")
        lines.append("")

    # 未归类条目
    ungrouped = [(iid, items[iid]) for iid in items if iid not in item_to_cats]
    if ungrouped:
        lines.append("### 未归类")
        lines.append("")
        for item_id, item in sorted(ungrouped, key=lambda x: x[1].created_at or datetime.min):
            created = (item.created_at or "").isoformat()[:19] if item.created_at else ""
            summary = item.summary.strip()
            lines.append(f"- **{summary[:200]}{'…' if len(summary) > 200 else ''}**")
            meta = []
            if item.memory_type:
                meta.append(f"类型: {item.memory_type}")
            if created:
                meta.append(f"记录于: {created}")
            if meta:
                lines.append(f"  - {', '.join(meta)}")
            lines.append("")

    text = "\n".join(lines)
    output_path.write_text(text, encoding="utf-8")
    return output_path


__all__ = ["export_memory_to_md", "CATEGORY_ORDER", "CATEGORY_LABELS"]
