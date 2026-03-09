"""
Internal bus message types for Gateway.
Fields satisfy A2A boundary layer and Worker (plan §7); self-contained, no nanobot dependency.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InboundMessage:
    """One item enqueued to MessageBus (from A2A boundary layer)."""

    task_id: str
    target_employee_id: str
    owner_id: str
    content: str
    session_key: str
    channel: str = "cli"
    chat_id: str = "direct"
    from_employee_id: str | None = None
    model: str | None = None


@dataclass
class OutboundMessage:
    """Result from Worker (written to TaskStore / returned to boundary)."""

    task_id: str
    status: str  # completed | failed
    final_content: str = ""
    usage: dict | None = None  # {"prompt_tokens": int, "completion_tokens": int}
    error: str | None = None
