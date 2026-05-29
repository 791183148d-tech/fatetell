"""
Backward-compatible wrapper — delegates to infrastructure.stripe_gateway.
"""
from infrastructure.stripe_gateway import StripeService, StripeResult, stripe_service  # noqa: F401
