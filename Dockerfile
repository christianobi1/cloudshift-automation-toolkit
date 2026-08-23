# Dockerfile — production upgrade of the version already in cloud-automation-toolkit.
#
# What changed vs. the original teaching version, and why:
#   - multi-stage build: final image doesn't carry pip's build cache or compilers
#   - pinned base image: reproducible builds
#   - non-root user: container can't be used to gain root on the node if it's ever compromised
#   - gunicorn, not `python3 app.py`: a real WSGI server (workers, timeouts), not Flask's dev server
#   - HEALTHCHECK: lets `docker ps` / plain Docker show health too, not just Kubernetes
#
# iputils-ping is kept from the original Dockerfile because monitor.py / deploy.py
# in this repo may still use it for reachability checks.

# ---- Stage 1: build dependencies --------------------------------------

FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt


# ---- Stage 2: runtime image -------------------------------------------

FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends iputils-ping curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser

WORKDIR /app

# Bring in only the installed packages from the build stage.
COPY --from=builder /root/.local /home/appuser/.local

COPY --chown=appuser:appuser . .

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/healthz || exit 1

# 2 workers is enough for a small internal tool.
# Tune with WEB_CONCURRENCY in real production.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
