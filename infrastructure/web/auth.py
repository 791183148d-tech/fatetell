"""
Auth routes — user registration, login, logout, and account management.

Uses session-based auth (no Flask-Login dependency).
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from infrastructure.db.user_repo import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_orders,
    check_password,
    link_session_orders,
)
from infrastructure.web._utils import get_session_id

logger = logging.getLogger("fatetell.auth")
auth_bp = Blueprint("auth", __name__)


def login_required(f):
    """Decorator to require login."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "info")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return wrapper


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration page."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        name = request.form.get("name", "").strip() or email.split("@")[0]

        if not email or "@" not in email:
            return render_template("register.html", error="Please enter a valid email address.")
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters.")
        if password != confirm:
            return render_template("register.html", error="Passwords do not match.")

        user = create_user(email, password, name)
        if not user:
            return render_template("register.html", error="An account with this email already exists.")

        # Log in immediately
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session.permanent = True

        # Link any anonymous session orders
        sid = get_session_id()
        linked = link_session_orders(user["id"], sid)
        if linked:
            logger.info("Linked %d session orders to user %s", linked, user["id"])

        flash("Account created successfully!", "success")
        next_url = request.args.get("next") or url_for("auth.account")
        return redirect(next_url)

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="Please enter both email and password.")

        user = get_user_by_email(email)
        if not user or not check_password(password, user["password_hash"]):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session.permanent = True

        # Link session orders
        sid = get_session_id()
        linked = link_session_orders(user["id"], sid)
        if linked:
            logger.info("Linked %d session orders to user %s", linked, user["id"])

        flash("Welcome back!", "success")
        next_url = request.args.get("next") or url_for("auth.account")
        return redirect(next_url)

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Log out the current user."""
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/account")
@login_required
def account():
    """User account dashboard — order history and profile."""
    user = get_user_by_id(session["user_id"])
    orders = get_user_orders(session["user_id"])
    return render_template("account.html", user=user, orders=orders)
