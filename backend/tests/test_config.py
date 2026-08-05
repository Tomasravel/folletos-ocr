from folletos_ocr.config import Settings, Capabilities


def test_defaults_enable_easyocr_and_llm():
    s = Settings(_env_file=None)
    assert s.enable_easyocr is True
    assert s.enable_paddleocr is False
    assert s.enable_llm is True
    assert s.reject_on_missing is False


def test_capabilities_levels_available():
    caps = Settings(enable_easyocr=True, enable_paddleocr=False,
                    enable_llm=True, _env_file=None).capabilities()
    assert isinstance(caps, Capabilities)
    assert "rapida" in caps.levels
    assert "media" in caps.levels
    assert "avanzada" not in caps.levels  # sin paddle no hay avanzada plena


def test_capabilities_full():
    caps = Settings(enable_easyocr=True, enable_paddleocr=True,
                    enable_llm=True, _env_file=None).capabilities()
    assert set(caps.levels) == {"rapida", "media", "avanzada"}
