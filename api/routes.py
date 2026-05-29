"""
Centralized blueprint registration — one call to register all.
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Import and register all route blueprints."""
    from api.main import main_bp
    from api.bazi import bazi_bp
    from api.payment import payment_bp
    from api.report import report_bp
    from api.learn import learn_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(bazi_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(learn_bp)
