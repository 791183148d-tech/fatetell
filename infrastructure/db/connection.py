"""
Database connection management — shared across repository adapters.

Performance design:
- Context-aware ``_ctx_conn()`` reuses Flask's per-request connection
  inside request handlers, avoiding 1.4ms connect/close per CRUD call.
  Outside request context (background threads), falls back to a new
  connection that the caller must close.
- ``updated_at`` is set inline in UPDATE statements rather than via SQL
  triggers, eliminating a double-write on every mutation.
"""

import sqlite3
from pathlib import Path
from flask import g

from infrastructure.config import settings

_DB_URL = settings.db_url


def _resolve_path() -> Path:
    raw = _DB_URL.replace("sqlite:///", "", 1)
    p = Path(raw)
    if not p.is_absolute():
        p = Path(__file__).parent.parent.parent / raw
    return p


def _raw_conn() -> sqlite3.Connection:
    """Open a brand-new connection with correct PRAGMAs."""
    path = _resolve_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ctx_conn():
    """
    Return (connection, should_close).

    Inside a Flask request → returns the ``g``-cached connection
    (closed by teardown, caller must NOT close).
    Outside a request → returns a new connection (caller MUST close).
    """
    from flask import has_request_context
    if has_request_context():
        if "db" not in g:
            conn = _raw_conn()
            conn.execute("PRAGMA busy_timeout=5000")
            g.db = conn
        return g.db, False
    return _raw_conn(), True


def get_conn() -> sqlite3.Connection:
    """Per-request connection (cached in Flask ``g``)."""
    conn, _ = _ctx_conn()
    return conn


def close_conn(exception=None) -> None:
    """Teardown handler — closes the per-request connection."""
    conn = g.pop("db", None)
    if conn:
        conn.close()


# ── Schema / migration ─────────────────────────────────────────────────

SCHEMA_VERSION = 5

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT DEFAULT '',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id          TEXT PRIMARY KEY,
    user_id     TEXT REFERENCES users(id),
    session_id  TEXT DEFAULT '',
    name        TEXT DEFAULT 'You',
    birth_data  TEXT DEFAULT '',
    bazi_json   TEXT DEFAULT '',
    report_text TEXT DEFAULT '',
    status      TEXT DEFAULT 'pending',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id                    TEXT PRIMARY KEY,
    order_id              TEXT REFERENCES orders(id),
    amount                INTEGER DEFAULT 0,
    currency              TEXT DEFAULT 'usd',
    status                TEXT DEFAULT 'pending',
    stripe_session_id     TEXT DEFAULT '',
    stripe_payment_intent TEXT DEFAULT '',
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_session ON orders(session_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_session ON payments(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_payments_pi   ON payments(stripe_payment_intent);
"""


def init_db() -> None:
    """Run schema migration if needed. Idempotent."""
    conn = _raw_conn()
    conn.execute("PRAGMA busy_timeout=5000")

    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='_schema_version'"
    ).fetchone()
    current_ver = 0
    if existing:
        current_ver = conn.execute("SELECT MAX(version) FROM _schema_version").fetchone()[0] or 0

    if current_ver < SCHEMA_VERSION:
        # v4 → v5: add user_id + session_id columns to orders if missing
        if current_ver < 5:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
            if "user_id" not in cols:
                conn.execute("ALTER TABLE orders ADD COLUMN user_id TEXT REFERENCES users(id)")
            if "session_id" not in cols:
                conn.execute("ALTER TABLE orders ADD COLUMN session_id TEXT DEFAULT ''")

        # Run full schema (CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS)
        conn.executescript(SCHEMA_SQL)

        conn.execute("INSERT OR REPLACE INTO _schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
        conn.execute("DROP TRIGGER IF EXISTS trg_orders_updated")
        conn.execute("DROP TRIGGER IF EXISTS trg_payments_updated")
        conn.commit()
        conn.execute("VACUUM")
        conn.commit()

    conn.close()
