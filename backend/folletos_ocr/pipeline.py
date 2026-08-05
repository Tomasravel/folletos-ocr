from __future__ import annotations
import multiprocessing as mp
import os
import time
import traceback
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Callable, Iterator

import numpy as np

from .annotate import annotate_boxes, annotate_fields
from .config import Settings
from .engines import detections_to_text
from .geocoding import geocode_query
from .parser_regex import parse_overlay
from .schemas import Detection, Fields, StageEvent

# level -> lista ordenada de etapas (engine, parser, stage_label)
# Cada nivel usa un único paso (motor + parser), sin fase rápida previa.
LEVEL_STAGES = {
    "rapida":   [("easyocr", "regex", "fast")],
    "media":    [("easyocr", "llm", "final")],
    "avanzada": [("paddleocr", "llm", "final")],
}


def _available_ram_gb() -> float:
    """RAM disponible en GB. Sin psutil devuelve inf (no capa por memoria)."""
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except Exception:
        return float("inf")


def resolve_workers(requested: int, *, per_worker_gb: float = 1.5,
                    ram_fraction: float = 0.8) -> tuple[int, str | None]:
    """Capa los workers solicitados a un máximo seguro para paralelismo por procesos.

    Cada proceso carga su propia copia de los modelos OCR, así que la RAM crece con
    los workers. El techo es ``min(núcleos, RAM_disponible*fraction / RAM_por_worker)``.
    Devuelve (workers_efectivos, warning|None).
    """
    cores = os.cpu_count() or 1
    n = max(1, int(requested or 1))
    cap, reason = cores, f"núcleos={cores}"
    avail = _available_ram_gb()
    if avail != float("inf") and per_worker_gb > 0:
        ram_cap = max(1, int((avail * ram_fraction) // per_worker_gb))
        if ram_cap < cap:
            cap, reason = ram_cap, f"RAM disponible ~{avail:.1f}GB (~{per_worker_gb}GB/worker)"
    if n > cap:
        return cap, f"workers pedidos={requested}, limitado a {cap} ({reason})"
    return n, None




def _resolve_stages(level: str, settings: Settings) -> tuple[list, list[str]]:
    """Devuelve (stages_ejecutables, warnings) según capacidades habilitadas."""
    engines = set(settings.enabled_engines())
    parsers = set(settings.enabled_parsers())
    planned = LEVEL_STAGES.get(level)
    if planned is None:
        raise ValueError(f"nivel desconocido: {level}")
    resolved, warnings = [], []
    for engine, parser, label in planned:
        eng, par = engine, parser
        if engine not in engines:
            alt = next(iter(engines), None)
            if alt is None:
                raise ValueError("no hay motores OCR habilitados")
            warnings.append(f"{engine} no habilitado, se usó {alt}")
            eng = alt
        if parser == "llm" and "llm" not in parsers:
            warnings.append("llm no habilitado, se usó regex")
            par = "regex"
        resolved.append((eng, par, label))
    # dedup de stages idénticas (p.ej. avanzada sin paddle == fast repetida)
    seen, out = set(), []
    for st in resolved:
        key = (st[0], st[1])
        if key in seen:
            continue
        seen.add(key)
        out.append(st)
    if warnings and settings.reject_on_missing:
        raise ValueError("; ".join(warnings))
    return out, warnings


def _compute_stage(img, image_id, run_id, engine, parser, label, level,
                   settings, detectors, llm_fn, geocode_fn, warnings, recorder):
    """Corre una etapa (OCR + parser [+ geocoding]) sobre una imagen.

    Devuelve (StageEvent, trace_entries) y, si hay recorder, persiste artefactos.
    """
    t0 = time.time()
    dets = detectors[engine](img)
    text = detections_to_text(dets, min_conf=0.0)
    ocr_ms = int((time.time() - t0) * 1000)

    t1 = time.time()
    if parser == "llm" and llm_fn is not None:
        raw = llm_fn(text, settings.llm_model)
    else:
        raw = parse_overlay(text)
    parse_ms = int((time.time() - t1) * 1000)

    timings = {"ocr": ocr_ms, "parse": parse_ms}
    if (raw.get("x_lon") is None or raw.get("y_lat") is None) \
            and settings.enable_geocoding and geocode_fn and raw.get("adreca"):
        t2 = time.time()
        lat, lon = geocode_fn(geocode_query(raw["adreca"], raw.get("cp")))
        raw["y_lat"], raw["x_lon"] = lat, lon
        timings["geocode"] = int((time.time() - t2) * 1000)

    fields = Fields(**{k: raw.get(k) for k in
                       ["adreca", "cp", "zt", "fecha", "x_lon", "y_lat"]})
    boxes = [Detection(**d) for d in dets]

    trace_entries = []
    if recorder is not None:
        recorder.save_json(f"ocr_{engine}", dets)
        recorder.save_json(f"parse_{parser}", raw)
        recorder.save_image(f"annot_{engine}", annotate_boxes(img, dets))
        recorder.save_image("annot_fields", annotate_fields(img, raw))
        trace_entries.append({"name": f"ocr:{engine}", "ok": True, "ms": ocr_ms})
        trace_entries.append({"name": f"parse:{parser}", "ok": True,
                              "ms": parse_ms, "fields": raw})

    event = StageEvent(image_id=image_id, run_id=run_id, stage=label, level=level,
                       engine=engine, parser=parser, fields=fields,
                       timings_ms=timings, warnings=warnings, boxes=boxes)
    return event, trace_entries


def _error_trace(image_id, run_id, level, engine, parser, trace_stages, exc):
    return {"image_id": image_id, "run_id": run_id, "level": level, "status": "error",
            "stages": trace_stages,
            "error": {"stage": f"{engine}:{parser}", "type": type(exc).__name__,
                      "message": str(exc), "traceback": traceback.format_exc()}}


def run_pipeline(
    img: np.ndarray,
    image_id: str,
    *,
    level: str,
    settings: Settings,
    detectors: dict[str, Callable],
    llm_fn: Callable[[str, str], dict] | None = None,
    geocode_fn: Callable[[str], tuple] | None = None,
    recorder=None,
    run_id: str | None = None,
) -> Iterator[StageEvent]:
    run_id = run_id or f"{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}"
    stages, warnings = _resolve_stages(level, settings)
    if recorder is not None:
        recorder.save_input(img)
    trace_stages = []

    for engine, parser, label in stages:
        try:
            event, entries = _compute_stage(img, image_id, run_id, engine, parser, label,
                                            level, settings, detectors, llm_fn, geocode_fn,
                                            warnings, recorder)
            trace_stages.extend(entries)
            yield event
        except Exception as exc:  # noqa: BLE001
            if recorder is not None:
                recorder.save_trace(_error_trace(image_id, run_id, level, engine, parser,
                                                 trace_stages, exc))
            raise

    if recorder is not None:
        recorder.save_trace({"image_id": image_id, "run_id": run_id, "level": level,
                             "status": "ok", "stages": trace_stages, "error": None})


def _stage_task(args):
    """Ejecuta una etapa sobre una imagen. Todos los args son picklables para poder
    correr en un proceso worker. Encapsula el error para aislarlo."""
    (img, image_id, run_id, engine, parser, label, level, settings,
     detectors, llm_fn, geocode_fn, recorder, warnings, prior_entries) = args
    try:
        event, entries = _compute_stage(img, image_id, run_id, engine, parser, label,
                                        level, settings, detectors, llm_fn, geocode_fn,
                                        warnings, recorder)
        return "ok", image_id, event, entries
    except Exception as exc:  # noqa: BLE001
        if recorder is not None:
            recorder.save_trace(_error_trace(image_id, run_id, level, engine, parser,
                                             list(prior_entries), exc))
        return "err", image_id, exc, None


def run_batch(
    items: list[tuple[str, np.ndarray]],
    *,
    level: str,
    settings: Settings,
    detectors: dict[str, Callable],
    llm_fn: Callable[[str, str], dict] | None = None,
    geocode_fn: Callable[[str], tuple] | None = None,
    recorders: dict | None = None,
    run_ids: dict | None = None,
    workers: int = 1,
):
    """Procesa un lote **por fases**: primero la etapa más rápida para TODAS las
    imágenes, luego la siguiente, etc. Así se obtienen rápido los datos de todo el lote
    mientras el paso lento (p.ej. PaddleOCR + LLM) se procesa después.

    Con ``workers > 1`` las imágenes de una misma etapa se procesan en paralelo con un
    pool de **procesos** (``ProcessPoolExecutor``): cada worker es un intérprete aislado
    con su propia copia de los modelos OCR (sin GIL, sin deadlocks de torch entre hilos),
    a costa de multiplicar la RAM. Por eso ``workers`` se capa con ``resolve_workers``
    según la RAM disponible. Las fases se siguen respetando (toda la etapa rápida antes
    de la final); el orden dentro de una etapa deja de estar garantizado.

    Para el pool, ``detectors``, ``llm_fn`` y ``geocode_fn`` deben ser **picklables**
    (funciones de módulo o ``functools.partial``, no lambdas/closures).

    Yields `StageEvent` en cada etapa exitosa. Si una imagen falla en una etapa, emite
    `{"image_id": ..., "error": ...}` y deja de procesar esa imagen (las demás siguen).
    """
    stages, warnings = _resolve_stages(level, settings)
    eff_workers, wmsg = resolve_workers(workers, per_worker_gb=settings.worker_ram_gb)
    if wmsg:
        warnings = warnings + [wmsg]
    recorders = recorders or {}
    run_ids = run_ids or {}
    traces: dict[str, list] = {img_id: [] for img_id, _ in items}
    dead: set[str] = set()

    for img_id, img in items:
        rec = recorders.get(img_id)
        if rec is not None:
            rec.save_input(img)

    def _args(engine, parser, label, img_id, img):
        return (img, img_id, run_ids.get(img_id, ""), engine, parser, label, level,
                settings, detectors, llm_fn, geocode_fn, recorders.get(img_id),
                warnings, list(traces[img_id]))

    def _handle(kind, img_id, payload, entries):
        if kind == "ok":
            traces[img_id].extend(entries)
            return payload
        dead.add(img_id)
        return {"image_id": img_id, "error": str(payload)}

    if eff_workers > 1:
        with ProcessPoolExecutor(max_workers=eff_workers,
                                 mp_context=mp.get_context("spawn")) as ex:
            for engine, parser, label in stages:
                alive = [(i, im) for i, im in items if i not in dead]
                if not alive:
                    continue
                futs = [ex.submit(_stage_task, _args(engine, parser, label, i, im))
                        for i, im in alive]
                for fut in as_completed(futs):
                    yield _handle(*fut.result())
    else:
        for engine, parser, label in stages:
            for img_id, img in items:
                if img_id in dead:
                    continue
                yield _handle(*_stage_task(_args(engine, parser, label, img_id, img)))

    for img_id, _ in items:
        if img_id in dead:
            continue
        rec = recorders.get(img_id)
        if rec is not None:
            rec.save_trace({"image_id": img_id, "run_id": run_ids.get(img_id, ""),
                            "level": level, "status": "ok",
                            "stages": traces[img_id], "error": None})
