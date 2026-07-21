from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.config import houston_hospitals_dir
from src.reference_data.hospitals import Hospital, load_hospitals


@dataclass
class RosterEntry:
    hospital_id: str
    name: str
    ingestion_status: str
    last_ingested_at: str | None
    matched_drug_codes: list[str]


def _hospitals_dir() -> Path:
    return houston_hospitals_dir()


def _load_hospital_file(hospital_id: str) -> dict | None:
    path = _hospitals_dir() / f"{hospital_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_roster(selected_codes: list[str]) -> tuple[list[RosterEntry], list[RosterEntry]]:
    """Given selected drug codes, return (available, unavailable) hospital rosters.

    A hospital is "available" if its ingested Charge Records contain at least
    one of the selected codes. A hospital whose ingestion failed (or that has
    never been ingested) is listed separately as unavailable rather than
    silently dropped (FR-002/FR-003).
    """
    code_set = set(selected_codes)
    available: list[RosterEntry] = []
    unavailable: list[RosterEntry] = []

    for hospital in load_hospitals():
        data = _load_hospital_file(hospital.id)
        if data is None:
            unavailable.append(
                RosterEntry(
                    hospital_id=hospital.id,
                    name=hospital.name,
                    ingestion_status="not_ingested",
                    last_ingested_at=None,
                    matched_drug_codes=[],
                )
            )
            continue

        status = data.get("ingestion_status", "not_ingested")
        last_ingested_at = data.get("last_ingested_at")

        if status != "success":
            unavailable.append(
                RosterEntry(
                    hospital_id=hospital.id,
                    name=hospital.name,
                    ingestion_status=status,
                    last_ingested_at=last_ingested_at,
                    matched_drug_codes=[],
                )
            )
            continue

        matched = sorted(
            {
                record["drug_code"]
                for record in data.get("charge_records", [])
                if record["drug_code"] in code_set
            }
        )
        if matched:
            available.append(
                RosterEntry(
                    hospital_id=hospital.id,
                    name=hospital.name,
                    ingestion_status=status,
                    last_ingested_at=last_ingested_at,
                    matched_drug_codes=matched,
                )
            )
        # else: successfully ingested but genuinely doesn't publish any
        # selected drug — normal absence per FR-002/FR-003, not shown at all.

    return available, unavailable
