"""Redis-backed cache — falls back to memory if Redis unavailable."""

import json
import logging

from infrastructure.cache.memory import MemoryBackend
from infrastructure.config import settings

logger = logging.getLogger("fatetell.cache")


class RedisBackend:
    """Redis-backed cache. Falls back to memory if Redis unavailable."""

    def __init__(self, default_ttl: int = 3600):
        self._default_ttl = default_ttl
        self._fallback = MemoryBackend(default_ttl)
        self._client = None
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis as r
            url = settings.redis_url or "redis://localhost:6379/0"
            self._client = r.from_url(url, decode_responses=True, socket_timeout=2)
            self._client.ping()
            logger.info("Cache: Redis connected (%s)", url)
        except Exception as exc:
            logger.warning("Cache: Redis unavailable (%s), falling back to memory", exc)
            self._client = None

    def get(self, key: str):
        if not self._client:
            return self._fallback.get(key)
        try:
            val = self._client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return self._fallback.get(key)

    def set(self, key: str, value, ttl: int | None = None) -> None:
        if not self._client:
            self._fallback.set(key, value, ttl)
            return
        try:
            self._client.setex(key, ttl or self._default_ttl, json.dumps(value))
        except Exception:
            self._fallback.set(key, value, ttl)

    def clear(self) -> None:
        if self._client:
            try:
                self._client.flushdb()
            except Exception:
                pass
        self._fallback.clear()
