from folletos_ocr.geocoding import geocode, _user_agent, geocode_query


class FakeLoc:
    def __init__(self, lat, lon): self.latitude, self.longitude = lat, lon


def test_geocode_returns_latlon():
    fake = lambda q, **k: FakeLoc(40.32, -3.87)
    assert geocode("Carrer X, Barcelona", geocode_fn=fake) == (40.32, -3.87)


def test_geocode_none_when_not_found():
    assert geocode("nada", geocode_fn=lambda q, **k: None) == (None, None)


def test_geocode_none_on_empty_address():
    assert geocode("", geocode_fn=lambda q, **k: FakeLoc(1, 2)) == (None, None)


def test_geocode_none_and_logs_on_error(caplog):
    def boom(q, **k):
        raise RuntimeError("403")
    import logging
    with caplog.at_level(logging.WARNING):
        assert geocode("Carrer X", geocode_fn=boom) == (None, None)
    assert any("geocod" in r.message.lower() for r in caplog.records)


def test_user_agent_is_app_not_email():
    # un email como User-Agent hace que Nominatim devuelva 403
    ua = _user_agent("contacto@ejemplo.com")
    assert ua != "contacto@ejemplo.com"
    assert ua.startswith("folletos-ocr")
    assert "contacto@ejemplo.com" in ua  # el email va como contacto


def test_user_agent_default_without_email():
    assert _user_agent("") == "folletos-ocr"


def test_geocode_query_appends_cp():
    assert geocode_query("Calle de las Higueras 5", "37700") == "Calle de las Higueras 5, 37700"


def test_geocode_query_without_cp():
    assert geocode_query("Calle de las Higueras 5", None) == "Calle de las Higueras 5"


def test_geocode_query_does_not_duplicate_cp():
    # si la dirección ya trae el CP, no volver a pegarlo (rompe la búsqueda en Nominatim)
    adreca = "C. San Mateo, 34, 11130 Chiclana de la Frontera, Cádiz, España"
    assert geocode_query(adreca, "11130") == adreca
