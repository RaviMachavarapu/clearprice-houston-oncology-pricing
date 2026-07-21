from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.breakdowns import router as breakdowns_router
from src.api.drugs import router as drugs_router
from src.api.hospitals import router as hospitals_router
from src.config import houston_hospitals_dir
from src.reference_data.hospitals import load_hospitals

app = FastAPI(title="ClearPrice Houston Oncology Pricing Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drugs_router)
app.include_router(hospitals_router)
app.include_router(breakdowns_router)


@app.get("/api/status")
def status() -> dict:
    """Surfaces ingestion completeness so it's obvious, without inspecting
    files by hand, whether `python -m src.ingestion.run_all` has actually
    been run for every locked hospital on this machine — since
    `houston_hospitals/` is not checked into git, this is the one place two
    different machines can confirm they're looking at the same dataset.
    """
    hospitals = load_hospitals()
    out_dir = houston_hospitals_dir()
    ingested_ids = {p.stem for p in out_dir.glob("*.json")} if out_dir.is_dir() else set()

    succeeded = 0
    failed = 0
    missing: list[str] = []
    for hospital in hospitals:
        path = out_dir / f"{hospital.id}.json"
        if not path.is_file():
            missing.append(hospital.id)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            missing.append(hospital.id)
            continue
        if data.get("ingestion_status") == "success":
            succeeded += 1
        else:
            failed += 1

    return {
        "status": "ok",
        "service": "clearprice-houston-oncology",
        "ingestion": {
            "total_hospitals": len(hospitals),
            "ingested_success": succeeded,
            "ingested_failed": failed,
            "not_yet_ingested": missing,
            "complete": not missing,
        },
    }


@app.exception_handler(Exception)
def unhandled_exception_handler(request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": str(exc)})


_frontend_dir = Path(__file__).resolve().parents[3] / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
