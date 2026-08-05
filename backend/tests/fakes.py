def fake_detector(text):
    """Devuelve un detector que ignora la imagen y emite una detección con `text`."""
    def _d(source):
        return [{"box": (0, 0, 10, 10), "text": text, "conf": 0.95}]
    return _d


class ConstDetector:
    """Detector picklable (para el pool de procesos): emite `text` fijo."""
    def __init__(self, text):
        self.text = text

    def __call__(self, source):
        return [{"box": (0, 0, 10, 10), "text": self.text, "conf": 0.95}]


def failing_detector(source):
    """Detector picklable que siempre falla (para probar aislamiento de errores)."""
    raise RuntimeError("ocr falló")
