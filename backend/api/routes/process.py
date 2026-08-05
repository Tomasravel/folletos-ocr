import json
import time
import uuid
from functools import partial

import cv2
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse

from folletos_ocr.config import Settings, get_settings
from folletos_ocr.engines import DETECTORS
from folletos_ocr.parser_llm import parse_llm
from folletos_ocr.geocoding import geocode
from folletos_ocr.pipeline import run_batch
from folletos_ocr.debug import DebugRecorder, prune_old_runs

router = APIRouter()


def build_detectors(settings: Settings) -> dict:
    return {name: DETECTORS[name] for name in settings.enabled_engines()}


def build_llm_fn(settings: Settings):
    if not settings.enable_llm:
        return None
    # partial (no lambda) para que sea picklable en el pool de procesos
    return partial(parse_llm, host=settings.ollama_host)


def build_geocode_fn(settings: Settings):
    if not settings.enable_geocoding:
        return None
    return partial(geocode, nominatim_url=settings.nominatim_url,
                   email=settings.nominatim_email,
                   rate_limit_s=settings.nominatim_rate_limit_s)


def _read_image(raw: bytes) -> np.ndarray:
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="imagen inválida")
    return img


@router.post("/process")
async def process(
    images: list[UploadFile] = File(...),
    level: str = Query("rapida"),
    stream: bool = Query(True),
    strict: bool = Query(False),
    debug: bool = Query(False),
    workers: int = Query(1, ge=1),
    settings: Settings = Depends(get_settings),
):
    if strict:
        settings = settings.model_copy(update={"reject_on_missing": True})
    detectors = build_detectors(settings)
    llm_fn = build_llm_fn(settings)
    geocode_fn = build_geocode_fn(settings)
    payloads = [(f.filename, await f.read()) for f in images]

    if debug:
        prune_old_runs(settings.debug_dir, settings.debug_retention_days)

    items, recorders, run_ids = [], {}, {}
    for i, (name, raw) in enumerate(payloads):
        image_id = f"img_{i}"
        items.append((image_id, _read_image(raw)))
        if debug:
            run_id = f"{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}-{i:02d}"
            run_ids[image_id] = run_id
            recorders[image_id] = DebugRecorder(settings.debug_dir, run_id, name)

    def _batch():
        return run_batch(items, level=level, settings=settings, detectors=detectors,
                         llm_fn=llm_fn, geocode_fn=geocode_fn,
                         recorders=recorders or None, run_ids=run_ids or None,
                         workers=workers)

    if stream:
        def gen():
            try:
                for ev in _batch():
                    if isinstance(ev, dict):  # error de una imagen puntual
                        yield f"event: error\ndata: {json.dumps(ev)}\n\n"
                    else:
                        yield f"data: {ev.model_dump_json()}\n\n"
            except ValueError as exc:  # gating (nivel no disponible en modo estricto)
                yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
            yield "event: done\ndata: {}\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")

    try:
        last = {}
        for ev in _batch():
            if not isinstance(ev, dict):
                last[ev.image_id] = ev
    except ValueError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
    return [last[f"img_{i}"].model_dump() if f"img_{i}" in last else None
            for i in range(len(items))]
