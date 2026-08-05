import json
from fastapi.testclient import TestClient
from api.main import create_app
from folletos_ocr.config import Settings


def _client(tmp_path):
    s = Settings(api_token="", edits_dir=str(tmp_path), _env_file=None)
    return TestClient(create_app(settings=s))


def test_edits_appends_jsonl(tmp_path):
    c = _client(tmp_path)
    r = c.post("/edits", json={"records": [
        {"image": "a.jpg", "level": "avanzada", "run_id": "r1",
         "changes": {"cp": {"from": "08033", "to": "08034"}}}]})
    assert r.status_code == 200
    assert r.json()["saved"] == 1
    lines = (tmp_path / "edits.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["image"] == "a.jpg"
    assert rec["changes"]["cp"]["to"] == "08034"
    assert "ts" in rec  # server stamps a timestamp when missing


def test_edits_appends_multiple_calls(tmp_path):
    c = _client(tmp_path)
    c.post("/edits", json={"records": [{"image": "a.jpg", "changes": {}}]})
    c.post("/edits", json={"records": [{"image": "b.jpg", "changes": {}}]})
    lines = (tmp_path / "edits.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
