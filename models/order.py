"""
Backward-compatible wrapper — delegates to infrastructure.db.order_repo.
"""
from infrastructure.db.order_repo import (  # noqa: F401
    create_order, get_order, update_order, get_orders_by_session,
    get_report_status, set_report_status,
)
