#!/usr/bin/env python3

"""
CloudShift Status Dashboard — production build
-----------------------------------------------
This is an UPGRADE of the app.py already in cloud-automation-toolkit.

The original was:

    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    def home():
        return {"status": "ok", "service": "cloudshift-app"}

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)

That JSON response still exists below at /api/status, unchanged, so
anything that already depends on it keeps working.
"""

import logging
import os
import signal
import socket
import sys
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

# --- Structured-ish logging --------------------------------------------
# A real deployment would use JSON logging + a log shipper. This keeps it
# simple but still goes to stdout, which is what `kubectl logs` reads and
# what any log aggregator tails in production.
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s level=%(levelname)s msg=%(message)s",
)
log = logging.getLogger("cloudshift")

app = Flask(__name__)

# When this process started. Used to show "pod uptime" — the number that
# resets to zero every time Kubernetes restarts a crashed pod.
PROCESS_START = time.time()

# --- Config values ----------------------------------------------------
# In Lab Guide 4 these move from hardcoded strings into a ConfigMap.
# We read them from the environment with safe defaults so the app also
# runs fine locally with plain `docker run`, before any K8s concepts
# are applied — that's the "before" picture.
APP_VERSION = os.environ.get("APP_VERSION", "v1-local")
FLASK_ENV = os.environ.get("FLASK_ENV", "development")
REDIS_HOST = os.environ.get("REDIS_HOST", "not-configured")

# Off by default. Only the classroom ConfigMap sets this to "true".
# A real production ConfigMap should never set this.
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

# --- Pod identity -------------------------------------------------------
# POD_NAME and POD_IP are populated by the Kubernetes Downward API
# (see k8s/deployment.yaml, env: section referencing fieldRef).
# Locally / under plain Docker they fall back to the container hostname.
POD_NAME = os.environ.get("POD_NAME", socket.gethostname())
POD_IP = os.environ.get("POD_IP", "unknown")

# Detects whether we're running under gunicorn (see Dockerfile CMD) or
# directly via `python3 app.py` (local testing, no supervisor process).
# /crash needs to behave differently in each case — see that route below.
RUNNING_UNDER_GUNICORN = "gunicorn" in sys.argv[0]

# --- Request logging -----------------------------------------------------
@app.after_request
def _log_request(response):
    log.info(
        "request path=%s status=%s pod=%s",
        request.path,
        response.status_code,
        POD_NAME,
    )
    return response


def pod_uptime_seconds() -> int:
    return int(time.time() - PROCESS_START)


@app.route("/")
def index():
    return render_template(
        "index.html",
        pod_name=POD_NAME,
        pod_ip=POD_IP,
        uptime=pod_uptime_seconds(),
        version=APP_VERSION,
        env=FLASK_ENV,
        redis_host=REDIS_HOST,
        now=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


@app.route("/api/status")
def api_status():
    """Unchanged from the original app.py — kept for backward compatibility
    with anything that already calls this route."""
    return jsonify(status="ok", service="cloudshift-app")


@app.route("/healthz")
def healthz():
    """Liveness probe. Answers one question: is this process still alive
    and able to respond at all? If this stops responding, Kubernetes
    kills and replaces the pod — it does NOT ask whether the app is
    ready for traffic, only whether it should keep existing."""
    return jsonify(
        status="ok",
        pod=POD_NAME,
        uptime_seconds=pod_uptime_seconds(),
    )


@app.route("/readyz")
def readyz():
    """Readiness probe. Answers a different question: should THIS pod
    receive traffic right now? In a real app this would check its
    actual dependencies (database, cache, etc.) and return 503 if any
    of them are unreachable, so the Service stops routing to it until
    it recovers — without Kubernetes killing the pod over it."""
    return jsonify(status="ready", pod=POD_NAME)


@app.route("/config")
def config():
    """Shows exactly what Lab Guide 4 is teaching: which values came from
    the ConfigMap vs. which are hardcoded fallback defaults."""
    return jsonify(
        app_version=APP_VERSION,
        flask_env=FLASK_ENV,
        redis_host=REDIS_HOST,
        source=(
            "ConfigMap"
            if REDIS_HOST != "not-configured"
            else "hardcoded default (no ConfigMap applied)"
        ),
    )


@app.route("/crash")
def crash():
    """Disabled unless DEMO_MODE=true (see k8s/configmap.yaml). A real
    production deployment never sets DEMO_MODE, so this always 403s there.

    Why this kills the gunicorn MASTER process, not just this worker:
    the Dockerfile runs the app under gunicorn, which supervises 2 worker
    processes and quietly restarts any worker that dies — that's normally
    a good thing, but it means a plain os._exit(1) here would only kill
    one worker. Gunicorn would respawn it immediately, the container
    would never actually stop, and Kubernetes would never see a crash to
    heal from. To make the demo show what it's meant to show — a whole
    POD dying and Kubernetes noticing — we kill the master (our parent
    process) when running under gunicorn. When running locally via
    `python3 app.py` there's no supervisor, so a plain exit is enough.
    """
    if not DEMO_MODE:
        return jsonify(
            error="disabled: set DEMO_MODE=true to enable this demo endpoint"
        ), 403

    log.warning(
        "crash endpoint triggered on pod=%s — killing container",
        POD_NAME,
    )

    if RUNNING_UNDER_GUNICORN:
        os.kill(os.getppid(), signal.SIGKILL)
    else:
        os._exit(1)

    return jsonify(status="crashing"), 200  # likely never sent — the process is already dying


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)