from __future__ import annotations
import cv2
import numpy as np


def _scale(img):
    h, w = img.shape[:2]
    return max(0.4, min(w, h) / 1000.0)


def annotate_boxes(img: np.ndarray, dets: list[dict]) -> np.ndarray:
    out = img.copy()
    s = _scale(out)
    for d in dets:
        x0, y0, x1, y1 = (int(v) for v in d["box"])
        cv2.rectangle(out, (x0, y0), (x1, y1), (0, 255, 0), max(1, int(2 * s)))
        cv2.putText(out, f"{d['conf']:.2f}", (x0, max(0, y0 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5 * s, (0, 255, 0), max(1, int(s)))
    return out


def annotate_fields(img: np.ndarray, fields: dict) -> np.ndarray:
    h, w = img.shape[:2]
    s = _scale(img)
    panel_h = int(180 * s)
    panel = np.full((panel_h, w, 3), 30, dtype=np.uint8)
    y = int(28 * s)
    for k in ["adreca", "cp", "zt", "fecha", "x_lon", "y_lat"]:
        cv2.putText(panel, f"{k}: {fields.get(k)}", (int(12 * s), y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6 * s, (255, 255, 255), max(1, int(s)))
        y += int(26 * s)
    return np.vstack([img, panel])
