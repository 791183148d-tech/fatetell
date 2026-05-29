"""
Internal helpers for API route modules (not exported via __init__).
"""

import uuid
from flask import session

from config import settings


def get_session_id() -> str:
    """Get or create a persistent session ID."""
    if "session_id" not in session:
        session["session_id"] = uuid.uuid4().hex[:12]
        session.permanent = True
    return session["session_id"]


def get_price() -> float:
    """Current report price in dollars."""
    return settings.report_price_usd


def price_cents() -> int:
    """Current report price in cents (for Stripe)."""
    return int(get_price() * 100)
