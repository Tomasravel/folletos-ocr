import json
import time
from pathlib import Path

from fastapi import APIRouter, Body, Depends

from folletos_ocr.config import Settings, get_settings

router = APIRouter()


@router.post("/edits")
def save_edits(payload: dict = Body(...), settings: Settings = Depends(get_settings)):
    records = payload.get("records", [])
    directory = Path(settings.edits_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "edits.jsonl"
    with path.open("a", encoding="utf-8") as f:
        for rec in records:
            stamped = {"ts": rec.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S"), **rec}
            f.write(json.dumps(stamped, ensure_ascii=False) + "\n")
    return {"saved": len(records)}
