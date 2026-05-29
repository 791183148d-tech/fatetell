"""
Security & infrastructure middleware.

- Security headers (XSS, clickjacking, MIME sniffing)
- Cache control for static assets
- Health check endpoint (k8s / Docker HEALTHCHECK)
- Rate limiting (token bucket, per-IP)
- Structured JSON error responses for API routes
"""

import time
import logging
from flask import Flask, request, jsonify

from infrastructure.config import settings

logger = logging.getLogger("fatetell.middleware")


class TokenBucket:
    """Per-IP token bucket rate limiter."""

    def __init__(self, rate: int, burst: int):
        self._rate = rate
        self._burst = burst
        self._buckets: dict[str, dict] = {}

    def check(self, ip: str) -> bool:
        now = time.time()
        bucket = self._buckets.get(ip)
        if bucket is None:
            self._buckets[ip] = {"tokens": self._burst - 1, "last": now}
            return True

        elapsed = now - bucket["last"]
        bucket["tokens"] = min(self._burst, bucket["tokens"] + elapsed * self._rate / 60.0)
        bucket["last"] = now

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True

        return False


_rate_limiter = TokenBucket(settings.rate_limit_per_minute, settings.rate_limit_burst)


def register_middleware(app: Flask) -> None:
    """Register all middleware on the app."""

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )

        if request.path.startswith("/static/"):
            response.headers.setdefault("Cache-Control", "public, max-age=86400, immutable")

        return response

    @app.before_request
    def rate_limit():
        if request.path.startswith("/api/") and request.method in ("POST", "PUT", "DELETE"):
            ip = request.remote_addr or "unknown"
            if not _rate_limiter.check(ip):
                return jsonify({"success": False, "error": "Rate limit exceeded. Try again shortly."}), 429

    @app.errorhandler(429)
    def ratelimit_error(e):
        return jsonify({"success": False, "error": "Rate limit exceeded"}), 429


def register_health_check(app: Flask) -> None:
    """Lightweight health check — no DB hit."""
    @app.route("/healthz")
    def healthz():
        return {"status": "ok", "app": "FateTell", "version": "3.0", "uptime": time.time()}
