"""Run the REAL detection pipeline (same code the API uses) on an image or video.

    python scripts/check_detection.py path/to/photo.jpg
    python scripts/check_detection.py path/to/clip.mp4 --require helmet,vest,mask

Run it from the backend folder (it reads .env there). Annotated output goes to ./uploads/test_out/.
"""
import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import cv2  # noqa: E402

from app.ml import postprocessing  # noqa: E402
from app.ml.model_loader import ModelUnavailable, get_model, model_status  # noqa: E402
from app.ml.rule_engine import RuleSpec, summarize  # noqa: E402
from app.models.enums import PpeItem, Severity  # noqa: E402
from app.services import detection_service as svc  # noqa: E402
from app.services.video_processing import process_video  # noqa: E402

VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}

p = argparse.ArgumentParser()
p.add_argument("source")
p.add_argument("--require", default="helmet,vest", help="comma list of: helmet,vest,gloves,safety_shoes,mask")
a = p.parse_args()

rules = [RuleSpec(PpeItem(n.strip().upper()), True, Severity.HIGH) for n in a.require.split(",") if n.strip()]
src = Path(a.source)
out_dir = BACKEND / "uploads" / "test_out"
out_dir.mkdir(parents=True, exist_ok=True)

try:
    handle = get_model()
except ModelUnavailable as exc:
    sys.exit(f"Model unavailable: {exc}")
print(f"Model source: {handle.source} ({handle.path})")
print("PPE judged:", ", ".join(sorted(i.value for i in handle.support)) or "none (demo mode: people only)")

if src.suffix.lower() in VIDEO_EXTS:
    dst = out_dir / f"{src.stem}_annotated.mp4"
    print(json.dumps(process_video(str(src), str(dst), rules, lambda pct: print(f"  {pct:.0f}%", end="\r")), indent=2))
    print("Saved", dst)
else:
    frame, persons, ppe = svc.analyze_bytes(src.read_bytes(), rules)
    h, w = frame.shape[:2]
    for pr in persons:
        print(json.dumps(postprocessing.person_to_dict(pr, w, h)))
    print("Summary:", summarize(persons))
    dst = out_dir / f"{src.stem}_annotated.jpg"
    cv2.imwrite(str(dst), postprocessing.annotate(frame, persons, ppe))
    print("Saved", dst)
