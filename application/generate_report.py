"""
Report generation use case — queue-based AI report generation.

Orchestrates: fetch order → find/generate BaZi → call AI → persist report.
Depends on abstract ports (OrderRepository, BaZiCache, ReportGateway, TaskQueue).
No framework imports.
"""

import logging

from domain.bazi import calc_bazi
from application.interfaces import OrderRepository, ReportGateway, TaskQueue

logger = logging.getLogger("fatetell.use_case")


def generate_report(order_id: str, repo: OrderRepository, ai: ReportGateway) -> None:
    """
    Generate a BaZi report for the given order.

    Intended to be run as an async background task.
    """
    order = repo.get(order_id)
    if not order:
        logger.error("generate_report: order %s not found", order_id)
        return

    repo.set_status(order_id, "generating")

    # Parse birth data from order
    try:
        parts = order.get("birth_data", "").split("-")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        hour = 12  # default noon
        minute = 0
        gender = "male"
    except (ValueError, IndexError):
        logger.exception("Invalid birth_data for order %s", order_id)
        repo.set_status(order_id, "failed")
        return

    # Calculate / fetch BaZi chart
    bazi = calc_bazi(year, month, day, hour, minute, gender)

    # Generate report via AI gateway
    try:
        name = order.get("name", "You")
        report_text = ai.generate(bazi, name)
    except Exception:
        logger.exception("AI report generation failed for order %s", order_id)
        repo.set_status(order_id, "failed")
        return

    # Persist report
    repo.update(order_id, report_text=report_text, status="completed")
    logger.info("Report %s generated successfully", order_id)


def start_report_generation(order_id: str, repo: OrderRepository,
                             ai: ReportGateway, queue: TaskQueue) -> None:
    """Enqueue report generation as an async task."""
    repo.set_status(order_id, "queued")
    queue.enqueue("generate_report", order_id)
    logger.info("Report generation queued for order %s", order_id)
