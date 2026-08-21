"""
test_app.py — actual tests for app.py, run by the Jenkins pipeline's
Build & Test stage before any image is built or deployed.

(test_backup.py's current assertion — `os.path.exists(...) or True` —
always passes regardless of the real condition. These tests are written
to actually fail if the behavior they check breaks.)
"""

import app as app_module

client = app_module.app.test_client()


def _set(monkeypatch, **attrs):
    """Patch the already-imported app module's globals directly, rather
    than re-importing app.py per test — re-importing would re-run its
    module-level setup (logging config, etc.) on every test for no
    benefit."""
    for name, value in attrs.items():
        monkeypatch.setattr(app_module, name, value)


def test_healthz_returns_ok(monkeypatch):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_readyz_returns_ready(monkeypatch):
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ready"


def test_api_status_matches_original_contract(monkeypatch):
    """Locks in the exact response shape of the original app.py's `/`
    route, now served at /api/status, so nothing downstream that
    depends on it silently breaks."""
    resp = client.get("/api/status")

    assert resp.status_code == 200
    assert resp.get_json() == {
        "status": "ok",
        "service": "cloudshift-app",
    }


def test_crash_disabled_by_default(monkeypatch):
    """The most important test in this file: /crash must 403 unless
    DEMO_MODE is explicitly set to 'true'. If this test ever fails,
    do not ship the change that broke it."""
    _set(monkeypatch, DEMO_MODE=False)

    resp = client.get("/crash")

    assert resp.status_code == 403


def test_config_reports_hardcoded_when_no_configmap(monkeypatch):
    _set(monkeypatch, REDIS_HOST="not-configured")

    resp = client.get("/config")
    body = resp.get_json()

    assert body["redis_host"] == "not-configured"
    assert "hardcoded" in body["source"]


def test_config_reports_configmap_when_set(monkeypatch):
    _set(monkeypatch, REDIS_HOST="cache")

    resp = client.get("/config")
    body = resp.get_json()

    assert body["redis_host"] == "cache"
    assert body["source"] == "ConfigMap"


def test_index_page_renders(monkeypatch):
    resp = client.get("/")

    assert resp.status_code == 200
    assert b"CloudShift" in resp.data