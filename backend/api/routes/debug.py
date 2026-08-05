from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from folletos_ocr.config import Settings, get_settings
from folletos_ocr.debug import bundle_zip

router = APIRouter(prefix="/debug")


@router.get("/{run_id}/bundle.zip")
def bundle(run_id: str, settings: Settings = Depends(get_settings)):
    run = Path(settings.debug_dir) / run_id
    if not run.exists():
        raise HTTPException(404, "run inexistente")
    path = bundle_zip(settings.debug_dir, run_id)
    return FileResponse(path, media_type="application/zip", filename=f"{run_id}.zip")


@router.get("/{run_id}/{image}/{artifact}")
def artifact(run_id: str, image: str, artifact: str,
             settings: Settings = Depends(get_settings)):
    base = Path(settings.debug_dir).resolve()
    path = (base / run_id / image / artifact).resolve()
    if not str(path).startswith(str(base)) or not path.exists():
        raise HTTPException(404, "artefacto inexistente")
    return FileResponse(path)
