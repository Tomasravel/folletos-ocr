from fastapi import APIRouter, Depends

from folletos_ocr.config import Settings, get_settings

router = APIRouter()


@router.get("/capabilities")
def capabilities(settings: Settings = Depends(get_settings)):
    return settings.capabilities().model_dump()
