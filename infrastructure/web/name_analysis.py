"""Name Analysis (姓名学) — Chinese name science routes."""

from flask import Blueprint, render_template, request

from domain.name_analysis import analyze_name

name_bp = Blueprint("name", __name__)


@name_bp.route("/name-analysis", methods=["GET", "POST"])
def index():
    """Name analysis page."""
    result = None
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        birth_year_str = request.form.get("birth_year", "").strip()

        if not name:
            error = "Please enter a name."
        else:
            try:
                birth_year = int(birth_year_str) if birth_year_str else None
                if birth_year and not (1900 <= birth_year <= 2100):
                    raise ValueError("Birth year must be between 1900 and 2100")
                result = analyze_name(name, birth_year)
            except ValueError as e:
                error = str(e)
            except Exception as e:
                error = f"Analysis error: {e}"

    return render_template("name_analysis.html", result=result, error=error)
