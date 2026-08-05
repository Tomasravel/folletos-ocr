from fastapi.testclient import TestClient
from api.main import create_app


def test_health_ok():
    c = TestClient(create_app())
    assert c.get("/health").json() == {"status": "ok"}


def test_capabilities_shape():
    c = TestClient(create_app())
    body = c.get("/capabilities").json()
    assert "levels" in body and "engines" in body and "parsers" in body
