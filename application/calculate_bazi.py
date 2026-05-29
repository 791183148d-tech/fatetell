"""
BaZi calculation use case — cache-aware calculation orchestration.

Depends on ``domain.bazi`` for pure logic and ``application.interfaces.BaZiCache``
for caching.  No framework imports.
"""

from domain.bazi import calc_bazi
from application.interfaces import BaZiCache


def make_cache_key(year: int, month: int, day: int, hour: int, minute: int, gender: str) -> str:
    """Standardised cache key for BaZi calculations."""
    return f"bazi:{year}-{month:02d}-{day:02d}-{hour:02d}-{minute:02d}-{gender}"


def get_or_calc_bazi(year, month, day, hour, minute=0, gender="male", cache: BaZiCache = None):
    """
    Cache-aware BaZi calculation.

    Returns cached result if available, otherwise calculates and caches.

    Args:
        year, month, day, hour, minute: Birth date/time.
        gender: "male" or "female".
        cache: A BaZiCache instance.  If None, always recalculates.

    Returns:
        dict: BaZi chart data.
    """
    key = make_cache_key(year, month, day, hour, minute, gender)

    if cache is not None:
        bazi = cache.get(key)
        if bazi is not None:
            return bazi

    bazi = calc_bazi(year, month, day, hour, minute, gender)

    if cache is not None:
        cache.set(key, bazi)

    return bazi
