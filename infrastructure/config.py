"""
Configuration — single source of truth for all environment variables.

Reads from .env via python-dotenv, then falls back to env vars.
Export via the `Settings` dataclass so every module reads from one place.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Use absolute path so watchdog reloader (debug mode) finds .env too
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path, override=True)


@dataclass(frozen=True)
class Settings:
    # ── App ────────────────────────────────────────────────────────
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-key-change-me"))
    site_url: str = field(default_factory=lambda: os.getenv("SITE_URL", "http://localhost:5050"))
    port: int = int(os.getenv("PORT", "5050"))
    debug: bool = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    report_price_usd: float = float(os.getenv("REPORT_PRICE", "29.99"))

    # ── Claude / AI ────────────────────────────────────────────────
    claude_api_key: str = field(default_factory=lambda: os.getenv("CLAUDE_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 16000
    claude_timeout: int = 120

    # ── Stripe (all internal whitespace removed — Render pasting can
    #     embed \n / spaces inside the key) ───────────────────────────
    stripe_secret_key: str = field(default_factory=lambda: os.getenv("STRIPE_SECRET_KEY", "").translate(str.maketrans("", "", " \n\r\t")))
    stripe_publishable_key: str = field(default_factory=lambda: os.getenv("STRIPE_PUBLISHABLE_KEY", "").translate(str.maketrans("", "", " \n\r\t")))
    stripe_webhook_secret: str = field(default_factory=lambda: os.getenv("STRIPE_WEBHOOK_SECRET", "").translate(str.maketrans("", "", " \n\r\t")))

    # ── Rate limiting ──────────────────────────────────────────────
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 100

    # ── Database ───────────────────────────────────────────────────
    db_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///data/fatetell.db"))

    # ── Cache ──────────────────────────────────────────────────────
    cache_backend: str = field(default_factory=lambda: os.getenv("CACHE_BACKEND", "memory"))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))

    # ── Queue ──────────────────────────────────────────────────────
    queue_backend: str = field(default_factory=lambda: os.getenv("QUEUE_BACKEND", "thread"))
    queue_redis_url: str = field(default_factory=lambda: os.getenv("QUEUE_REDIS_URL", ""))

    @property
    def is_live_mode(self) -> bool:
        """Whether Stripe live mode is active."""
        return bool(self.stripe_secret_key)

    @property
    def preferred_api_key(self) -> str:
        """First available AI API key."""
        return self.claude_api_key or self.anthropic_api_key or self.deepseek_api_key


settings = Settings()
