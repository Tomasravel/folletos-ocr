from fastapi.testclient import TestClient
from api.main import create_app
from folletos_ocr.config import Settings

def _client(tmp_path):
    s = Settings(api_token="", debug_dir=str(tmp_path), _env_file=None)
    return TestClient(create_app(settings=s)), tmp_path

def test_get_artifact(tmp_path):
    c, base = _client(tmp_path)
    run = base / "run1" / "img.jpg"; run.mkdir(parents=True)
    (run / "trace.json").write_text('{"status":"ok"}')
    r = c.get("/debug/run1/img.jpg/trace.json")
    assert r.status_code == 200 and r.json()["status"] == "ok"

def test_bundle_zip(tmp_path):
    c, base = _client(tmp_path)
    run = base / "run1" / "img.jpg"; run.mkdir(parents=True)
    (run / "trace.json").write_text("{}")
    r = c.get("/debug/run1/bundle.zip")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
