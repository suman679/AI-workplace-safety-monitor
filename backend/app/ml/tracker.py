"""Small IoU tracker: gives each person a stable id across frames (needed to count workers, not frames)."""


def iou(a, b) -> float:
    ix1, iy1, ix2, iy2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


class Tracker:
    def __init__(self, iou_threshold: float = 0.3, max_age: int = 15):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self._tracks: dict[int, dict] = {}
        self._next_id = 1

    def update(self, boxes: list[tuple]) -> list[int]:
        """Returns one track id per input box (same order)."""
        pairs = sorted(
            ((iou(box, t["box"]), i, tid) for i, box in enumerate(boxes) for tid, t in self._tracks.items()),
            reverse=True,
        )
        assigned: dict[int, int] = {}
        used: set[int] = set()
        for score, i, tid in pairs:
            if score < self.iou_threshold:
                break
            if i not in assigned and tid not in used:
                assigned[i] = tid
                used.add(tid)
        for tid, t in list(self._tracks.items()):
            if tid not in used:
                t["age"] += 1
                if t["age"] > self.max_age:
                    del self._tracks[tid]
        ids = []
        for i, box in enumerate(boxes):
            tid = assigned.get(i)
            if tid is None:
                tid, self._next_id = self._next_id, self._next_id + 1
            self._tracks[tid] = {"box": box, "age": 0}
            ids.append(tid)
        return ids
