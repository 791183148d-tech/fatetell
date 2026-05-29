"""
Backward-compatible wrapper — delegates to application.calculate_bazi.
"""
from application.calculate_bazi import get_or_calc_bazi, make_cache_key  # noqa: F401
from domain.rules import compatibility_score  # noqa: F401
