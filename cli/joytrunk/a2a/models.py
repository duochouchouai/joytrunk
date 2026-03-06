"""
A2A (Agent2Agent) protocol data models.
Aligns with https://a2a-protocol.org/dev/specification/ (Task, Message, Part, AgentCard, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# --- Task status (A2A lifecycle) ---
TaskStatus = str  # working | completed | failed | canceled


@dataclass
class Part:
    """Smallest unit of content. First release: text only."""

    type: str  # "text" | "file" | ...
    text: str | None = None
    # file_url, mime_type, etc. for future


@dataclass
class Message:
    """Single turn: user or agent."""

    role: str  # "user" | "agent"
    parts: list[Part] = field(default_factory=list)
    context_id: str | None = None
    task_id: str | None = None


@dataclass
class SendMessageConfiguration:
    """SendMessage request configuration."""

    blocking: bool = False
    history_length: int | None = None


@dataclass
class SendMessageRequest:
    """Inbound A2A Send Message request."""

    message: Message
    configuration: SendMessageConfiguration | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# --- Task (stateful unit of work) ---
@dataclass
class Task:
    """A2A Task: id, owner_id, status, contextId, history, artifacts, metadata, timestamps."""

    id: str
    owner_id: str
    status: TaskStatus
    context_id: str
    history: list[Message] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None


# --- AgentCard (discovery) ---
@dataclass
class AgentCardCapabilities:
    """Optional capabilities declared by the agent."""

    streaming: bool = False
    push_notifications: bool = False
    extended_agent_card: bool = False


@dataclass
class AgentCard:
    """Agent metadata for discovery."""

    name: str | None = None
    description: str | None = None
    capabilities: AgentCardCapabilities | None = None
    url: str | None = None  # endpoint URL
    # security_schemes, skills, etc. optional


def part_to_text(parts: list[Part]) -> str:
    """Concatenate text from all text Parts (plan 10.1)."""
    return "".join(p.text or "" for p in parts if p.type == "text")


def message_to_dict(m: Message) -> dict[str, Any]:
    """Serialize Message for JSON (A2A style)."""
    return {
        "role": m.role,
        "parts": [
            {"type": p.type, "text": p.text} for p in m.parts
        ],
        **({"contextId": m.context_id} if m.context_id else {}),
        **({"taskId": m.task_id} if m.task_id else {}),
    }


def task_to_dict(t: Task) -> dict[str, Any]:
    """Serialize Task for JSON (A2A style)."""
    return {
        "id": t.id,
        "status": t.status,
        "contextId": t.context_id,
        "history": [message_to_dict(h) for h in t.history],
        "artifacts": t.artifacts,
        "metadata": t.metadata,
        **({"createdAt": t.created_at} if t.created_at else {}),
        **({"updatedAt": t.updated_at} if t.updated_at else {}),
    }


def agent_card_to_dict(c: AgentCard) -> dict[str, Any]:
    """Serialize AgentCard for JSON."""
    caps = c.capabilities
    return {
        "name": c.name,
        "description": c.description,
        "url": c.url,
        "capabilities": {
            "streaming": caps.streaming if caps else False,
            "pushNotifications": caps.push_notifications if caps else False,
            "extendedAgentCard": caps.extended_agent_card if caps else False,
        } if caps else {},
    }
