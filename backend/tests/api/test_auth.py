from fastapi.testclient import TestClient
from api.main import create_app
from folletos_ocr.config import Settings


def _client(token=""):
    app = create_app(settings=Settings(api_token=token, _env_file=None))
    return TestClient(app)


def test_open_when_no_token():
    assert _client("").get("/capabilities").status_code == 200


def test_rejects_without_header_when_token_set():
    assert _client("secret").get("/capabilities").status_code == 401


def test_accepts_with_valid_header():
    c = _client("secret")
    r = c.get("/capabilities", headers={"Authorization": "Bearer secret"})
    assert r.status_code == 200


def test_health_always_open():
    assert _client("secret").get("/health").status_code == 200
