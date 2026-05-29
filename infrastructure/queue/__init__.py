"""Infrastructure queue package — thread and RQ backends."""

import logging

from infrastructure.config import settings
from .thread import ThreadBackend
from .rq_backend import RQBackend
from .registry import register, get_task

logger = logging.getLogger("fatetell.queue")

_backends = {
    "thread": ThreadBackend,
    "rq": RQBackend,
}

backend_cls = _backends.get(settings.queue_backend, ThreadBackend)
queue = backend_cls()
logger.info("Queue backend: %s", backend_cls.__name__)

__all__ = ["ThreadBackend", "RQBackend", "register", "get_task", "queue"]
