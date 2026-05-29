"""Centralized blueprint registration — one call to register all."""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Import and register all route blueprints."""
    from infrastructure.web.main import main_bp
    from infrastructure.web.bazi import bazi_bp
    from infrastructure.web.payment import payment_bp
    from infrastructure.web.report import report_bp
    from infrastructure.web.learn import learn_bp
    from infrastructure.web.qimen import qimen_bp
    from infrastructure.web.palm import palm_bp
    from infrastructure.web.liuyao import liuyao_bp
    from infrastructure.web.name_analysis import name_bp
    from infrastructure.web.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(bazi_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(learn_bp)
    app.register_blueprint(qimen_bp)
    app.register_blueprint(palm_bp)
    app.register_blueprint(liuyao_bp)
    app.register_blueprint(name_bp)
    app.register_blueprint(auth_bp)
