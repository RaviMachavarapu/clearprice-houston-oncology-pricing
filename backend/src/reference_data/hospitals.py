from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.config import houston_hospitals_dir

_SEED_PATH = Path(__file__).parent / "houston_candidates_final.json"


@dataclass
class Hospital:
    id: str
    name: str
    mrf_url: str
    mrf_type: str
    ingestion_status: str = "not_ingested"
    last_ingested_at: str | None = None
    enrollment_340b: str = "unverified"
    enrollment_340b_checks: list = field(default_factory=list)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


def load_hospitals() -> list[Hospital]:
    """Load the 44 locked Houston-area hospitals from houston_candidates_final.json.

    Only the "working" list is in scope (per plan.md/spec.md FR-015) — the
    "broken" list was excluded during the approved design's own review and is
    not re-litigated here.
    """
    data = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    hospitals = []
    for entry in data["working"]:
        hospital_id = _slugify(entry["name"])
        hospital = Hospital(
            id=hospital_id,
            name=entry["name"],
            mrf_url=entry["url"],
            mrf_type=entry["type"],
        )
        ingested = _load_ingested_state(hospital_id)
        if ingested is not None:
            hospital.ingestion_status = ingested.get("ingestion_status", hospital.ingestion_status)
            hospital.last_ingested_at = ingested.get("last_ingested_at")
            hospital.enrollment_340b = ingested.get("enrollment_340b", "unverified")
            hospital.enrollment_340b_checks = ingested.get("enrollment_340b_checks", [])
        hospitals.append(hospital)
    return hospitals


def _load_ingested_state(hospital_id: str) -> dict | None:
    """Reads this hospital's own persisted ingestion output so every caller of
    load_hospitals() sees its true 340B/ingestion state, rather than each
    caller having to separately re-read houston_hospitals/<id>.json and patch
    it in by hand.
    """
    path = houston_hospitals_dir() / f"{hospital_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
