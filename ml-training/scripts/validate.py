"""Print precision / recall / mAP per class for a trained model."""
import argparse
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--weights", default=str(ROOT.parent / "backend" / "models" / "ppe.pt"))
p.add_argument("--data", default=str(ROOT / "dataset" / "data.yaml"))
a = p.parse_args()

m = YOLO(a.weights).val(data=a.data)
print(f"mAP50: {m.box.map50:.3f}  mAP50-95: {m.box.map:.3f}")
for i, name in m.names.items():
    print(f"{name:14s} AP50-95: {m.box.maps[i]:.3f}")
