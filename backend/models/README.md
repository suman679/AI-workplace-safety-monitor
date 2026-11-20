# Models

`ppe.pt` is the PPE detector loaded by the backend (`MODEL_PATH` in `.env`). It is not committed (see .gitignore).
Install one with:

    python scripts/install_ppe_model.py

Default model: `models/best.pt` from github.com/snehilsanyal/Construction-Site-Safety-PPE-Detection
(YOLOv8n fine-tuned for 100 epochs on the Roboflow "Construction Site Safety" dataset, 2,801 images).
- Classes: Hardhat, Mask, NO-Hardhat, NO-Mask, NO-Safety Vest, Person, Safety Cone, Safety Vest, machinery, vehicle
- SHA-256: 4d07bbd92ca30d5c12dd67ccf52b2f54f533c9ccfef534284124682ef9f56129
- It cannot judge gloves or safety shoes (the UI shows them as "not checked").
- Licensing: the dataset is published on Roboflow Universe (CC BY 4.0 according to third-party model cards; verify on the dataset page) and the repository states no licence of its own. Credit both in your report and check the terms before commercial use. Ultralytics itself is AGPL-3.0.
- Accuracy on your own site footage is unknown until you test it; judge it with `ml-training/scripts/validate.py` or your own videos.
