from __future__ import annotations
from functools import lru_cache
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Capabilities(BaseModel):
    engines: list[str]
    parsers: list[str]
    levels: list[str]
    llm_model: str | None
    geocoding: bool
    auth_required: bool


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    enable_easyocr: bool = True
    enable_paddleocr: bool = False
    enable_llm: bool = True
    enable_geocoding: bool = True
    reject_on_missing: bool = False

    warmup: bool = False  # precargar modelos al arrancar (evita lazy-load en el 1er request)

    worker_ram_gb: float = 1.5  # RAM estimada por worker de proceso (safeguard)

    ollama_host: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:3b"

    nominatim_url: str = "https://nominatim.openstreetmap.org"
    nominatim_email: str = ""
    nominatim_rate_limit_s: float = 1.0

    api_token: str = ""

    debug_dir: str = "./data/debug"
    debug_retention_days: int = 7
    edits_dir: str = "./data/edits"

    def enabled_engines(self) -> list[str]:
        out = []
        if self.enable_easyocr:
            out.append("easyocr")
        if self.enable_paddleocr:
            out.append("paddleocr")
        return out

    def enabled_parsers(self) -> list[str]:
        out = ["regex"]
        if self.enable_llm:
            out.append("llm")
        return out

    def available_levels(self) -> list[str]:
        engines = self.enabled_engines()
        parsers = self.enabled_parsers()
        levels = []
        if "easyocr" in engines:
            levels.append("rapida")
            if "llm" in parsers:
                levels.append("media")
        if "paddleocr" in engines and "llm" in parsers:
            levels.append("avanzada")
        return levels

    def capabilities(self) -> Capabilities:
        return Capabilities(
            engines=self.enabled_engines(),
            parsers=self.enabled_parsers(),
            levels=self.available_levels(),
            llm_model=self.llm_model if self.enable_llm else None,
            geocoding=self.enable_geocoding,
            auth_required=bool(self.api_token),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
