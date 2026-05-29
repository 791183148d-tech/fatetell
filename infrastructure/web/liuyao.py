"""Liu Yao (六爻) — I Ching coin divination routes."""

from flask import Blueprint, render_template, jsonify

from domain.liuyao import calc_liuyao

liuyao_bp = Blueprint("liuyao", __name__)


@liuyao_bp.route("/liuyao")
def index():
    """Liu Yao divination page."""
    reading = None
    return render_template("liuyao.html", reading=reading)


@liuyao_bp.route("/api/liuyao/toss")
def api_toss():
    """API endpoint: toss coins and return hexagram result."""
    try:
        reading = calc_liuyao()
        return jsonify({"success": True, "data": reading})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
