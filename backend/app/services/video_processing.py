"""Frame-by-frame video analysis. Pure function: no database, easy to test."""
import logging
import math
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Callable

import cv2

from app.core.config import get_settings
from app.ml import postprocessing, preprocessing
from app.ml.rule_engine import ITEM_LABEL, RuleSpec
from app.ml.tracker import Tracker
from app.models.enums import PpeItem
from app.services.detection_service import analyze_frame

log = logging.getLogger("safevision.video")
MIN_TRACK_FRAMES = 2  # ignore flickers: a "worker" must be seen on at least this many analysed frames


def probe_video(path: str) -> tuple[int, float]:
    """Returns (frame_count, fps) or raises ValueError for files OpenCV cannot read."""
    cap = cv2.VideoCapture(path)
    try:
        ok, _ = cap.read()
        if not ok:
            raise ValueError("Invalid video format")
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return max(total, 1), cap.get(cv2.CAP_PROP_FPS) or 25.0
    finally:
        cap.release()


def _to_h264(src: Path, dst: Path) -> bool:
    """Browsers cannot play OpenCV's mp4v; re-encode to H.264 with the ffmpeg bundled in imageio-ffmpeg."""
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = shutil.which("ffmpeg")
    if not exe:
        return False
    cmd = [exe, "-y", "-loglevel", "error", "-i", str(src), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dst)]
    try:
        subprocess.run(cmd, check=True, timeout=1800)
        return dst.exists() and dst.stat().st_size > 0
    except Exception:
        log.exception("ffmpeg transcode failed; keeping mp4v output")
        return False


def process_video(src: str, dst: str, rules: list[RuleSpec], progress: Callable[[float], None] | None = None) -> dict:
    s = get_settings()
    total, fps = probe_video(src)
    stride = max(1, s.VIDEO_FRAME_STRIDE)
    cap = cv2.VideoCapture(src)
    tracker = Tracker(max_age=max(15, 15 * stride))
    raw_path = Path(dst).with_suffix(".raw.mp4")
    writer = None
    last: tuple[list, list] = ([], [])
    frames_read = analysed = 0
    track_frames: dict[int, int] = defaultdict(int)
    track_viol: dict[int, dict[PpeItem, int]] = defaultdict(lambda: defaultdict(int))
    scores: list[float] = []
    ppe_capable = True
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = preprocessing.limit_size(frame, s.MAX_FRAME_SIDE)
            if writer is None:
                h, w = frame.shape[:2]
                writer = cv2.VideoWriter(str(raw_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
            if frames_read % stride == 0:
                persons, ppe = analyze_frame(frame, rules, tracker)
                last = (persons, ppe)
                analysed += 1
                for p in persons:
                    track_frames[p.person_id] += 1
                    for item in p.violations:
                        track_viol[p.person_id][item] += 1
                    if p.compliance_score is not None:
                        scores.append(p.compliance_score)
                    if p.unchecked and not p.violations and p.compliance_score is None:
                        ppe_capable = False
            writer.write(postprocessing.annotate(frame, *last))
            frames_read += 1
            if progress and frames_read % 10 == 0:
                progress(min(99.0, 100.0 * frames_read / total))
    finally:
        cap.release()
        if writer is not None:
            writer.release()

    final = Path(dst)
    if raw_path.exists():
        if _to_h264(raw_path, final):
            raw_path.unlink(missing_ok=True)
        else:
            raw_path.replace(final)

    real = [t for t, n in track_frames.items() if n >= MIN_TRACK_FRAMES] or list(track_frames)
    per_item: dict[str, int] = {item.value: 0 for item in PpeItem}
    violators = 0
    for t in real:
        flagged = [i for i, n in track_viol[t].items() if n >= max(MIN_TRACK_FRAMES, math.ceil(0.4 * track_frames[t]))]
        violators += bool(flagged)
        for i in flagged:
            per_item[i.value] += 1
    workers = len(real)
    return {
        "frames_total": frames_read,
        "frames_analysed": analysed,
        "total_workers": workers,
        "workers_with_violations": violators,
        "total_violations": sum(per_item.values()),
        "violations_by_item": per_item,
        "violation_labels": {k: ITEM_LABEL[PpeItem(k)] for k in per_item},
        "compliance_rate": round(100 * (workers - violators) / workers, 1) if workers else None,
        "safety_score": round(sum(scores) / len(scores), 1) if scores else None,
        "ppe_checked": bool(scores),
    }
