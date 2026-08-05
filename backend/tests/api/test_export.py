from fastapi.testclient import TestClient
from api.main import create_app
from folletos_ocr.config import Settings

def _client():
    return TestClient(create_app(settings=Settings(api_token="", _env_file=None)))

ROWS = [{"adreca": "X", "cp": "08033", "zt": "0803301",
         "fecha": "2025-06-03T12:19:13", "x_lon": -3.0, "y_lat": 40.0}]

def test_export_csv():
    r = _client().post("/export?fmt=csv", json={"rows": ROWS})
    assert r.status_code == 200 and "adreca" in r.text and "08033" in r.text

def test_export_json():
    r = _client().post("/export?fmt=json", json={"rows": ROWS})
    assert r.json()[0]["zt"] == "0803301"

def test_export_xlsx_content_type():
    r = _client().post("/export?fmt=xlsx", json={"rows": ROWS})
    assert r.status_code == 200
    assert "spreadsheet" in r.headers["content-type"]
