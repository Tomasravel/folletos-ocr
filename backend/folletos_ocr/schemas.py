from __future__ import annotations
from pydantic import BaseModel


class Detection(BaseModel):
    box: tuple[float, float, float, float]
    text: str
    conf: float


class Fields(BaseModel):
    adreca: str | None = None
    cp: str | None = None
    zt: str | None = None
    fecha: str | None = None   # ISO string; None si no se detecta
    x_lon: float | None = None
    y_lat: float | None = None


class Stage(BaseModel):
    name: str
    ok: bool = True
    ms: int = 0
    detections: list[Detection] = []
    fields: Fields | None = None
    raw_response: str | None = None
    query: str | None = None
    result: dict | None = None
    artifacts: list[str] = []
    notes: str | None = None


class StageEvent(BaseModel):
    image_id: str
    run_id: str
    stage: str            # "fast" | "final"
    level: str
    engine: str | None = None
    parser: str | None = None
    fields: Fields
    timings_ms: dict[str, int] = {}
    warnings: list[str] = []
    boxes: list[Detection] = []


class Trace(BaseModel):
    image_id: str
    run_id: str
    level: str
    status: str = "ok"    # "ok" | "error"
    stages: list[Stage] = []
    error: dict | None = None
