import numpy as np
from folletos_ocr import engines

def test_detections_to_text_filters_by_conf():
    dets = [{"box": (0,0,1,1), "text": "a", "conf": 0.9},
            {"box": (0,0,1,1), "text": "b", "conf": 0.1}]
    assert engines.detections_to_text(dets, min_conf=0.5) == "a"

def test_registry_lists_known_engines():
    assert set(["easyocr", "paddleocr", "tesseract"]).issubset(engines.DETECTORS.keys())
