"""Redis RQ backend — for multi-server deployments."""

import logging

from .thread import ThreadBackend

logger = logging.getLogger("fatetell.queue")


class RQBackend:
    """Redis RQ backend — for multi-server deployments."""

    def __init__(self):
        self._enabled = False
        self._fallback = ThreadBackend()
        self._init_rq()

    def _init_rq(self) -> None:
        try:
            from redis import from_url
            from rq import Queue
            url = settings.queue_redis_url or settings.redis_url or "redis://localhost:6379/0"
            self._conn = from_url(url, socket_timeout=2)
            self._conn.ping()
            self._queue = Queue("fatetell", connection=self._conn)
            self._enabled = True
            logger.info("Queue: RQ connected (%s)", url)
        except Exception as exc:
            logger.warning("Queue: RQ unavailable (%s), falling back to threads", exc)

    def enqueue(self, task: str, *args, **kwargs) -> None:
        if not self._enabled:
            self._fallback.enqueue(task, *args, **kwargs)
            return
        delay = kwargs.pop("_delay", 0)
        if delay > 0:
            self._queue.enqueue_in(("fatetell", task), delay, *args, **kwargs)
        else:
            self._queue.enqueue(f"fatetell.tasks.{task}", *args, **kwargs)

    def shutdown(self, wait: bool = True) -> None:
        pass


