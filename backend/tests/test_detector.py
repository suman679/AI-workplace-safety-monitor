"""Exercises detector.detect() with a fake YOLO object that returns torch-like tensors."""
import threading

import numpy as np

from app.ml import detector
from app.ml.class_map import classify_label, ppe_support
from app.ml.model_loader import ModelHandle
from app.models.enums import PpeItem

NAMES = {0: "Hardhat", 1: "Mask", 2: "NO-Hardhat", 3: "NO-Mask", 4: "NO-Safety Vest", 5: "Person", 6: "Safety Cone", 7: "Safety Vest", 8: "machinery", 9: "vehicle"}


class T:  # minimal stand-in for a torch tensor
    def __init__(self, a): self.a = np.array(a)
    def cpu(self): return self
    def numpy(self): return self.a


class FakeYolo:
    def __init__(self, rows):  # rows: (x1, y1, x2, y2, conf, cls)
        self.rows = rows
    def predict(self, frame, conf, imgsz, verbose):
        r = np.array(self.rows, dtype=float)
        boxes = type("B", (), {"xyxy": T(r[:, :4]), "conf": T(r[:, 4]), "cls": T(r[:, 5])})
        return [type("R", (), {"boxes": boxes})]


def handle(rows):
    kinds = {i: k for i, n in NAMES.items() if (k := classify_label(n))}
    return ModelHandle(FakeYolo(rows), NAMES, kinds, ppe_support(kinds), "custom", "x.pt", threading.Lock())


def test_detect_keeps_only_known_classes(monkeypatch):
    rows = [(10, 10, 100, 300, 0.9, 5), (20, 5, 80, 60, 0.8, 0), (0, 0, 5, 5, 0.9, 6), (0, 0, 9, 9, 0.7, 8), (30, 100, 90, 200, 0.6, 4)]
    monkeypatch.setattr(detector, "get_model", lambda: handle(rows))
    out = detector.detect(np.zeros((320, 320, 3), np.uint8))
    assert [(d.kind, d.item) for d in out] == [("person", None), ("has", PpeItem.HELMET), ("missing", PpeItem.VEST)]
    assert out[1].label == "Hardhat" and abs(out[1].conf - 0.8) < 1e-6


def test_detect_handles_an_empty_result(monkeypatch):
    h = handle([(0, 0, 1, 1, 0.9, 5)])
    h.yolo.predict = lambda *a, **k: [type("R", (), {"boxes": None})]
    monkeypatch.setattr(detector, "get_model", lambda: h)
    assert detector.detect(np.zeros((8, 8, 3), np.uint8)) == []
