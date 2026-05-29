"""
Backward-compatible wrapper — delegates to infrastructure.cache.
"""
from infrastructure.cache.memory import MemoryBackend  # noqa: F401
from infrastructure.cache.redis_backend import RedisBackend  # noqa: F401
