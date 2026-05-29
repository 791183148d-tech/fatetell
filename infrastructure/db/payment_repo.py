"""
Payment repository — all ``payments`` table operations.

Connection strategy: same as ``order_repo`` — context-aware reads,
short-lived write conns.
"""

from infrastructure.db.connection import _ctx_conn, _raw_conn

_ALLOWED_COLUMNS = frozenset(
    {"status", "stripe_session_id", "stripe_payment_intent", "amount", "currency"}
)


def _write(sql: str, params=()) -> None:
    conn = _raw_conn()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def create_payment(payment_id: str, order_id: str, amount: int,
                   stripe_session_id: str = "") -> None:
    _write(
        "INSERT INTO payments (id, order_id, amount, stripe_session_id) VALUES (?,?,?,?)",
        (payment_id, order_id, amount, stripe_session_id),
    )


def update_payment(stripe_session_id: str, **kwargs) -> None:
    if not kwargs:
        return
    invalid = set(kwargs) - _ALLOWED_COLUMNS
    if invalid:
        raise ValueError(f"Invalid payment columns: {invalid}")
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [stripe_session_id]
    _write(
        f"UPDATE payments SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE stripe_session_id = ?",
        vals,
    )


def get_payment_by_session(stripe_session_id: str) -> dict | None:
    conn, close = _ctx_conn()
    conn.row_factory = __import__("sqlite3").Row
    row = conn.execute(
        "SELECT * FROM payments WHERE stripe_session_id = ?", (stripe_session_id,)
    ).fetchone()
    if close:
        conn.close()
    return dict(row) if row else None


def get_payment_by_intent(payment_intent: str) -> dict | None:
    conn, close = _ctx_conn()
    conn.row_factory = __import__("sqlite3").Row
    row = conn.execute(
        "SELECT * FROM payments WHERE stripe_payment_intent = ?", (payment_intent,)
    ).fetchone()
    if close:
        conn.close()
    return dict(row) if row else None
