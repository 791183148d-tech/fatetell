"""Qimen Dunjia (奇门遁甲) routes: query and chart display."""

from flask import Blueprint, render_template, request

from domain.qimen import calc_qimen

qimen_bp = Blueprint("qimen", __name__)


@qimen_bp.route("/qimen", methods=["GET", "POST"])
def index():
    """Qimen Dunjia query page."""
    chart = None
    error = None

    if request.method == "POST":
        try:
            year = int(request.form.get("year", 2026))
            month = int(request.form.get("month", 1))
            day = int(request.form.get("day", 1))
            hour = int(request.form.get("hour", 12))
            minute = int(request.form.get("minute", 0))

            if not (1900 <= year <= 2100):
                raise ValueError("Year must be between 1900 and 2100")
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12")
            if not (1 <= day <= 31):
                raise ValueError("Day must be between 1 and 31")
            if not (0 <= hour <= 23):
                raise ValueError("Hour must be between 0 and 23")
            if not (0 <= minute <= 59):
                raise ValueError("Minute must be between 0 and 59")

            chart = calc_qimen(year, month, day, hour, minute)
        except (ValueError, KeyError) as e:
            error = str(e)
        except Exception as e:
            error = f"Calculation error: {e}"

    return render_template("qimen.html", chart=chart, error=error)
