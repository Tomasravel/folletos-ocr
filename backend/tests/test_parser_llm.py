import json
from folletos_ocr.parser_llm import parse_llm

class FakeClient:
    def __init__(self, payload): self._payload = payload
    def chat(self, **kwargs):
        return {"message": {"content": json.dumps(self._payload)}}

def test_parse_llm_maps_fields():
    fake = FakeClient({"adreca": "Carrer X 8", "cp": "08033",
                       "fecha": "2025-06-03T12:19:13", "x_lon": None, "y_lat": None})
    out = parse_llm("texto ocr", model="m", client=fake)
    assert out["adreca"] == "Carrer X 8"
    assert out["zt"] == "0803301"

def test_parse_llm_bad_json_returns_empty():
    class Bad:
        def chat(self, **kwargs): return {"message": {"content": "no-json"}}
    out = parse_llm("t", model="m", client=Bad())
    assert out["adreca"] is None and out["cp"] is None
