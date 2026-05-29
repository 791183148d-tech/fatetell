"""Thread-safe in-memory TTL cache."""

import time
from typing import Any


class MemoryBackend:
    """Thread-safe in-process TTL dict."""

    def __init__(self, default_ttl: int = 3600):
        self._store: dict[str, dict] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + (ttl or self._default_ttl),
        }

    def clear(self) -> None:
        self._store.clear()
