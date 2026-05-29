"""
Payment routes — Stripe Checkout, Webhook, AJAX status polling.

Two modes:
  LIVE — real Stripe Checkout (STRIPE_SECRET_KEY set)
  DEMO — instant queue.enqueue for testing (no key)
"""

import json
import logging
import uuid

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, jsonify,
)

from infrastructure.config import settings
from infrastructure.queue import queue
from infrastructure.db.connection import _raw_conn
from infrastructure.db.order_repo import get_order, update_order, get_report_status
from infrastructure.db.payment_repo import create_payment, update_payment
from infrastructure.stripe_gateway import stripe_service
from infrastructure.web._utils import price_cents, get_price

logger = logging.getLogger("fatetell.payment")
payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/checkout/<order_id>")
def checkout(order_id):
    """Show checkout / payment page."""
    order = get_order(order_id)
    if not order:
        return redirect(url_for("main.index"))

    sk = settings.stripe_publishable_key
    logger.info("CHECKOUT stripe_key len=%s val=%s", len(sk) if sk else 0, repr(sk[:20] + "...") if sk else "EMPTY")
    logger.info("CHECKOUT is_live_mode=%s secret_key=%s", settings.is_live_mode, bool(settings.stripe_secret_key))

    return render_template(
        "payment.html",
        order_id=order_id,
        price=get_price(),
        name=order.get("name", "You"),
        stripe_key=sk,
    )


@payment_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Create Stripe Checkout Session — or enqueue for demo mode."""
    order_id = request.form.get("order_id") or session.get("order_id")
    if not order_id:
        return redirect(url_for("main.index"))

    order = get_order(order_id)
    if not order:
        return redirect(url_for("main.index"))

    if not settings.is_live_mode:
        queue.enqueue("generate_report", order_id)
        session["order_id"] = order_id
        return redirect(url_for("payment.payment_success", order_id=order_id))

    result = stripe_service.create_checkout_session(
        order_id=order_id,
        price_cents=price_cents(),
        success_url=request.host_url.rstrip("/") + url_for(
            "payment.payment_success", order_id=order_id
        ),
        cancel_url=request.host_url.rstrip("/") + url_for(
            "payment.payment_cancelled", order_id=order_id
        ),
    )

    if result.error:
        return render_template(
            "payment.html", order_id=order_id, price=get_price(),
            error="Payment system error. Please try again.",
        )

    create_payment(
        payment_id=uuid.uuid4().hex[:12],
        order_id=order_id,
        amount=price_cents(),
        stripe_session_id=result.session_id,
    )
    update_order(order_id, status="awaiting_payment")

    return redirect(result.session_url, code=303)


@payment_bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    """
    Stripe webhook — idempotent via stripe_payment_intent dedup.

    Atomic guard: uses BEGIN IMMEDIATE so two workers processing
    duplicate webhooks don't both start report generation.
    """
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    event = stripe_service.verify_webhook(payload, sig_header)
    if event is None:
        return jsonify({"error": "Invalid signature"}), 400

    evtype, evobj = stripe_service.parse_event(event)

    if evtype != "checkout.session.completed":
        return jsonify({"status": "ok"}), 200

    session_id = evobj.get("id", "")
    payment_intent = evobj.get("payment_intent", "")
    order_id = evobj.get("metadata", {}).get("order_id", "")
    if not session_id or not payment_intent or not order_id:
        return jsonify({"error": "Missing fields"}), 400

    conn = _raw_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT status FROM payments WHERE stripe_payment_intent = ?",
            (payment_intent,),
        ).fetchone()

        if existing and existing[0] == "completed":
            conn.commit()
            logger.info("Duplicate webhook — payment %s already processed", payment_intent)
            return jsonify({"status": "ok", "duplicate": True}), 200

        conn.execute(
            "UPDATE payments SET status = ?, stripe_payment_intent = ? "
            "WHERE stripe_session_id = ?",
            ("completed", payment_intent, session_id),
        )
        conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            ("paid", order_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Webhook atomic update failed")
        return jsonify({"error": "Processing failed"}), 500
    finally:
        conn.close()

    queue.enqueue("generate_report", order_id)
    logger.info("Payment confirmed for order %s — generation enqueued", order_id)

    return jsonify({"status": "ok"}), 200


@payment_bp.route("/payment/success")
def payment_success():
    """Payment success — shows status or redirects to report."""
    order_id = request.args.get("order_id") or session.get("order_id")
    if not order_id:
        return redirect(url_for("main.index"))

    order = get_order(order_id)
    if not order:
        return redirect(url_for("main.index"))

    if order["status"] == "completed" and order["report_text"]:
        return redirect(url_for("report.view_report", order_id=order_id))

    if order["status"] in ("pending", "preview"):
        queue.enqueue("generate_report", order_id)
        order = get_order(order_id)
        status = order["status"] if order else "generating"
    else:
        known = {"generating", "completed", "error"}
        status = order["status"] if order["status"] in known else "pending"

    return render_template(
        "payment_success.html",
        order_id=order_id,
        name=order["name"],
        status=status,
    )


@payment_bp.route("/payment/cancelled")
def payment_cancelled():
    order_id = request.args.get("order_id") or session.get("order_id")
    return render_template("payment_cancelled.html", order_id=order_id)


@payment_bp.route("/api/report-status/<order_id>")
def api_report_status(order_id):
    """Polled by frontend AJAX during report generation."""
    status = get_report_status(order_id)
    if status == "completed":
        return jsonify({
            "status": "completed",
            "redirect": url_for("report.view_report", order_id=order_id),
        })
    return jsonify({"status": status})
