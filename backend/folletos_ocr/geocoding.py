from __future__ import annotations
import logging
from functools import lru_cache

log = logging.getLogger(__name__)


def _user_agent(email: str) -> str:
    """User-Agent de aplicación para Nominatim.

    Nominatim rechaza (403) un email usado como User-Agent; exige un identificador
    de aplicación. Si hay email, se incluye como contacto (política de uso).
    """
    return f"folletos-ocr/1.0 ({email})" if email else "folletos-ocr"


def geocode_query(adreca: str, cp: str | None = None) -> str:
    """Compone la query de geocoding: añade el CP solo si aún no está en la dirección.

    Si la dirección ya lo trae (p. ej. la línea completa del overlay), volver a pegar el
    CP al final malforma la query y Nominatim no la encuentra.
    """
    return f"{adreca}, {cp}" if cp and cp not in adreca else adreca


@lru_cache
def _default_geocoder(nominatim_url: str, email: str, rate_limit_s: float):
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    geolocator = Nominatim(
        user_agent=_user_agent(email),
        domain=nominatim_url.replace("https://", "").replace("http://", "").rstrip("/"),
        scheme="https" if nominatim_url.startswith("https") else "http",
        timeout=10,
    )
    # swallow_exceptions=False: que los errores lleguen a geocode() y se registren,
    # en vez de quedar invisibles como un (None, None) silencioso.
    return RateLimiter(geolocator.geocode, min_delay_seconds=rate_limit_s,
                       swallow_exceptions=False)


def geocode(address: str, *, geocode_fn=None, nominatim_url="https://nominatim.openstreetmap.org",
            email="", rate_limit_s=1.0):
    if not address or not address.strip():
        return (None, None)
    fn = geocode_fn or _default_geocoder(nominatim_url, email, rate_limit_s)
    try:
        try:
            loc = fn(address, country_codes="es")
        except TypeError:
            loc = fn(address)
    except Exception as exc:  # noqa: BLE001 -- degradar a vacío pero dejando rastro
        log.warning("geocoding falló para %r: %s", address, exc)
        return (None, None)
    if loc is None:
        return (None, None)
    return (loc.latitude, loc.longitude)
