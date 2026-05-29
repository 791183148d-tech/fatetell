"""
Stripe payment gateway — lazy-init, two modes (live / demo).

Implements the PaymentGateway port from application/interfaces.py.
Live mode: real Stripe Checkout sessions.
Demo mode: instant report generation (no Stripe key configured).
"""

import json
import logging
from dataclasses import dataclass

from infrastructure.config import settings

logger = logging.getLogger("fatetell.stripe")


@dataclass
class StripeResult:
    session_url: str = ""
    session_id: str = ""
    error: str = ""
    is_demo: bool = False


class StripeService:
    """Thin wrapper around the Stripe SDK."""

    def __init__(self):
        self._client = None
        self._init()

    def _init(self) -> None:
        if not settings.is_live_mode:
            logger.info("Stripe: demo mode (no secret key)")
            return
        try:
            import stripe
            stripe.api_key = settings.stripe_secret_key
            self._client = stripe
            logger.info("Stripe: live mode")
        except ImportError:
            logger.warning("Stripe: package not installed, falling back to demo")

    @property
    def publishable_key(self) -> str:
        return settings.stripe_publishable_key

    @property
    def webhook_secret(self) -> str:
        return settings.stripe_webhook_secret

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def create_checkout_session(self, order_id: str, price_cents: int,
                                success_url: str, cancel_url: str) -> StripeResult:
        """Create a Stripe Checkout Session (or return demo result)."""
        if not self._client:
            from infrastructure.queue import queue
            queue.enqueue("generate_report", order_id)
            return StripeResult(is_demo=True)

        try:
            session = self._client.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "BaZi Life Reading Report",
                            "description": "Complete AI-powered BaZi life reading — 10,000+ words.",
                        },
                        "unit_amount": price_cents,
                    },
                    "quantity": 1,
                }],
                metadata={"order_id": order_id},
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return StripeResult(
                session_url=session.url,
                session_id=session.id,
            )
        except Exception as e:
            logger.exception("Stripe session creation failed")
            return StripeResult(error=str(e))

    def verify_webhook(self, payload: bytes, sig_header: str) -> dict | None:
        """Verify and parse a Stripe webhook event. Returns None on failure."""
        if not self._client or not self.webhook_secret:
            return json.loads(payload)
        try:
            event = self._client.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event if isinstance(event, dict) else event.to_dict_recursive()
        except Exception as e:
            logger.warning("Webhook signature invalid: %s", e)
            return None

    @staticmethod
    def parse_event(event: dict) -> tuple:
        """Extract (type, object_dict) from a Stripe event."""
        return (event.get("type", ""), event.get("data", {}).get("object", {}))


stripe_service = StripeService()
