"""
Backward-compatible wrapper — delegates to infrastructure.queue.
"""
from infrastructure.queue import ThreadBackend, RQBackend, register, get_task, queue  # noqa: F401
