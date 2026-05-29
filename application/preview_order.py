"""
Preview order use case — create an order from the user's input form data.

Depends on abstract OrderRepository.  No framework imports.
"""

import logging

from application.interfaces import OrderRepository
from domain.bazi import calc_bazi

logger = logging.getLogger("fatetell.use_case")


def create_preview_order(order_id: str, name: str, session_id: str,
                         year: int, month: int, day: int,
                         hour: int, minute: int, gender: str,
                         repo: OrderRepository) -> dict:
    """
    Validate input, calculate BaZi, and persist a preview order.

    Returns the BaZi chart dict so the caller can render a preview.
    """
    # Validate date range
    if not (1900 <= year <= 2030):
        raise ValueError("Year must be between 1900 and 2030")
    if not (1 <= month <= 12):
        raise ValueError("Month must be between 1 and 12")
    if not (1 <= day <= 31):
        raise ValueError("Day must be between 1 and 31")
    if not (0 <= hour <= 23):
        raise ValueError("Hour must be between 0 and 23")

    bazi = calc_bazi(year, month, day, hour, minute, gender)

    import json
    birth = f"{year:04d}-{month:02d}-{day:02d}"
    repo.create(
        order_id=order_id,
        session_id=session_id,
        name=name,
        birth_data=birth,
        bazi_json=json.dumps(bazi, ensure_ascii=False),
    )

    return bazi
