import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install_ppe_model.py"
spec = importlib.util.spec_from_file_location("install_ppe_model", SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

COCO = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck"]
REAL = ["Hardhat", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest", "Person", "Safety Cone", "Safety Vest", "machinery", "vehicle"]


def run(monkeypatch, names):
    monkeypatch.setattr(installer, "load_names", lambda path: (names, "test"))
    return installer.report(Path("x.pt"))


def test_plain_yolov8n_is_rejected(monkeypatch, capsys):
    assert run(monkeypatch, COCO) is False
    assert "no PPE classes" in capsys.readouterr().out


def test_ppe_model_without_person_is_rejected(monkeypatch, capsys):
    assert run(monkeypatch, ["helmet", "vest"]) is False
    assert "'person' class" in capsys.readouterr().out


def test_real_ppe_model_is_accepted_and_unsupported_items_are_listed(monkeypatch, capsys):
    assert run(monkeypatch, REAL) is True
    out = capsys.readouterr().out
    assert "GLOVES, SAFETY_SHOES" in out and "HELMET (both)" in out
