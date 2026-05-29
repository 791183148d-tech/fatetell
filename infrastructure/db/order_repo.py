"""
Order repository — all ``orders`` table operations.

Connection strategy:
- Inside a Flask request → reuses the per-request connection
  (``_ctx_conn``), no open/close overhead.
- Outside (background threads) → opens a fresh connection.
"""

from infrastructure.db.connection import _ctx_conn, _raw_conn

_ALLOWED_COLUMNS = frozenset(
    {"session_id", "name", "birth_data", "bazi_json", "report_text", "status"}
)


def _write(sql: str, params=()) -> None:
    conn = _raw_conn()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def create_order(order_id: str, session_id: str = "", name: str = "You",
                 birth_data: str = "", bazi_json: str = "") -> None:
    _write(
        "INSERT INTO orders (id, session_id, name, birth_data, bazi_json, status) "
        "VALUES (?,?,?,?,?,'pending')",
        (order_id, session_id, name, birth_data, bazi_json),
    )


def get_order(order_id: str) -> dict | None:
    conn, close = _ctx_conn()
    conn.row_factory = __import__("sqlite3").Row
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if close:
        conn.close()
    return dict(row) if row else None


def update_order(order_id: str, **kwargs) -> None:
    if not kwargs:
        return
    invalid = set(kwargs) - _ALLOWED_COLUMNS
    if invalid:
        raise ValueError(f"Invalid order columns: {invalid}")
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [order_id]
    _write(f"UPDATE orders SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", vals)


def get_orders_by_session(session_id: str, limit: int = 10) -> list[dict]:
    conn, close = _ctx_conn()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute(
        "SELECT * FROM orders WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    if close:
        conn.close()
    return [dict(r) for r in rows]


def get_report_status(order_id: str) -> str:
    conn, close = _ctx_conn()
    row = conn.execute(
        "SELECT status FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if close:
        conn.close()
    if not row:
        return "unknown"
    return row[0] if isinstance(row, tuple) else row["status"]


def set_report_status(order_id: str, status: str) -> None:
    update_order(order_id, status=status)
