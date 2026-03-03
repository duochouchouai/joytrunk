"""
预览 ContextBuilder 合并后的 system prompt 内容。

用法:
  python -m joytrunk.scripts.preview_system_prompt              # 使用第一个员工，打印到 stdout 并写入 preview_system_prompt.txt
  python -m joytrunk.scripts.preview_system_prompt <employee_id>
"""
from __future__ import annotations

import sys
from pathlib import Path

_cli_root = Path(__file__).resolve().parent.parent.parent
if str(_cli_root) not in sys.path:
    sys.path.insert(0, str(_cli_root))

# Windows 控制台 UTF-8 输出
if sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from joytrunk.agent.context import ContextBuilder
from joytrunk.config_store import ensure_owner_id, list_employees_from_config, create_employee_in_config


def main() -> None:
    owner_id = ensure_owner_id()
    employees = list_employees_from_config(owner_id)
    if len(sys.argv) >= 2:
        employee_id = sys.argv[1].strip()
    elif employees:
        employee_id = employees[0].get("id") or employees[0].get("name") or ""
    else:
        emp = create_employee_in_config(owner_id, "预览员工")
        employee_id = emp["id"]
        print(f"未找到员工，已创建预览员工: {employee_id}\n", file=sys.stderr)

    builder = ContextBuilder(employee_id)
    prompt = builder.build_system_prompt()

    # 写入文件（UTF-8），便于在编辑器中查看完整内容
    out_file = _cli_root / "preview_system_prompt.txt"
    out_file.write_text(prompt, encoding="utf-8")
    print(f"已写入: {out_file}\n", file=sys.stderr)
    print(prompt)


if __name__ == "__main__":
    main()
