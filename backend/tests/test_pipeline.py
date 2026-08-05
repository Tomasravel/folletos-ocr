import numpy as np
from folletos_ocr.pipeline import run_pipeline, run_batch, resolve_workers
from folletos_ocr.config import Settings
from folletos_ocr.debug import DebugRecorder
from tests.fakes import fake_detector, ConstDetector, failing_detector

IMG = np.zeros((50, 50, 3), dtype=np.uint8)
OCR_TEXT = "Carrer X 8\nBarcelona 08033\n2025-06-03 12:19:13"


def _deps(**over):
    base = dict(
        detectors={"easyocr": fake_detector(OCR_TEXT), "paddleocr": fake_detector(OCR_TEXT)},
        llm_fn=lambda text, model: {"adreca": "Carrer X 8", "cp": "08033",
                                    "zt": "0803301", "fecha": "2025-06-03T12:19:13",
                                    "x_lon": None, "y_lat": None},
        geocode_fn=lambda addr: (40.0, -3.0),
    )
    base.update(over)
    return base


def test_rapida_emits_one_fast_event():
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=True, _env_file=None)
    events = list(run_pipeline(IMG, "img0", level="rapida", settings=s, **_deps()))
    assert len(events) == 1
    assert events[0].stage == "fast"
    assert events[0].fields.cp == "08033"


def test_media_emits_single_easyocr_llm_event():
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=True, _env_file=None)
    events = list(run_pipeline(IMG, "img0", level="media", settings=s, **_deps()))
    assert len(events) == 1
    assert events[0].engine == "easyocr" and events[0].parser == "llm"


def test_avanzada_emits_single_paddleocr_llm_event():
    s = Settings(enable_easyocr=True, enable_paddleocr=True, enable_llm=True, _env_file=None)
    events = list(run_pipeline(IMG, "img0", level="avanzada", settings=s, **_deps()))
    assert len(events) == 1
    assert events[-1].engine == "paddleocr" and events[-1].parser == "llm"


def test_avanzada_without_paddle_degrades_with_warning():
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=True, _env_file=None)
    events = list(run_pipeline(IMG, "img0", level="avanzada", settings=s, **_deps()))
    assert any(e.warnings for e in events)


def test_strict_rejects_when_missing():
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=True,
                 reject_on_missing=True, _env_file=None)
    import pytest
    with pytest.raises(ValueError):
        list(run_pipeline(IMG, "img0", level="avanzada", settings=s, **_deps()))


def test_geocode_fills_coords_when_overlay_missing():
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=False,
                 enable_geocoding=True, _env_file=None)
    events = list(run_pipeline(IMG, "img0", level="rapida", settings=s, **_deps()))
    assert events[-1].fields.x_lon == -3.0 and events[-1].fields.y_lat == 40.0


def test_pipeline_saves_annotated_debug_images(tmp_path):
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=True, _env_file=None)
    rec = DebugRecorder(str(tmp_path), "runX", "img.jpg")
    list(run_pipeline(IMG, "img0", level="rapida", settings=s, recorder=rec,
                      run_id="runX", **_deps()))
    d = tmp_path / "runX" / "img.jpg"
    assert (d / "annot_easyocr.jpg").exists()
    assert (d / "annot_fields.jpg").exists()


def test_run_batch_emits_one_event_per_image():
    s = Settings(enable_easyocr=True, enable_paddleocr=True, enable_llm=True, _env_file=None)
    items = [("img_0", IMG), ("img_1", IMG)]
    evs = list(run_batch(items, level="avanzada", settings=s, **_deps()))
    stages = [(e.image_id, e.stage) for e in evs]
    assert stages == [("img_0", "final"), ("img_1", "final")]


def test_run_batch_isolates_image_error():
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=False, _env_file=None)

    def failing(_source):
        raise RuntimeError("ocr falló")

    items = [("img_0", IMG), ("img_1", IMG)]
    evs = list(run_batch(items, level="rapida", settings=s,
                         detectors={"easyocr": failing}))
    # cada imagen que falla emite un evento de error; ninguna tira la excepción
    assert all(isinstance(e, dict) and "error" in e for e in evs)
    assert {e["image_id"] for e in evs} == {"img_0", "img_1"}


def test_resolve_workers_caps_to_cpu_count():
    import os
    # per_worker_gb minúsculo → la RAM no es el límite, manda cpu_count
    n, warn = resolve_workers(1000, per_worker_gb=1e-6)
    assert n == (os.cpu_count() or 1)
    assert warn is not None and "1000" in warn


def test_resolve_workers_floor_is_one():
    n, warn = resolve_workers(0, per_worker_gb=1e-6)
    assert n == 1 and warn is None


def test_resolve_workers_caps_by_ram(monkeypatch):
    import folletos_ocr.pipeline as pl
    monkeypatch.setattr(pl, "_available_ram_gb", lambda: 4.0)  # 4 GB libres
    # 0.8*4 / 1.5 ≈ 2.13 → 2 workers como techo por RAM
    n, warn = resolve_workers(8, per_worker_gb=1.5)
    assert n == 2
    assert warn is not None and "RAM" in warn


def test_run_batch_parallel_emits_all_images():
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=False,
                 enable_geocoding=False, _env_file=None)
    items = [(f"img_{i}", IMG) for i in range(5)]
    evs = list(run_batch(items, level="rapida", settings=s, workers=3,
                         detectors={"easyocr": ConstDetector(OCR_TEXT)}))
    assert {e.image_id for e in evs} == {f"img_{i}" for i in range(5)}
    assert all(e.stage == "fast" for e in evs)


def test_run_batch_parallel_isolates_image_error():
    s = Settings(enable_easyocr=True, enable_paddleocr=False, enable_llm=False,
                 enable_geocoding=False, _env_file=None)
    items = [(f"img_{i}", IMG) for i in range(4)]
    evs = list(run_batch(items, level="rapida", settings=s, workers=3,
                         detectors={"easyocr": failing_detector}))
    assert all(isinstance(e, dict) and "error" in e for e in evs)
    assert {e["image_id"] for e in evs} == {f"img_{i}" for i in range(4)}
