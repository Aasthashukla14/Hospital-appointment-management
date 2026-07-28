"""
Smoke test for the liveness/readiness probe.

Deliberately the only test that ships without a live Postgres instance:
`/health` has no DB dependency, so this can run in CI purely to confirm
the app boots and the ASGI app is wired correctly (all routers import
cleanly, middleware stack builds, etc.) before a real database is
available. Full CRUD / auth-flow testing is documented in README.md
under "API Testing Instructions" and exercised against a running
Postgres instance via Swagger UI or curl.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body
    assert "version" in body


def test_openapi_schema_is_served():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"]


def test_docs_ui_is_served():
    response = client.get("/docs")
    assert response.status_code == 200
