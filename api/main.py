"""
Public page routes: landing, input, about, daily, zodiac, SEO.
"""

import os
from pathlib import Path
from flask import Blueprint, render_template, send_from_directory, Response

from config import settings

main_bp = Blueprint("main", __name__)
STATIC_DIR = Path(__file__).parent.parent / "static"

# ── Pages ───────────────────────────────────────────────────────────

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


# ── SEO ─────────────────────────────────────────────────────────────

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
