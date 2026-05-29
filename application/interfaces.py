"""
Application ports (abstract interfaces) — dependency inversion boundaries.

All concrete implementations live in ``infrastructure/`` and implement
these abstract classes.  Use cases depend on these ports, never on
concrete implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


# ── Cache ───────────────────────────────────────────────────────────────

class BaZiCache(ABC):
    """Cache for BaZi calculation results."""

    @abstractmethod
    def get(self, key: str) -> Optional[dict]:
        ...

    @abstractmethod
    def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        ...


# ── Repositories ────────────────────────────────────────────────────────

class OrderRepository(ABC):
    """Persistence for orders."""

    @abstractmethod
    def create(self, order_id: str, session_id: str = "", name: str = "You",
               birth_data: str = "", bazi_json: str = "") -> None:
        ...

    @abstractmethod
    def get(self, order_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    def update(self, order_id: str, **kwargs) -> None:
        ...

    @abstractmethod
    def get_by_session(self, session_id: str, limit: int = 10) -> list:
        ...

    @abstractmethod
    def get_status(self, order_id: str) -> str:
        ...

    @abstractmethod
    def set_status(self, order_id: str, status: str) -> None:
        ...


class PaymentRepository(ABC):
    """Persistence for payments."""

    @abstractmethod
    def create(self, payment_id: str, order_id: str, amount: int,
               stripe_session_id: str = "") -> None:
        ...

    @abstractmethod
    def update_by_session(self, stripe_session_id: str, **kwargs) -> None:
        ...

    @abstractmethod
    def get_by_session(self, stripe_session_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    def get_by_intent(self, payment_intent: str) -> Optional[dict]:
        ...


# ── Gateways ───────────────────────────────────────────────────────────

class ReportGateway(ABC):
    """External AI text-generation service (e.g. Claude)."""

    @abstractmethod
    def generate(self, bazi_data: dict, name: str) -> str:
        ...


class PaymentGateway(ABC):
    """External payment processor (e.g. Stripe)."""

    @abstractmethod
    def create_checkout_session(self, order_id: str, price_cents: int,
                                success_url: str, cancel_url: str) -> str:
        ...

    @abstractmethod
    def verify_webhook(self, payload: bytes, sig_header: str) -> dict:
        ...


# ── Task Queue ─────────────────────────────────────────────────────────

class TaskQueue(ABC):
    """Async job queue."""

    @abstractmethod
    def enqueue(self, task: str, *args, **kwargs) -> None:
        ...

    @abstractmethod
    def shutdown(self, wait: bool = True) -> None:
        ...
