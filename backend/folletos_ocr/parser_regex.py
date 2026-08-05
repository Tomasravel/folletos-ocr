from __future__ import annotations
import re
import unicodedata
from datetime import datetime

MESES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12,
}


def _strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


CP_RE = re.compile(r"(?<![\d.])(\d{5})(?![\d.])")
COORD_LABELED_RE = re.compile(
    r"lat[^\d\-]*(-?\d{1,2}\.\d{3,}).*?lon[g]?[^\d\-]*(-?\d{1,3}\.\d{3,})",
    re.IGNORECASE | re.DOTALL,
)
COORD_PAIR_RE = re.compile(r"(-?\d{1,2}\.\d{4,})\s*[,;]\s*(-?\d{1,3}\.\d{4,})")
DATE_ISO_RE = re.compile(r"(\d{4})[-/](\d{2})[-/](\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?")
DATE_NUM_RE = re.compile(
    r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})[,\s]+(\d{1,2}):(\d{2})(?::(\d{2}))?"
)
DATE_TEXT_RE = re.compile(
    r"(\d{1,2})\s+([a-zç]{3,})\.?\s+(\d{4})[,\s]+(\d{1,2})[.:h](\d{2})(?:[.:](\d{2}))?",
    re.IGNORECASE,
)

STREET_KW = [
    "calle", "carrer", "avinguda", "avenida", "av.", "c/", "plaza", "plaça",
    "passeig", "paseo", "camino", "carretera", "ronda", "travessera",
]


def find_cp(text):
    for m in CP_RE.finditer(text):
        cp = m.group(1)
        if "01000" <= cp <= "52999":
            return cp
    return None


def find_coords(text):
    m = COORD_LABELED_RE.search(text)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = COORD_PAIR_RE.search(text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


def find_datetime(text):
    m = DATE_ISO_RE.search(text)
    if m:
        y, mo, d, h, mi, s = m.groups()
        return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s or 0))
    m = DATE_NUM_RE.search(text)
    if m:
        d, mo, y, h, mi, s = m.groups()
        try:
            return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s or 0))
        except ValueError:
            pass
    m = DATE_TEXT_RE.search(text)
    if m:
        d, mes, y, h, mi, s = m.groups()
        mo = MESES.get(_strip_accents(mes).lower()[:3])
        if mo:
            try:
                return datetime(int(y), mo, int(d), int(h), int(mi), int(s or 0))
            except ValueError:
                pass
    return None


def find_address(text):
    lineas = [l.strip() for l in text.splitlines() if l.strip()]
    candidatas = [l for l in lineas if any(k in l.lower() for k in STREET_KW)]
    return max(candidatas, key=len) if candidatas else None


def parse_overlay(text):
    lat, lon = find_coords(text)
    cp = find_cp(text)
    dt = find_datetime(text)
    return {
        "adreca": find_address(text),
        "cp": cp,
        "zt": (cp + "01") if cp else None,
        "fecha": dt.isoformat() if dt else None,
        "y_lat": lat,
        "x_lon": lon,
    }
