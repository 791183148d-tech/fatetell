"""BaZi routes: preview (conversion funnel), JSON API, compatibility."""

import json
import uuid
from flask import Blueprint, render_template, request, session, jsonify

from domain.bazi import TIAN_GAN_EN
from domain.rules import compatibility_score
from infrastructure.db.order_repo import create_order
from infrastructure.cache.memory import MemoryBackend
from application.calculate_bazi import get_or_calc_bazi
from infrastructure.web._utils import get_session_id, get_price

bazi_bp = Blueprint("bazi", __name__)
_cache = MemoryBackend()


@bazi_bp.route("/preview", methods=["POST"])
def preview():
    """Calculate BaZi chart and show free preview."""
    name = request.form.get("name", "You").strip() or "You"

    try:
        year = int(request.form["year"])
        month = int(request.form["month"])
        day = int(request.form["day"])
        hour = int(request.form.get("hour", 12))
        minute = int(request.form.get("minute", 0))
        gender = request.form.get("gender", "male")

        if not (1900 <= year <= 2030):
            raise ValueError("Year must be between 1900 and 2030")
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        if not (1 <= day <= 31):
            raise ValueError("Day must be between 1 and 31")
        if not (0 <= hour <= 23):
            raise ValueError("Hour must be between 0 and 23")
    except (ValueError, KeyError) as e:
        return render_template("input.html", error=f"Invalid input: {e}")

    try:
        bazi = get_or_calc_bazi(year, month, day, hour, minute, gender, _cache)
    except Exception as e:
        return render_template("input.html", error=f"Calculation error: {e}")

    order_id = uuid.uuid4().hex[:12]
    birth = f"{year:04d}-{month:02d}-{day:02d}"
    create_order(
        order_id=order_id,
        session_id=get_session_id(),
        name=name,
        birth_data=birth,
        bazi_json=json.dumps(bazi, ensure_ascii=False),
    )
    session["order_id"] = order_id

    return render_template(
        "preview.html",
        name=name,
        order_id=order_id,
        bazi=bazi,
        dm_gan=bazi["day_master"]["gan"],
        dm_en=TIAN_GAN_EN[bazi["day_master"]["gan_index"]],
        zodiac=bazi["extra"]["zodiac"],
        price=get_price(),
    )


@bazi_bp.route("/api/bazi", methods=["POST"])
def api_bazi():
    """REST API for BaZi calculation."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON"}), 400

    try:
        bazi = get_or_calc_bazi(
            int(data["year"]),
            int(data["month"]),
            int(data["day"]),
            int(data.get("hour", 12)),
            int(data.get("minute", 0)),
            data.get("gender", "male"),
            _cache,
        )
        return jsonify({"success": True, "data": bazi})
    except KeyError as e:
        return jsonify({"success": False, "error": f"Missing field: {e}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@bazi_bp.route("/compatibility", methods=["GET", "POST"])
def compatibility():
    """Compare two BaZi charts."""
    result = None
    if request.method == "POST":
        try:
            name1 = request.form.get("name1", "Person A") or "Person A"
            name2 = request.form.get("name2", "Person B") or "Person B"
            bazi1 = get_or_calc_bazi(
                int(request.form["year1"]), int(request.form["month1"]),
                int(request.form["day1"]), int(request.form.get("hour1", 12)),
                0, request.form.get("gender1", "male"), _cache,
            )
            bazi2 = get_or_calc_bazi(
                int(request.form["year2"]), int(request.form["month2"]),
                int(request.form["day2"]), int(request.form.get("hour2", 12)),
                0, request.form.get("gender2", "male"), _cache,
            )
            result = compatibility_score(bazi1, bazi2, name1, name2)
        except Exception as e:
            result = {"score": 0, "verdict": "Error", "analysis": str(e),
                      "name1": "Person A", "name2": "Person B",
                      "dm1": "?", "dm2": "?", "element1": "?", "element2": "?"}

    return render_template("compatibility.html", result=result)
