from fastapi import Header, HTTPException, Depends
from folletos_ocr.config import Settings, get_settings


def require_auth(authorization: str | None = Header(default=None),
                 settings: Settings = Depends(get_settings)):
    if not settings.api_token:
        return
    if authorization != f"Bearer {settings.api_token}":
        raise HTTPException(status_code=401, detail="no autorizado")
