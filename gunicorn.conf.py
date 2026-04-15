"""
Gunicorn configuration for the ICS platform.

Start command:
  gunicorn ics_project.wsgi:application -c gunicorn.conf.py

Nginx should proxy to 127.0.0.1:8001 with upstream keepalive enabled.
"""

# ── Binding ───────────────────────────────────────────────────────────────────

bind = "127.0.0.1:8001"

# ── Workers ───────────────────────────────────────────────────────────────────

# Rule of thumb: (2 × CPU cores) + 1.  Adjust based on actual core count.
workers = 3
worker_class = "sync"

# Restart each worker after this many requests to limit memory growth.
# Jitter staggers the restarts so all workers don't restart simultaneously.
max_requests = 1000
max_requests_jitter = 50

# ── Timeouts ─────────────────────────────────────────────────────────────────

timeout = 120           # kill worker if it takes longer than 2 minutes
keepalive = 5           # seconds to wait for next request on a keep-alive connection
                        # match Nginx's upstream keepalive_timeout

# ── Memory ───────────────────────────────────────────────────────────────────

# Load the Django app before forking workers (copy-on-write memory sharing).
preload_app = True

# ── Logging ───────────────────────────────────────────────────────────────────

accesslog = "/var/log/gunicorn/ics_access.log"
errorlog = "/var/log/gunicorn/ics_error.log"
loglevel = "warning"
capture_output = True   # redirect worker stdout/stderr to errorlog
