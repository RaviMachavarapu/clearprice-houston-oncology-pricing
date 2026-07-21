from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.config import houston_hospitals_dir
from src.ingestion.ingest_hospital import ingest_hospital
from src.reference_data.hospitals import load_hospitals

router = APIRouter()


def _hospitals_dir() -> Path:
    return houston_hospitals_dir()


def _load_hospital_file(hospital_id: str) -> dict | None:
    path = _hospitals_dir() / f"{hospital_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _hospital_summary(hospital) -> dict:
    """FR-003: every hospital is always listed, with its ingestion_status and
    last_ingested_at, plus (US3/T038) the raw 340B double-check detail so the
    verification state is visible rather than assumed.
    """
    data = _load_hospital_file(hospital.id)
    if data is None:
        return {
            "id": hospital.id,
            "name": hospital.name,
            "ingestion_status": "not_ingested",
            "last_ingested_at": None,
            "enrollment_340b": "unverified",
            "enrollment_340b_checks": [],
        }
    return {
        "id": hospital.id,
        "name": hospital.name,
        "ingestion_status": data.get("ingestion_status", "not_ingested"),
        "last_ingested_at": data.get("last_ingested_at"),
        "enrollment_340b": data.get("enrollment_340b", "unverified"),
        "enrollment_340b_checks": data.get("enrollment_340b_checks", []),
    }


@router.get("/api/hospitals")
def get_hospitals() -> dict:
    return {"hospitals": [_hospital_summary(h) for h in load_hospitals()]}


@router.post("/api/hospitals/{hospital_id}/refresh")
def refresh_hospital(hospital_id: str) -> dict:
    """Manual re-ingestion trigger for a single hospital (no scheduler, per
    spec Clarifications — refresh is always user-initiated).
    """
    hospital = next((h for h in load_hospitals() if h.id == hospital_id), None)
    if hospital is None:
        raise HTTPException(status_code=404, detail=f"Unknown hospital_id: {hospital_id}")
    result = ingest_hospital(hospital)
    return {
        "id": hospital.id,
        "name": hospital.name,
        "ingestion_status": result["ingestion_status"],
        "last_ingested_at": result.get("last_ingested_at"),
    }
