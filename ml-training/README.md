# Training a PPE model

SafeVision works with any YOLO model whose class names it recognises. Without a model it runs in **demo mode** (people only, PPE not checked, and the UI says so).

## Classes
| Class name (any of these spellings works) | Meaning |
|---|---|
| `person` / `worker` | required, PPE is matched to people |
| `helmet`, `hardhat`, `hard hat` | helmet worn |
| `vest`, `safety vest` | vest worn |
| `gloves` | gloves worn |
| `safety_shoes`, `boots` | shoes worn |
| `mask`, `face mask` | mask worn |
| `no-helmet`, `NO-Hardhat`, `no_vest`, `NO-Safety Vest`, `no_mask` ... | explicit violation classes (optional) |

Models trained with "positive" classes only (helmet, vest): a person with no helmet detected is a violation.
Models with "no-x" classes only: a violation is flagged when a `no-x` box is found.
Models with both (e.g. `Hardhat` and `NO-Hardhat`): the explicit class decides; if neither is detected the item is "not verified" (warning), never a guessed violation.
Items the model has no class for are shown as "not checked", never guessed.

## Steps
1. Get a labelled dataset in YOLO format. Good starting points: Roboflow Universe (search "construction site safety PPE"; export as "YOLOv8") or Kaggle PPE datasets. Check each dataset's licence.
2. Put it in `dataset/images/{train,val}` and `dataset/labels/{train,val}`, and make `dataset/data.yaml` match the dataset's class list (the exported `data.yaml` can replace ours).
3. Install and train (a GPU helps a lot; Google Colab's free GPU works well):
   ```bash
   pip install -r ../backend/requirements-ml.txt
   python scripts/train.py --epochs 50 --device 0      # use --device cpu without a GPU (slow)
   ```
   This copies the best weights to `backend/models/ppe.pt`.
4. Check quality: `python scripts/validate.py`
5. In `backend/.env`: `MODEL_PATH=./models/ppe.pt` (default), then restart the backend.
6. Optional: `python scripts/export.py --format onnx`.

Judge the model by `validate.py` per-class results, not by how the demo looks.
