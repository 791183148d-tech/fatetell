"""
Concrete report-generation task — registered with the queue.

This is the bridge between the abstract application use case and
the concrete infrastructure: it performs DI by importing the real
dependencies (order_repo, claude_gateway, config).
"""

import json
import logging

from infrastructure.config import settings
from infrastructure.queue import register, queue
from infrastructure.db.order_repo import get_order, update_order, set_report_status
from infrastructure.claude_gateway import generate_report as gen_ai_report

logger = logging.getLogger("fatetell.report")


@register("generate_report")
def generate_report(order_id: str) -> None:
    """Generate a BaZi report for the given order (runs in background thread)."""
    try:
        set_report_status(order_id, "generating")
        order = get_order(order_id)
        if not order:
            logger.error("Order %s not found", order_id)
            set_report_status(order_id, "error")
            return

        bazi = json.loads(order["bazi_json"])
        api_key = settings.preferred_api_key

        if api_key:
            report = gen_ai_report(bazi, api_key)
        else:
            from infrastructure.claude_gateway import _sample_report
            report = _sample_report(bazi)

        update_order(order_id, report_text=report, status="completed")
        logger.info("Report completed for order %s (%d chars)", order_id, len(report))

    except Exception as e:
        logger.exception("Report generation failed for order %s: %s", order_id, e)
        try:
            set_report_status(order_id, "error")
        except Exception:
            pass
