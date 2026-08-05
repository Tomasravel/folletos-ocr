from folletos_ocr.parser_regex import parse_overlay, find_cp, find_coords, find_datetime

def test_find_cp_valid():
    assert find_cp("Barcelona 08033 ES") == "08033"

def test_find_cp_rejects_out_of_range():
    assert find_cp("codigo 99999 fin") is None

def test_find_coords_labeled():
    lat, lon = find_coords("Lat 40.3222591 Long -3.877213")
    assert round(lat, 4) == 40.3223 and round(lon, 4) == -3.8772

def test_find_datetime_iso():
    dt = find_datetime("2025-06-03 12:19:13")
    assert dt.year == 2025 and dt.hour == 12

def test_parse_overlay_zt_is_cp_plus_01():
    out = parse_overlay("Carrer de Finestrelles 8-4\nBarcelona 08033\n2025-06-03 12:19:13")
    assert out["cp"] == "08033"
    assert out["zt"] == "0803301"
    assert out["adreca"] is not None
