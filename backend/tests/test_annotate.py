import numpy as np
from folletos_ocr.annotate import annotate_boxes, annotate_fields


def _img():
    return np.zeros((400, 600, 3), dtype=np.uint8)


def test_annotate_boxes_returns_same_shape():
    dets = [{"box": (10, 10, 100, 40), "text": "hola", "conf": 0.9}]
    out = annotate_boxes(_img(), dets)
    assert out.shape == (400, 600, 3) and out.dtype == np.uint8


def test_annotate_fields_returns_image_with_panel():
    out = annotate_fields(_img(), {"adreca": "X", "cp": "08033", "zt": "0803301",
                                   "fecha": None, "x_lon": None, "y_lat": None})
    assert out.shape[0] >= 400 and out.shape[1] == 600
