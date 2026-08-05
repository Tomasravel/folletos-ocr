import json, os, time
import numpy as np
from folletos_ocr.debug import DebugRecorder, prune_old_runs

def test_recorder_persists_everything(tmp_path):
    rec = DebugRecorder(base_dir=str(tmp_path), run_id="run1", image_name="img.jpg")
    rec.save_input(np.zeros((10, 10, 3), dtype=np.uint8))
    rec.save_json("ocr_easyocr", [{"text": "a"}])
    rec.save_text("parse_llm_raw", '{"adreca": null}')
    rec.save_image("annot_fields", np.zeros((10, 10, 3), dtype=np.uint8))
    rec.save_trace({"status": "ok", "stages": []})
    d = tmp_path / "run1" / "img.jpg"
    assert (d / "input.jpg").exists()
    assert (d / "ocr_easyocr.json").exists()
    assert (d / "parse_llm_raw.txt").exists()
    assert (d / "annot_fields.jpg").exists()
    assert json.loads((d / "trace.json").read_text())["status"] == "ok"

def test_image_name_is_sanitized_against_traversal(tmp_path):
    rec = DebugRecorder(str(tmp_path), "run1", "../../evil.jpg")
    rec.save_input(np.zeros((10, 10, 3), dtype=np.uint8))
    assert rec.dir == tmp_path / "run1" / "evil.jpg"
    assert (tmp_path / "run1" / "evil.jpg" / "input.jpg").exists()

def test_prune_removes_old_runs(tmp_path):
    old = tmp_path / "old_run"; old.mkdir()
    os.utime(old, (time.time() - 9 * 86400, time.time() - 9 * 86400))
    new = tmp_path / "new_run"; new.mkdir()
    prune_old_runs(str(tmp_path), retention_days=7)
    assert not old.exists() and new.exists()
