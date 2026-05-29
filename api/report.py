"""Report display route."""

from flask import Blueprint, render_template, redirect, url_for

from models.order import get_order

report_bp = Blueprint("report", __name__)


@report_bp.route("/report/<order_id>")
def view_report(order_id):
    """Show a completed BaZi report."""
    order = get_order(order_id)
    if not order:
        return render_template("error.html", code=404, message="Report not found."), 404
    if not order["report_text"]:
        return redirect(url_for("payment.payment_success", order_id=order_id))

    return render_template(
        "report.html",
        name=order["name"],
        report=order["report_text"],
        order_id=order_id,
    )
