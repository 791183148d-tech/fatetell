"""
Backward-compatible wrapper — delegates to infrastructure.db.payment_repo.
"""
from infrastructure.db.payment_repo import (  # noqa: F401
    create_payment, update_payment, get_payment_by_session, get_payment_by_intent,
)
