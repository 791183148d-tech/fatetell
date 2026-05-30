"""Public page routes: landing, input, about, daily, zodiac, SEO."""

from pathlib import Path
from flask import Blueprint, render_template, send_from_directory, Response

from infrastructure.config import settings

main_bp = Blueprint("main", __name__)
STATIC_DIR = Path(__file__).parent.parent.parent / "static"


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/input")
def input_page():
    return render_template("input.html")


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/daily")
def daily():
    return render_template("daily.html")


@main_bp.route("/zodiac")
def zodiac():
    return render_template("zodiac.html")


@main_bp.route("/debug/env")
def debug_env():
    from infrastructure.config import settings
    from infrastructure.stripe_gateway import stripe_service
    sk = settings.stripe_secret_key
    pk = settings.stripe_publishable_key
    dk = settings.deepseek_api_key
    return {
        "stripe_secret_configured": bool(sk),
        "stripe_secret_prefix": sk[:10] + "..." if sk else "",
        "stripe_publishable_configured": bool(pk),
        "stripe_publishable_prefix": pk[:10] + "..." if pk else "",
        "deepseek_configured": bool(dk),
        "deepseek_prefix": dk[:10] + "..." if dk else "",
        "is_live_mode": settings.is_live_mode,
        "stripe_client_initialized": stripe_service._client is not None,
        "site_url": settings.site_url,
        "port": settings.port,
    }


@main_bp.route("/debug/test-stripe")
def debug_test_stripe():
    """Directly test Stripe session creation."""
    from infrastructure.stripe_gateway import stripe_service
    from infrastructure.web._utils import price_cents
    result = stripe_service.create_checkout_session(
        order_id="test-debug-001",
        price_cents=price_cents(),
        success_url=settings.site_url.rstrip("/") + "/payment/success",
        cancel_url=settings.site_url.rstrip("/") + "/payment/cancelled",
    )
    return {
        "has_error": bool(result.error),
        "error": result.error,
        "has_session_url": bool(result.session_url),
        "session_url_prefix": result.session_url[:50] + "..." if result.session_url else "",
        "session_id": result.session_id,
        "is_demo": result.is_demo,
    }


@main_bp.route("/robots.txt")
def robots():
    site_url = settings.site_url
    return Response(
        f"User-agent: *\nDisallow:\nSitemap: {site_url}/sitemap.xml\n",
        mimetype="text/plain",
    )


@main_bp.route("/sitemap.xml")
def sitemap():
    site_url = settings.site_url
    pages = ["", "/input", "/learn", "/daily", "/zodiac", "/compatibility", "/about"]
    urlset = "\n".join(
        f"  <url><loc>{site_url}{p}</loc><changefreq>weekly</changefreq></url>"
        for p in pages
    )
    return Response(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urlset}\n</urlset>',
        mimetype="application/xml",
    )


@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(STATIC_DIR, "favicon.ico", mimetype="image/svg+xml")
