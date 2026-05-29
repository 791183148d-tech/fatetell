"""
Payment processing use case — Stripe checkout, webhook handling, status updates.

Orchestrates the payment lifecycle through abstract ports.
No framework imports.
"""

import logging

from application.interfaces import OrderRepository, PaymentRepository, PaymentGateway

logger = logging.getLogger("fatetell.use_case")


def create_checkout_session(order_id: str, price_cents: int,
                            gateway: PaymentGateway,
                            success_url: str, cancel_url: str) -> str:
    """Create a Stripe Checkout Session for an order."""
    return gateway.create_checkout_session(
        order_id=order_id,
        price_cents=price_cents,
        success_url=success_url,
        cancel_url=cancel_url,
    )


def handle_checkout_completed(session_data: dict,
                               payment_repo: PaymentRepository,
                               order_repo: OrderRepository) -> None:
    """
    Handle a successful Stripe Checkout session completion.

    Called from the webhook handler with verified session data.
    Maps the Stripe session to a payment record and marks the order as paid.
    """
    session_id = session_data.get("id", "")
    order_id = session_data.get("client_reference_id", "")
    payment_intent = session_data.get("payment_intent", "")
    amount = session_data.get("amount_total", 0)

    if not order_id:
        logger.error("No order_id in checkout.session.completed")
        return

    # Update payment record
    payment_repo.update_by_session(
        session_id,
        status="completed",
        stripe_payment_intent=payment_intent,
    )

    # Mark order as paid
    order_repo.set_status(order_id, "paid")
    logger.info("Order %s marked paid (session %s)", order_id, session_id)


def handle_payment_failed(session_data: dict,
                           payment_repo: PaymentRepository,
                           order_repo: OrderRepository) -> None:
    """Handle a failed Stripe payment."""
    session_id = session_data.get("id", "")
    order_id = session_data.get("client_reference_id", "")

    payment_repo.update_by_session(session_id, status="failed")

    if order_id:
        order_repo.set_status(order_id, "failed")
        logger.info("Order %s marked failed", order_id)
