"""WSGI entry point for production (gunicorn on Railway)."""
import os
from infrastructure.flask_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5050")))
