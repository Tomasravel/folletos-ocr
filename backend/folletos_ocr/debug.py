from __future__ import annotations
import json
import shutil
import time
from pathlib import Path

import cv2
import numpy as np


class DebugRecorder:
    def __init__(self, base_dir: str, run_id: str, image_name: str):
        safe_run = Path(run_id).name or "run"
        safe_name = Path(image_name).name or "img"
        self.dir = Path(base_dir) / safe_run / safe_name
        self.dir.mkdir(parents=True, exist_ok=True)

    def save_input(self, img: np.ndarray):
        cv2.imwrite(str(self.dir / "input.jpg"), img)

    def save_image(self, name: str, img: np.ndarray):
        cv2.imwrite(str(self.dir / f"{name}.jpg"), img)

    def save_json(self, name: str, obj):
        (self.dir / f"{name}.json").write_text(
            json.dumps(obj, ensure_ascii=False, indent=2, default=str))

    def save_text(self, name: str, text: str):
        (self.dir / f"{name}.txt").write_text(text)

    def save_trace(self, trace: dict):
        (self.dir / "trace.json").write_text(
            json.dumps(trace, ensure_ascii=False, indent=2, default=str))


def prune_old_runs(base_dir: str, retention_days: int) -> None:
    base = Path(base_dir)
    if not base.exists():
        return
    cutoff = time.time() - retention_days * 86400
    for run in base.iterdir():
        if run.is_dir() and run.stat().st_mtime < cutoff:
            shutil.rmtree(run, ignore_errors=True)


def bundle_zip(base_dir: str, run_id: str) -> str:
    run = Path(base_dir) / run_id
    archive = shutil.make_archive(str(run), "zip", root_dir=str(run))
    return archive
