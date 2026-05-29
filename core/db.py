"""
Backward-compatible wrapper — delegates to infrastructure.db.connection.
"""
from infrastructure.db.connection import (  # noqa: F401
    _raw_conn, _ctx_conn, get_conn, close_conn, init_db, SCHEMA_VERSION, SCHEMA_SQL,
)
