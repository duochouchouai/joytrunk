"""JoyTrunk 路径：平台无关的根目录与工作区路径。"""

import os
from pathlib import Path


def get_cli_root() -> Path:
    """CLI 项目根目录（joytrunk 包所在目录的上一级）。开发时即 cli/，用于解析 cli/.env。"""
    return Path(__file__).resolve().parent.parent


def get_joytrunk_root() -> Path:
    """JoyTrunk 本地根目录。可通过环境变量 JOYTRUNK_ROOT 覆盖（测试用）。"""
    if os.environ.get("JOYTRUNK_ROOT"):
        return Path(os.environ["JOYTRUNK_ROOT"]).resolve()
    return Path.home() / ".joytrunk"


def get_config_path() -> Path:
    """配置文件路径：~/.joytrunk/config.json"""
    return get_joytrunk_root() / "config.json"


def get_workspace_root() -> Path:
    """工作区根目录：~/.joytrunk/workspace"""
    return get_joytrunk_root() / "workspace"


def get_workspace_skills() -> Path:
    """团队共享技能目录：~/.joytrunk/workspace/skills"""
    return get_workspace_root() / "skills"


def get_workspace_memory() -> Path:
    """团队共享记忆目录：~/.joytrunk/workspace/memory"""
    return get_workspace_root() / "memory"


def get_employee_dir(employee_id: str) -> Path:
    """某员工的 workspace 子目录：~/.joytrunk/workspace/employees/<employee_id>"""
    return get_workspace_root() / "employees" / employee_id
