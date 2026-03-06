"""Gateway: A2A boundary, TaskStore, Worker, Channel (phase 4)."""

from joytrunk.gateway.channel import Channel, get_channel, list_channels, register_channel
from joytrunk.gateway.task_store import TaskStore, get_default_task_store

def run_worker_loop(*args, **kwargs):
    from joytrunk.gateway.worker import run_worker_loop as _run
    return _run(*args, **kwargs)

__all__ = [
    "Channel",
    "TaskStore",
    "get_channel",
    "get_default_task_store",
    "list_channels",
    "register_channel",
    "run_worker_loop",
]
