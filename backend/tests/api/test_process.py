import numpy as np
import cv2
from fastapi.testclient import TestClient
from api.main import create_app
from folletos_ocr.config import Settings
from api.routes import process as process_mod
from tests.fakes import fake_detector

def _png_bytes():
    ok, buf = cv2.imencode(".png", np.zeros((30, 30, 3), dtype=np.uint8))
    return buf.tobytes()

def _client(monkeypatch):
    monkeypatch.setattr(process_mod, "build_detectors",
                        lambda s: {"easyocr": fake_detector("Barcelona 08033")})
    monkeypatch.setattr(process_mod, "build_llm_fn", lambda s: None)
    monkeypatch.setattr(process_mod, "build_geocode_fn", lambda s: None)
    app = create_app(settings=Settings(enable_easyocr=True, enable_paddleocr=False,
                                       enable_llm=False, enable_geocoding=False,
                                       api_token="", _env_file=None))
    return TestClient(app)

def test_process_json_returns_final_fields(monkeypatch):
    c = _client(monkeypatch)
    r = c.post("/process?stream=false&level=rapida",
               files={"images": ("a.png", _png_bytes(), "image/png")})
    assert r.status_code == 200
    data = r.json()
    assert data[0]["fields"]["cp"] == "08033"

def test_process_stream_emits_sse(monkeypatch):
    c = _client(monkeypatch)
    with c.stream("POST", "/process?stream=true&level=rapida",
                  files={"images": ("a.png", _png_bytes(), "image/png")}) as r:
        body = "".join(chunk for chunk in r.iter_text())
    assert "data:" in body and "08033" in body
