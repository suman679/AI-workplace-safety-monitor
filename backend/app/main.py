import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import auth, cameras, dashboard, detection, ppe_rules, realtime, sites, workers
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
settings = get_settings()

app = FastAPI(title=f"{settings.APP_NAME} API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_error(_: Request, exc: StarletteHTTPException):
    return JSONResponse({"error": {"code": exc.status_code, "message": exc.detail}}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    fields = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(
        {"error": {"code": 422, "message": "Validation failed", "fields": fields}}, status_code=422
    )


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception):
    logging.getLogger("safevision").exception("Unhandled error", exc_info=exc)
    return JSONResponse({"error": {"code": 500, "message": "Internal server error"}}, status_code=500)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok"}


for r in (auth, dashboard, sites, cameras, workers, ppe_rules, detection, realtime):
    app.include_router(r.router)
