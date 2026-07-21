from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Query

from src.calc.breakdown import build_breakdown
from src.calc.roster import build_roster
from src.config import houston_hospitals_dir
from src.ingestion.charge_record import ChargeRecord, PayerRate
from src.reference_data.drugs import load_drugs
from src.reference_data.hospitals import load_hospitals

router = APIRouter()


def _hospitals_dir() -> Path:
    return houston_hospitals_dir()


def _load_hospital_file(hospital_id: str) -> dict | None:
    path = _hospitals_dir() / f"{hospital_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _record_from_dict(d: dict) -> ChargeRecord:
    return ChargeRecord(
        hospital_id=d["hospital_id"],
        drug_code=d["drug_code"],
        gross_charge_min=d.get("gross_charge_min"),
        gross_charge_max=d.get("gross_charge_max"),
        source_file=d["source_file"],
        retrieved_at=d["retrieved_at"],
        payer_rates=[PayerRate(**pr) for pr in d.get("payer_rates", [])],
    )


def _merge_raw_records(raw_records: list[dict]) -> dict:
    """A hospital's chargemaster can list the same HCPCS code across several
    line items (different NDCs/package sizes/revenue codes). Those all price
    the same drug at this hospital, so they collapse into one breakdown
    instead of one duplicate card per line item.
    """
    gross_mins = [r["gross_charge_min"] for r in raw_records if r.get("gross_charge_min") is not None]
    gross_maxs = [r["gross_charge_max"] for r in raw_records if r.get("gross_charge_max") is not None]

    seen_rates: set[tuple] = set()
    payer_rates: list[dict] = []
    for r in raw_records:
        for pr in r.get("payer_rates", []):
            key = (pr["payer_name"], pr["plan_name"], pr["billing_setting"], pr["rate"])
            if key in seen_rates:
                continue
            seen_rates.add(key)
            payer_rates.append(pr)

    first = raw_records[0]
    return {
        "hospital_id": first["hospital_id"],
        "drug_code": first["drug_code"],
        "gross_charge_min": min(gross_mins) if gross_mins else None,
        "gross_charge_max": max(gross_maxs) if gross_maxs else None,
        "source_file": first["source_file"],
        "retrieved_at": first["retrieved_at"],
        "payer_rates": payer_rates,
    }


@router.get("/api/breakdowns")
def get_breakdowns(drugs: str = Query(..., description="Comma-separated drug codes")) -> dict:
    """FR-001 through FR-014: given selected drug codes, return the hospital
    roster plus a full Section-4-style Pricing Breakdown per hospital/drug
    pair, and separately list hospitals unavailable for these drugs (failed
    ingestion, not yet ingested, or simply not publishing any selected code).
    """
    codes = [c.strip() for c in drugs.split(",") if c.strip()]
    available, unavailable = build_roster(codes)

    drugs_by_code = {d.code: d for d in load_drugs()}
    hospitals_by_id = {h.id: h for h in load_hospitals()}

    breakdowns = []
    for entry in available:
        data = _load_hospital_file(entry.hospital_id)
        hospital = hospitals_by_id[entry.hospital_id]

        raw_by_code: dict[str, list[dict]] = {}
        for raw_record in data.get("charge_records", []):
            if raw_record["drug_code"] not in entry.matched_drug_codes:
                continue
            raw_by_code.setdefault(raw_record["drug_code"], []).append(raw_record)

        for drug_code, raw_records in raw_by_code.items():
            drug = drugs_by_code.get(drug_code)
            if drug is None:
                continue
            record = _record_from_dict(_merge_raw_records(raw_records))
            breakdowns.append(build_breakdown(record, drug, hospital))

    return {
        "breakdowns": breakdowns,
        "unavailable_hospitals": [
            {
                "hospital_id": e.hospital_id,
                "name": e.name,
                "ingestion_status": e.ingestion_status,
                "last_ingested_at": e.last_ingested_at,
            }
            for e in unavailable
        ],
    }
