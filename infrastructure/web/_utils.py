"""Internal helpers for web route modules (not exported)."""

import uuid
from flask import session

from infrastructure.config import settings


def get_session_id() -> str:
    """Get or create a persistent session ID."""
    if "session_id" not in session:
        session["session_id"] = uuid.uuid4().hex[:12]
        session.permanent = True
    return session["session_id"]


def get_price() -> float:
    return settings.report_price_usd


def price_cents() -> int:
    return int(get_price() * 100)
