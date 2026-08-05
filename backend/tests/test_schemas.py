from folletos_ocr.schemas import Fields, Detection, Stage


def test_fields_defaults_none():
    f = Fields()
    assert f.adreca is None and f.cp is None and f.zt is None
    assert f.fecha is None and f.x_lon is None and f.y_lat is None


def test_stage_serializes():
    st = Stage(name="ocr:easyocr", ok=True, ms=120,
              detections=[Detection(box=(0, 0, 1, 1), text="hola", conf=0.9)])
    d = st.model_dump()
    assert d["name"] == "ocr:easyocr"
    assert d["detections"][0]["text"] == "hola"
