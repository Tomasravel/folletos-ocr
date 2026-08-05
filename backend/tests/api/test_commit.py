from fastapi.testclient import TestClient
from api.main import create_app
from folletos_ocr.config import Settings


def test_commit_returns_not_configured():
    c = TestClient(create_app(settings=Settings(api_token="", _env_file=None)))
    r = c.post("/commit", json={"rows": []})
    assert r.status_code == 501
    assert "no configurado" in r.json()["detail"].lower()
