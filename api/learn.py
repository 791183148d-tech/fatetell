"""
Educational content routes — the BaZi learning center.
Consolidated into a single dynamic route.
"""

from flask import Blueprint, render_template

learn_bp = Blueprint("learn", __name__)

_TOPIC_MAP = {
    "wuxing": "learn_wuxing.html",
    "stems": "learn_stems.html",
    "branches": "learn_branches.html",
    "zodiac": "learn_zodiac.html",
    "tenshen": "learn_tenshen.html",
    "dayun": "learn_dayun.html",
}


@learn_bp.route("/learn")
def index():
    return render_template("learn.html")


@learn_bp.route("/learn/<topic>")
def topic(topic):
    template = _TOPIC_MAP.get(topic)
    if template:
        return render_template(template)
    return render_template("error.html", code=404, message="Page not found."), 404
