"""
FateTell v3 — Flask application factory.

Wires together infrastructure adapters:
    infrastructure/db/      →  SQLite connection + repositories
    infrastructure/web/     →  Route blueprints + middleware
    infrastructure/cache/   →  BaZi result caching
    infrastructure/queue/   →  Background task processing
    infrastructure/config   →  Environment-based settings
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template

from infrastructure.config import settings


_PROJECT_ROOT = Path(__file__).parent.parent


def create_app(testing: bool = False) -> Flask:
    """Create and fully configure a Flask instance."""
    app = Flask(
        __name__,
        template_folder=str(_PROJECT_ROOT / "templates"),
        static_folder=str(_PROJECT_ROOT / "static"),
    )

    app.secret_key = settings.secret_key
    app.config.update(
        TESTING=testing,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=not testing and settings.site_url.startswith("https"),
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        MAX_CONTENT_LENGTH=1024 * 1024,
    )

    app.jinja_env.auto_reload = app.debug
    _setup_template_cache(app)

    _configure_logging(app)

    # ── Database ───────────────────────────────────────────────────
    from infrastructure.db import init_db, close_conn

    with app.app_context():
        init_db()
    app.teardown_appcontext(close_conn)

    # ── Error pages ────────────────────────────────────────────────
    _register_error_pages(app)

    # ── Template globals ───────────────────────────────────────────
    _register_template_globals(app)

    # ── Middleware ─────────────────────────────────────────────────
    from infrastructure.web.middleware import register_middleware, register_health_check

    register_middleware(app)
    register_health_check(app)

    # ── Ensure background task is registered ──────────────────────
    import infrastructure.report_task  # noqa: F401 — fires @register decorator

    # ── Routes ─────────────────────────────────────────────────────
    from infrastructure.web.routes import register_blueprints

    register_blueprints(app)

    if not testing:
        _log_routes(app)

    return app


# ── Internal helpers ────────────────────────────────────────────────────

def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    for noisy in ("urllib3", "stripe", "anthropic", "httpx", "httpcore", "charset_normalizer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    app.logger.info("FateTell v3 initializing (log level: %s)", "DEBUG" if app.debug else "INFO")


def _register_error_pages(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Internal server error")
        return render_template("error.html", code=500, message="Something went wrong."), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="Access denied."), 403

    @app.errorhandler(413)
    def too_large(e):
        return render_template("error.html", code=413, message="Request too large."), 413


def make_opts(start, end, step=1, fmt="{!s}"):
    """Build select options as (value, label) tuples for Jinja2 templates."""
    return [(i, fmt.format(i)) for i in range(start, end, step)]


def _register_template_globals(app: Flask) -> None:
    import markdown as _md

    @app.template_filter("markdown")
    def render_markdown(text: str) -> str:
        """Convert Markdown text to safe HTML."""
        if not text:
            return ""
        return _md.markdown(text, extensions=["extra", "codehilite"])

    @app.context_processor
    def inject_globals():
        return {
            "today": datetime.now(),
            "site_name": "FateTell",
            "report_price": settings.report_price_usd,
            "make_opts": make_opts,
        }


def _setup_template_cache(app: Flask) -> None:
    cache_dir = Path(app.instance_path) / "jinja_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    from jinja2 import FileSystemBytecodeCache
    app.jinja_env.bytecode_cache = FileSystemBytecodeCache(
        str(cache_dir), "%s.cache"
    )


def _log_routes(app: Flask) -> None:
    rules = sorted(
        r.rule for r in app.url_map.iter_rules()
        if r.rule.startswith("/") and "static" not in r.rule
    )
    app.logger.info("Routes registered: %d", len(rules))
    for r in rules:
        app.logger.debug("  %s", r)
