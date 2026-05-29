"""
Production entry point for gunicorn:
    gunicorn run:app -c gunicorn.conf.py

Development:
    python run.py
"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    app.run(debug=True, host="0.0.0.0", port=port)
