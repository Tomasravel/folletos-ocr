from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from folletos_ocr.config import Settings, get_settings
from api.deps import require_auth
from api.routes import health, capabilities, process, export, commit, debug, edits


def warmup_models(settings: Settings) -> None:
    """Precarga los modelos habilitados para evitar el lazy-load en el primer request."""
    import numpy as np
    from folletos_ocr.engines import DETECTORS

    img = np.zeros((32, 32, 3), dtype=np.uint8)
    for name in settings.enabled_engines():
        try:
            DETECTORS[name](img)
        except Exception:  # noqa: BLE001 - warmup best-effort
            pass
    if settings.enable_llm:
        from folletos_ocr.parser_llm import llm_available
        try:
            llm_available(settings.llm_model, host=settings.ollama_host)
        except Exception:  # noqa: BLE001
            pass


def create_app(settings: Settings | None = None) -> FastAPI:
    eff_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if eff_settings.warmup:
            warmup_models(eff_settings)
        yield

    app = FastAPI(title="Folletos OCR API", lifespan=lifespan)
    if settings is not None:
        app.dependency_overrides[get_settings] = lambda: settings
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                       allow_headers=["*"])
    app.include_router(health.router)
    protected = [Depends(require_auth)]
    app.include_router(capabilities.router, dependencies=protected)
    app.include_router(process.router, dependencies=protected)
    app.include_router(export.router, dependencies=protected)
    app.include_router(commit.router, dependencies=protected)
    app.include_router(debug.router, dependencies=protected)
    app.include_router(edits.router, dependencies=protected)
    return app


app = create_app()
