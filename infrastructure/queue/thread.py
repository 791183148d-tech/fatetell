"""In-process ThreadPoolExecutor backend — single-server, zero dependencies."""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from .registry import get_task

logger = logging.getLogger("fatetell.queue")


class ThreadBackend:
    """In-process ThreadPoolExecutor — single-server, zero dependencies."""

    def __init__(self, max_workers: int | None = None):
        if max_workers is None:
            max_workers = int(os.getenv("QUEUE_WORKERS", "4"))
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="task")

    def enqueue(self, task: str, *args, **kwargs) -> None:
        fn = get_task(task)
        if not fn:
            logger.error("Unknown task: %s", task)
            return
        delay = kwargs.pop("_delay", 0)

        def _run():
            if delay > 0:
                time.sleep(delay)
            try:
                fn(*args, **kwargs)
            except Exception:
                logger.exception("Task %s failed", task)

        self._pool.submit(_run)
        logger.debug("Task enqueued: %s (args=%s)", task, args)

    def shutdown(self, wait: bool = True) -> None:
        self._pool.shutdown(wait=wait)
