"""
FateTell v3 — Application entry point.

Delegates to ``infrastructure.flask_app`` for the actual factory.
Kept as the top-level entry point for backward compatibility.

Usage:
    Development:  python app.py
    Production:   gunicorn run:app -c gunicorn.conf.py
"""

from infrastructure.flask_app import create_app
from infrastructure.config import settings

if __name__ == "__main__":
    port = settings.port
    create_app().run(debug=True, host="0.0.0.0", port=port)
