"""
查看 memory.db 里包含的内容（表结构、行数、样例数据）。
不依赖 get_store，直接用 sqlite3 读库，便于排查「员工不存在或无权访问」时库内实际数据。

用法:
  python -m joytrunk.scripts.inspect_memory_db                    # 列出所有员工的 memory.db 并逐个概览
  python -m joytrunk.scripts.inspect_memory_db <employee_id>       # 只查看指定员工的 memory.db 详情
  JOYTRUNK_ROOT=/path python -m joytrunk.scripts.inspect_memory_db [employee_id]  # 指定根目录
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

# 确保可 import joytrunk
_cli_root = Path(__file__).resolve().parent.parent.parent
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))


def get_joytrunk_root() -> Path:
    if os.environ.get("JOYTRUNK_ROOT"):
        return Path(os.environ["JOYTRUNK_ROOT"]).resolve()
    return Path.home() / ".joytrunk"


def get_workspace_employees_root() -> Path:
    return get_joytrunk_root() / "workspace" / "employees"


def get_employee_memory_db_path(employee_id: str) -> Path:
    return get_workspace_employees_root() / employee_id / "memory.db"


def list_employees_with_memory_db() -> list[tuple[str, Path]]:
    root = get_workspace_employees_root()
    if not root.exists():
        return []
    out: list[tuple[str, Path]] = []
    for p in root.iterdir():
        if p.is_dir():
            db_path = p / "memory.db"
            if db_path.exists():
                out.append((p.name, db_path))
    return sorted(out, key=lambda x: x[0])


def get_table_schema(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    cur = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    return [(row[0], row[1] or "") for row in cur.fetchall()]


def get_table_count(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()
    return row[0] if row else 0


def get_sample_rows(
    conn: sqlite3.Connection, table: str, limit: int = 3
) -> list[dict]:
    cur = conn.execute(f"SELECT * FROM [{table}] LIMIT {limit}")
    names = [d[0] for d in cur.description]
    rows = cur.fetchall()
    out: list[dict] = []
    for row in rows:
        obj: dict = {}
        for i, name in enumerate(names):
            val = row[i]
            # 长文本/JSON 只显示摘要
            if name and "embedding" in name.lower() and val:
                obj[name] = f"<embedding len={len(str(val))}>"
            elif name and ("json" in name.lower() or "content" in name.lower()) and val and len(str(val)) > 120:
                s = str(val)
                obj[name] = s[:120] + "…" if len(s) > 120 else s
            else:
                obj[name] = val
        out.append(obj)
    return out


def inspect_db(db_path: Path, employee_id: str, verbose: bool = True) -> None:
    print(f"\n{'='*60}")
    print(f"员工: {employee_id}")
    print(f"路径: {db_path}")
    print("=" * 60)
    if not db_path.exists():
        print("  [不存在] 该员工目录下没有 memory.db")
        return
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"  [打开失败] {e}")
        return

    try:
        # 表结构
        schema = get_table_schema(conn)
        if not schema:
            print("  [空库] 无表")
            return
        print("\n--- 表结构 ---")
        for name, sql in schema:
            print(f"  [{name}]")
            if verbose and sql:
                for line in sql.splitlines():
                    print(f"    {line.strip()}")

        # 行数 + 样例
        print("\n--- 行数与样例 ---")
        for name, _ in schema:
            cnt = get_table_count(conn, name)
            print(f"  [{name}] 共 {cnt} 行")
            if cnt > 0:
                samples = get_sample_rows(conn, name, limit=3)
                for i, row in enumerate(samples):
                    print(f"    样例 {i+1}: {dict(row)}")
        print()
    finally:
        conn.close()


def main() -> None:
    root = get_joytrunk_root()
    print(f"JOYTRUNK_ROOT: {root}")
    print(f"员工目录: {root / 'workspace' / 'employees'}")

    if len(sys.argv) >= 2:
        employee_id = sys.argv[1].strip()
        db_path = get_employee_memory_db_path(employee_id)
        inspect_db(db_path, employee_id, verbose=True)
        return

    # 无参数：列出所有有 memory.db 的员工并逐个概览
    employees = list_employees_with_memory_db()
    if not employees:
        print("\n未找到任何 memory.db（workspace/employees 下无子目录或子目录下无 memory.db）")
        return
    print(f"\n找到 {len(employees)} 个员工的 memory.db:")
    for eid, path in employees:
        print(f"  - {eid}  ->  {path}")
    for eid, path in employees:
        inspect_db(path, eid, verbose=False)


if __name__ == "__main__":
    main()
