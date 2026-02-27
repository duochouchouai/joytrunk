# -*- coding: utf-8 -*-
"""
OpenClaw 风格 TUI 框线：┌ │ ◇ ├ └ ─ ╮ ╯ 等字符构成分栏与标题。
"""

from __future__ import annotations

PANEL_WIDTH = 68


def _fill_hline(char: str = "─", width: int = PANEL_WIDTH) -> str:
    return char * width


def panel_header(title: str, width: int = PANEL_WIDTH) -> str:
    """◇  Title ────────────────╮"""
    rest = width - 3 - len(title) - 2  # "◇  " + title + " " + "╮"
    if rest < 0:
        rest = 0
    return f"◇  {title} {_fill_hline(width=rest)}╮"


def panel_line(text: str, width: int = PANEL_WIDTH) -> str:
    """│  text (truncate or pad to width-2)"""
    max_inner = width - 2
    if len(text) > max_inner:
        text = text[: max_inner - 1] + "…"
    return f"│  {text}"


def panel_empty() -> str:
    return "│"


def panel_footer(width: int = PANEL_WIDTH) -> str:
    """├────────────────────────╯"""
    return "├" + _fill_hline(width=width) + "╯"


def screen_top(title: str, width: int = PANEL_WIDTH) -> str:
    """┌  Title (no right corner, open)"""
    return f"┌  {title}"


def screen_bottom() -> str:
    """└"""
    return "└"


def build_language_panel(title: str, hint: str, width: int = PANEL_WIDTH) -> str:
    """构建语言选择面板的静态框线文本（选项由 OptionList 单独渲染）。"""
    lines = [
        screen_top(title, width),
        panel_empty(),
        panel_header("选择语言" if "语言" in title or "language" in title.lower() else title, width),
        panel_empty(),
        panel_line(hint),
        panel_empty(),
        panel_footer(width),
        panel_empty(),
        screen_bottom(),
    ]
    return "\n".join(lines)


def build_entry_panel_section(header_title: str, body_lines: list[str], width: int = PANEL_WIDTH) -> list[str]:
    """构建一个分栏：◇ Header ──╮、│  line、├──╯。返回行列表。"""
    out = [panel_empty(), panel_header(header_title, width), panel_empty()]
    for line in body_lines:
        out.append(panel_line(line, width))
    out.append(panel_empty())
    out.append(panel_footer(width))
    return out


def build_entry_screen_top(title: str, width: int = PANEL_WIDTH) -> list[str]:
    """┌  Title 与首行 │"""
    return [screen_top(title, width), panel_empty()]


def _dim_frame(s: str) -> str:
    """框线字符用 [dim] 包裹，与终端/OpenClaw 风格一致。"""
    for char in "┌│├└─╮╯◇":
        s = s.replace(char, f"[dim]{char}[/]")
    return s


def build_entry_message_block(header_title: str, message_body: str, width: int = PANEL_WIDTH) -> str:
    """JoyTrunk 入口首屏：┌  JoyTrunk、◇  header ──╮、│  message lines、├──╯。"""
    lines = [""] + build_entry_screen_top("JoyTrunk", width)
    body_lines = [s.strip() for s in message_body.strip().split("\n") if s.strip()]
    lines.extend(build_entry_panel_section(header_title, body_lines or [" "], width))
    return _dim_frame("\n".join(lines))


def build_entry_bottom(hint: str) -> str:
    """◆  hint、└"""
    raw = "\n".join([panel_empty(), f"◆  {hint}", panel_empty(), screen_bottom()])
    return _dim_frame(raw)


# 语言选项用于 OpenClaw 风格单块渲染
LANG_OPTIONS = [
    ("zh", "中文 (zh)"),
    ("en", "English (en)"),
]


def build_language_screen(selected_index: int, section_title: str, hint: str, width: int = PANEL_WIDTH) -> str:
    """整屏语言选择：┌  Title、◇  Section ──╮、│  ○/● 选项、├──╯、◆  hint、└。框线用 [dim] 更柔和。"""
    lines = [
        "",
        screen_top(section_title, width),
        panel_empty(),
        panel_header("选择语言" if "语言" in section_title or "language" in section_title.lower() else section_title, width),
        panel_empty(),
    ]
    for i, (lid, label) in enumerate(LANG_OPTIONS):
        bullet = "●" if i == selected_index else "○"
        lines.append(panel_line(f"{bullet} {label}", width))
    lines.extend([
        panel_empty(),
        panel_footer(width),
        panel_empty(),
        f"◆  {hint}",
        panel_empty(),
        screen_bottom(),
        "",
    ])
    # 仅框线字符用 dim，◆ 与 ●○ 保持醒目
    raw = "\n".join(lines)
    for char in "┌│├└─╮╯◇":
        raw = raw.replace(char, f"[dim]{char}[/]")
    return raw
