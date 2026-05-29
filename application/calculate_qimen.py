"""
Qimen Dunjia calculation use case — cache-aware calculation orchestration.

Depends on ``domain.qimen`` for pure logic and ``application.interfaces.BaZiCache``
for caching.  No framework imports.
"""

from domain.qimen import calc_qimen
from application.interfaces import BaZiCache


def make_cache_key(year: int, month: int, day: int, hour: int, minute: int) -> str:
    """Standardised cache key for Qimen calculations."""
    return f"qimen:{year}-{month:02d}-{day:02d}-{hour:02d}-{minute:02d}"


def get_or_calc_qimen(year, month, day, hour=12, minute=0, cache: BaZiCache = None):
    """
    Cache-aware Qimen Dunjia calculation.

    Returns cached result if available, otherwise calculates and caches.

    Args:
        year, month, day, hour, minute: Date/time.
        cache: A BaZiCache instance.  If None, always recalculates.

    Returns:
        dict: Qimen Dunjia chart data.
    """
    key = make_cache_key(year, month, day, hour, minute)

    if cache is not None:
        cached = cache.get(key)
        if cached is not None:
            return cached

    qimen = calc_qimen(year, month, day, hour, minute)

    if cache is not None:
        cache.set(key, qimen, ttl=3600)

    return qimen
