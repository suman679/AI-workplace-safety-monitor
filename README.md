# SafeVision AI: Intelligent Workplace Safety & PPE Monitoring Platform

PPE detection SaaS (React + FastAPI + PostgreSQL + YOLO). Built in phases.

**Status: Phase 3 complete** (auth, sites/cameras/workers/PPE rules, AI detection on images, videos and live webcam).

## Quick start (Docker)
```bash
cp backend/.env.example backend/.env      # then set JWT_SECRET to a long random string
docker compose up --build
```
Frontend: http://localhost:5173 | API docs (Swagger): http://localhost:8000/docs

## Local setup (without Docker)
**Database**
```bash
docker run -d --name safevision-db -p 5432:5432 -e POSTGRES_USER=safevision \
  -e POSTGRES_PASSWORD=safevision_dev -e POSTGRES_DB=safevision postgres:16-alpine
```
**Backend** (Python 3.11+)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # set JWT_SECRET
alembic upgrade head
uvicorn app.main:app --reload
```
**Frontend** (Node 20+)
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Tests
```bash
cd backend && pytest          # 47 tests (SQLite in-memory; no Postgres, torch or GPU needed)
cd frontend && npm test
```

## Phase 1 API
| Method | Path | Notes |
|---|---|---|
| POST | /api/auth/register | Creates company + COMPANY_ADMIN user |
| POST | /api/auth/login | Returns access + refresh tokens |
| POST | /api/auth/refresh | Exchanges a refresh token |
| POST | /api/auth/logout | Audit-logged |
| GET | /api/auth/me | Current user |
| POST | /api/auth/forgot-password | Reset link is logged to the backend console in dev (email-ready) |
| POST | /api/auth/reset-password | Single-use reset token |

## Phase 2 API (all scoped to the user's company)
| Method | Path | Who can write |
|---|---|---|
| GET | /api/dashboard/stats | any logged-in user |
| GET/POST/PUT/DELETE | /api/sites | write: COMPANY_ADMIN, SAFETY_MANAGER; delete: COMPANY_ADMIN |
| GET/POST/PUT/DELETE | /api/cameras (filters: site_id, status_filter) | same |
| GET/POST/PUT/DELETE | /api/workers (filters: search, site_id) | same |
| GET/PUT | /api/ppe-rules?site_id= | write: COMPANY_ADMIN, SAFETY_MANAGER |

Creating a site also creates its 5 PPE rules from defaults for the site type (construction, factory, warehouse, other). Edit them on the PPE Rules page.
VIEWER is read-only. After pulling Phase 2, run `alembic upgrade head` again (migration 0002).

## Phase 3: AI detection
Pages: Live Monitoring (webcam, WebSocket), Video Analysis (background jobs, annotated H.264 output), Image Analysis.

```bash
cd backend
pip install -r requirements.txt        # includes OpenCV (needed by the app)
pip install -r requirements-ml.txt     # PyTorch + Ultralytics (large; needed for detection)
alembic upgrade head                   # migration 0003
```
Detection endpoints answer 503 with install instructions until `requirements-ml.txt` is installed; the rest of the app works without it.

**Model.** The app needs a PPE-trained YOLO model with a `person` class at `backend/models/ppe.pt`. Plain `yolov8n.pt` (COCO) cannot detect PPE, so never rename it. Install a public one, verified by checksum, from the backend folder:
```bash
python scripts/install_ppe_model.py          # downloads, validates classes, installs models/ppe.pt
python scripts/check_detection.py photo.jpg   # runs the real pipeline and saves an annotated image
```
See `backend/models/README.md` for the model's classes, limits and licence, and `ml-training/README.md` to train your own. Without it the app runs in demo mode with the generic `yolov8n.pt` (downloaded automatically on first use): people are detected but PPE is **not** checked, and the UI says so. Nothing is faked.

**Pipeline** (`backend/app/ml`): frame, resize, YOLO, class mapping, person/PPE association by box geometry (`ppe_classifier.py`), per-site rules (`rule_engine.py`), IoU tracking (`tracker.py`), annotation and JSON (`postprocessing.py`). The model is loaded once (`model_loader.py`).

| Method | Path | Notes |
|---|---|---|
| GET | /api/detection/status | model state, never loads the model |
| POST | /api/detection/image | multipart `file`, optional `site_id` |
| POST | /api/detection/video | multipart; returns 202 + job |
| GET | /api/detection/jobs, /jobs/{id}, /jobs/{id}/video | job list, status, processed video |
| WS | /ws/detect?token=&site_id=&camera_id= | binary JPEG frames in, JSON results out; sets the camera ONLINE/OFFLINE |

Settings (`.env`): `CONFIDENCE_THRESHOLD`, `MODEL_PATH`, `IMAGE_MAX_MB`, `VIDEO_MAX_MB`, `MAX_FRAME_SIDE`, `VIDEO_FRAME_STRIDE` (analyse every Nth video frame).

Errors always use `{"error": {"code", "message", "fields?"}}`.

## Roadmap
Phase 4 violations, incidents, alerts | Phase 5 analytics, reports, PDF/CSV |
Phase 6 security hardening, tests, docs | Phase 7 UI polish, demo mode, deployment
