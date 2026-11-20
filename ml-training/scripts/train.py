"""Fine-tune YOLO on a PPE dataset and install the result where the backend looks for it."""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT.parent / "backend" / "models" / "ppe.pt"

p = argparse.ArgumentParser()
p.add_argument("--data", default=str(ROOT / "dataset" / "data.yaml"))
p.add_argument("--base", default="yolov8n.pt", help="starting weights (yolov8s.pt is more accurate, slower)")
p.add_argument("--epochs", type=int, default=50)
p.add_argument("--imgsz", type=int, default=640)
p.add_argument("--batch", type=int, default=16)
p.add_argument("--device", default=None, help="0 for first GPU, cpu for CPU")
p.add_argument("--target", default=str(DEFAULT_TARGET))
a = p.parse_args()

model = YOLO(a.base)
results = model.train(data=a.data, epochs=a.epochs, imgsz=a.imgsz, batch=a.batch, device=a.device, project=str(ROOT / "runs"), name="ppe")
best = Path(results.save_dir) / "weights" / "best.pt"
Path(a.target).parent.mkdir(parents=True, exist_ok=True)
shutil.copy(best, a.target)
print(f"Installed {best} -> {a.target}")
