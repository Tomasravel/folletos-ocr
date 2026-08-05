from __future__ import annotations
import json

SYS = (
    "Sos un extractor de datos. Te paso texto crudo de OCR de una foto con overlay de "
    "cámara GPS (dirección, fecha, código postal, a veces lat/long). "
    "Devolve SOLO un JSON con estas claves: adreca (string o null), cp (5 dígitos o null), "
    "fecha (ISO 8601 o null), x_lon (float o null), y_lat (float o null). "
    "adreca debe ser la dirección postal COMPLETA tal como aparece, en una sola cadena: "
    "vía, número, código postal y localidad (p. ej. 'C. San Mateo, 34, 11130 Chiclana de "
    "la Frontera, Cádiz'). Nunca la recortes a solo el nombre de la vía ni a solo la localidad. "
    "No inventes datos: si no está en el texto, poné null."
)


def _get_client(host: str | None):
    import ollama
    return ollama.Client(host=host) if host else ollama


def parse_llm(text: str, model: str, client=None, host: str | None = None) -> dict:
    client = client or _get_client(host)
    try:
        r = client.chat(
            model=model, format="json",
            messages=[{"role": "system", "content": SYS},
                      {"role": "user", "content": text}],
            options={"temperature": 0},
        )
        d = json.loads(r["message"]["content"])
    except Exception:
        d = {}
    cp = d.get("cp") or None
    if cp is not None:
        cp = str(cp)
    return {
        "adreca": d.get("adreca") or None,
        "cp": cp,
        "zt": (cp + "01") if cp else None,
        "fecha": d.get("fecha") or None,
        "x_lon": d.get("x_lon"),
        "y_lat": d.get("y_lat"),
    }


def llm_available(model: str, client=None, host: str | None = None) -> bool:
    client = client or _get_client(host)
    try:
        client.chat(model=model, messages=[{"role": "user", "content": "ping"}],
                    options={"num_predict": 1})
        return True
    except Exception:
        return False
