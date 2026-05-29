"""
User repository — SQLite persistence for the users table.

Depends on ``infrastructure.db.connection`` for connection management.
"""

import uuid
from typing import Optional
import bcrypt

from infrastructure.db.connection import get_conn


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_user(email: str, password: str, name: str = "") -> Optional[dict]:
    """Create a new user. Returns the user dict or None if email exists."""
    conn = get_conn()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return None

    user_id = uuid.uuid4().hex[:12]
    pw_hash = hash_password(password)
    conn.execute(
        "INSERT INTO users (id, email, password_hash, name) VALUES (?, ?, ?, ?)",
        (user_id, email, pw_hash, name),
    )
    conn.commit()
    return {"id": user_id, "email": email, "name": name}


def get_user_by_email(email: str) -> Optional[dict]:
    """Look up a user by email."""
    conn = get_conn()
    row = conn.execute(
        "SELECT id, email, password_hash, name, created_at FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "password_hash": row[2],
        "name": row[3],
        "created_at": row[4],
    }


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Look up a user by ID."""
    conn = get_conn()
    row = conn.execute(
        "SELECT id, email, name, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "name": row[2], "created_at": row[3]}


def get_user_orders(user_id: str, limit: int = 20) -> list:
    """Get orders belonging to a user."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, birth_data, status, created_at FROM orders "
        "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [
        {"id": r[0], "name": r[1], "birth_data": r[2], "status": r[3], "created_at": r[4]}
        for r in rows
    ]


def link_session_orders(user_id: str, session_id: str) -> int:
    """Assign existing session orders to a user on registration/login."""
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET user_id = ? WHERE session_id = ? AND user_id IS NULL",
        (user_id, session_id),
    )
    conn.commit()
    return conn.total_changes
