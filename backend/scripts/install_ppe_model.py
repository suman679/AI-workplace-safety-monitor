"""Download (or take a local file), validate and install a PPE model at backend/models/ppe.pt.

    python scripts/install_ppe_model.py                     # default public model, checksum-verified
    python scripts/install_ppe_model.py --file my_best.pt   # your own trained weights
    python scripts/install_ppe_model.py --check-only        # just inspect models/ppe.pt

Run it from the backend folder. It never renames yolov8n.pt: a model is accepted only if it has a
'person' class and at least one PPE class the project understands (see app/ml/class_map.py).
"""
import argparse
import hashlib
import pickletools
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.ml.class_map import classify_label, ppe_support  # noqa: E402  (does not need .env)

DEFAULT_URL = "https://raw.githubusercontent.com/snehilsanyal/Construction-Site-Safety-PPE-Detection/main/models/best.pt"
DEFAULT_SHA256 = "4d07bbd92ca30d5c12dd67ccf52b2f54f533c9ccfef534284124682ef9f56129"
DEFAULT_TARGET = BACKEND / "models" / "ppe.pt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    print(f"Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "safevision-installer"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as out:
        shutil.copyfileobj(r, out)
    if dest.stat().st_size < 1_000_000:
        sys.exit(f"Downloaded file is only {dest.stat().st_size} bytes; that is not a model (Git LFS pointer or error page?).")


def names_preview(path: Path) -> list[str] | None:
    """Reads class names straight from the checkpoint without importing torch (best effort)."""
    try:
        with zipfile.ZipFile(path) as z:
            pkl = next(n for n in z.namelist() if n.endswith("data.pkl"))
            strings = [a for _, a, _ in pickletools.genops(z.read(pkl)) if isinstance(a, str)]
        start = strings.index("names") + 1
        out = []
        for s in strings[start:]:
            if s.startswith("torch") or s in ("nc", "args"):
                break
            out.append(s)
        return out or None
    except Exception:
        return None


def load_names(path: Path) -> tuple[list[str], str]:
    try:
        from ultralytics import YOLO
    except ImportError:
        names = names_preview(path)
        if names is None:
            sys.exit("Cannot read the model. Install the AI libraries first: pip install -r requirements-ml.txt")
        return names, "read from the file (ultralytics not installed, so the model was NOT loaded)"
    try:
        model = YOLO(str(path))
    except Exception as exc:
        sys.exit(f"ultralytics could not load {path}: {type(exc).__name__}: {exc}")
    return [model.names[i] for i in sorted(model.names)], "loaded with ultralytics"


def report(path: Path) -> bool:
    names, how = load_names(path)
    print(f"\nModel: {path}  ({how})\nClasses:")
    kinds = {}
    for i, name in enumerate(names):
        k = classify_label(name)
        if k:
            kinds[i] = k
        role = "ignored" if k is None else "person" if k[0] == "person" else f"{'worn' if k[0] == 'has' else 'MISSING'} {k[1].value}"
        print(f"  {i}: {name:16s} -> {role}")
    support = ppe_support(kinds)
    has_person = any(k[0] == "person" for k in kinds.values())
    print(f"\nPerson class: {'yes' if has_person else 'NO'}")
    print("PPE the app can judge:", ", ".join(f"{i.value} ({m})" for i, m in sorted(support.items(), key=lambda x: x[0].value)) or "none")
    missing = [i.value for i in __import__("app.models.enums", fromlist=["PpeItem"]).PpeItem if i not in support]
    if missing:
        print("Shown as 'not checked' (model has no class for them):", ", ".join(missing))
    if not has_person:
        print("REJECTED: the project matches PPE to people, so the model needs a 'person' class.")
    elif not support:
        print("REJECTED: no PPE classes the project understands.")
    return has_person and bool(support)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", help="use a local .pt file instead of downloading")
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--sha256", default=DEFAULT_SHA256, help="expected checksum of the download ('' to skip)")
    p.add_argument("--target", default=str(DEFAULT_TARGET))
    p.add_argument("--check-only", action="store_true")
    a = p.parse_args()
    target = Path(a.target)

    if a.check_only:
        if not target.is_file():
            sys.exit(f"{target} does not exist.")
        sys.exit(0 if report(target) else 1)

    with tempfile.TemporaryDirectory() as tmp:
        if a.file:
            src = Path(a.file)
            if not src.is_file():
                sys.exit(f"{src} not found.")
        else:
            src = Path(tmp) / "model.pt"
            download(a.url, src)
            digest = sha256(src)
            if a.sha256 and digest != a.sha256:
                sys.exit(f"Checksum mismatch.\n  expected {a.sha256}\n  got      {digest}\nThe file at that URL changed; inspect it before trusting it (use --sha256 '' to skip).")
            print("Checksum OK" if a.sha256 else f"sha256 {digest}")
        if not report(src):
            sys.exit(1)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and sha256(target) != sha256(src):
            shutil.copy(target, target.with_suffix(".pt.bak"))
            print(f"Existing model backed up to {target.with_suffix('.pt.bak')}")
        shutil.copy(src, target)
    print(f"\nInstalled -> {target}\nRestart the backend. The 'Demo mode' banner should disappear.")


if __name__ == "__main__":
    main()
