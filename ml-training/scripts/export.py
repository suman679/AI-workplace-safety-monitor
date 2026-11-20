"""Export weights for faster CPU or edge inference (ONNX by default)."""
import argparse
from pathlib import Path

from ultralytics import YOLO

p = argparse.ArgumentParser()
p.add_argument("--weights", default=str(Path(__file__).resolve().parents[2] / "backend" / "models" / "ppe.pt"))
p.add_argument("--format", default="onnx", help="onnx, openvino, engine (TensorRT for Jetson), tflite ...")
a = p.parse_args()
print("Exported to", YOLO(a.weights).export(format=a.format))
