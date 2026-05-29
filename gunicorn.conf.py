"""
Gunicorn configuration — production deployment.

Usage:  gunicorn run:app -c gunicorn.conf.py
"""
import os
import multiprocessing

# Socket
bind = f"0.0.0.0:{os.getenv('PORT', '5050')}"

# Workers: (2 × CPU) + 1 is the standard formula
workers = int(os.getenv("WEB_CONCURRENCY", str(multiprocessing.cpu_count() * 2 + 1)))
worker_class = "sync"
timeout = 120  # Claude API calls can take 60+ seconds

# Logging
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = os.getenv("ACCESS_LOG", "-")
errorlog = os.getenv("ERROR_LOG", "-")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s'

# Safety
limit_request_line = 4096
max_requests = 1000  # Prevent memory leak
max_requests_jitter = 100

# Lifecycle
preload_app = True
graceful_timeout = 30


def on_starting(server):
    server.log.info("FateTell starting — %d workers", workers)


def when_ready(server):
    server.log.info("FateTell ready — listening on %s", bind)
