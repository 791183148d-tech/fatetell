"""
Backward-compatible wrapper — delegates to infrastructure.report_task.
"""
from infrastructure.queue import register  # noqa: F401
from infrastructure.report_task import generate_report  # noqa: F401
