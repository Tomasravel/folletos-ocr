from __future__ import annotations
import numpy as np


def _as_pil(source):
    from PIL import Image
    if isinstance(source, np.ndarray):
        if source.ndim == 2:
            return Image.fromarray(source)
        return Image.fromarray(source[:, :, ::-1])
    return Image.open(source)


_easy_reader = None


def _get_easy_reader():
    global _easy_reader
    if _easy_reader is None:
        import easyocr
        try:
            import torch
            gpu = torch.cuda.is_available()
        except Exception:
            gpu = False
        _easy_reader = easyocr.Reader(["es", "en"], gpu=gpu)
    return _easy_reader


def detect_easyocr(source):
    reader = _get_easy_reader()
    src = source if isinstance(source, np.ndarray) else str(source)
    out = []
    for box, text, conf in reader.readtext(src, detail=1, paragraph=False):
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        out.append({"box": (min(xs), min(ys), max(xs), max(ys)),
                    "text": text, "conf": float(conf)})
    return out


_paddle = None


def _get_paddle():
    global _paddle
    if _paddle is None:
        from paddleocr import PaddleOCR
        # enable_mkldnn=False: el kernel oneDNN de Paddle rompe bajo emulación amd64
        # (Apple Silicon) con "ConvertPirAttribute2RuntimeAttribute not support".
        _paddle = PaddleOCR(lang="es", use_doc_orientation_classify=False,
                            use_doc_unwarping=False, use_textline_orientation=False,
                            enable_mkldnn=False)
    return _paddle


def detect_paddle(source):
    src = source if isinstance(source, np.ndarray) else str(source)
    res = _get_paddle().predict(src)
    out = []
    for page in res or []:
        texts = page.get("rec_texts", [])
        scores = page.get("rec_scores", [1.0] * len(texts))
        boxes = page.get("rec_boxes", None)
        polys = page.get("rec_polys", None)
        for i, text in enumerate(texts):
            if boxes is not None and i < len(boxes):
                x0, y0, x1, y1 = (float(v) for v in boxes[i])
            elif polys is not None and i < len(polys):
                xs = [p[0] for p in polys[i]]; ys = [p[1] for p in polys[i]]
                x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
            else:
                x0 = y0 = x1 = y1 = 0.0
            out.append({"box": (x0, y0, x1, y1), "text": text,
                        "conf": float(scores[i]) if i < len(scores) else 1.0})
    return out


def detect_tesseract(source):
    import pytesseract
    data = pytesseract.image_to_data(_as_pil(source), lang="spa+eng",
                                     output_type=pytesseract.Output.DICT)
    out = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = float(data["conf"][i])
        if not text or conf < 0:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        out.append({"box": (x, y, x + w, y + h), "text": text, "conf": conf / 100.0})
    return out


DETECTORS = {
    "tesseract": detect_tesseract,
    "easyocr": detect_easyocr,
    "paddleocr": detect_paddle,
}


def detections_to_text(dets, min_conf=0.0):
    return "\n".join(d["text"] for d in dets if d["conf"] >= min_conf)
