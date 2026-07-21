from __future__ import annotations

import json

from src.calc.roster import build_roster
from src.reference_data.hospitals import load_hospitals

_REAL_HOSPITAL_IDS = [h.id for h in load_hospitals()]


def _write_hospital_file(tmp_path, hospital_id: str, *, status: str, drug_codes: list[str]) -> None:
    charge_records = [
        {
            "hospital_id": hospital_id,
            "drug_code": code,
            "gross_charge_min": 100.0,
            "gross_charge_max": 200.0,
            "source_file": f"https://example.org/{hospital_id}.json",
            "retrieved_at": "2026-07-16T00:00:00+00:00",
            "payer_rates": [],
        }
        for code in drug_codes
    ]
    data = {
        "hospital_id": hospital_id,
        "name": hospital_id,
        "mrf_url": f"https://example.org/{hospital_id}.json",
        "last_ingested_at": "2026-07-16T00:00:00+00:00",
        "enrollment_340b": "unverified",
        "enrollment_340b_checks": [],
        "charge_records": charge_records,
        "ingestion_status": status,
    }
    (tmp_path / f"{hospital_id}.json").write_text(json.dumps(data), encoding="utf-8")


def test_roster_splits_available_and_unavailable_across_categories(tmp_path, monkeypatch):
    monkeypatch.setenv("HOUSTON_HOSPITALS_PATH", str(tmp_path))
    hosp_a, hosp_b, hosp_c, hosp_d = _REAL_HOSPITAL_IDS[:4]

    # T025: select 2 drugs spanning different categories (an ADC + an immunotherapy
    # agent) and verify the roster response correctly separates hospitals that
    # publish either selected drug from hospitals that don't or failed ingestion.
    _write_hospital_file(tmp_path, hosp_a, status="success", drug_codes=["J9354", "J9271"])
    _write_hospital_file(tmp_path, hosp_b, status="success", drug_codes=["J9271"])
    _write_hospital_file(tmp_path, hosp_c, status="success", drug_codes=["J9999-untracked"])
    _write_hospital_file(tmp_path, hosp_d, status="failed: MRF fetch timed out", drug_codes=[])

    available, unavailable = build_roster(["J9354", "J9271"])

    available_ids = {entry.hospital_id for entry in available}
    assert available_ids == {hosp_a, hosp_b}

    a = next(e for e in available if e.hospital_id == hosp_a)
    assert set(a.matched_drug_codes) == {"J9354", "J9271"}
    b = next(e for e in available if e.hospital_id == hosp_b)
    assert set(b.matched_drug_codes) == {"J9271"}

    unavailable_ids = {entry.hospital_id for entry in unavailable}
    # hosp_c was successfully ingested but genuinely doesn't publish either
    # selected drug: per FR-002/FR-003 this is a normal absence, not shown
    # in either bucket.
    assert hosp_c not in available_ids
    assert hosp_c not in unavailable_ids
    assert hosp_d in unavailable_ids
    d = next(e for e in unavailable if e.hospital_id == hosp_d)
    assert d.ingestion_status == "failed: MRF fetch timed out"

    # every hospital not written to tmp_path is still reported, as not_ingested
    untouched = set(_REAL_HOSPITAL_IDS) - {hosp_a, hosp_b, hosp_c, hosp_d}
    assert untouched <= unavailable_ids


def test_roster_marks_never_ingested_hospitals_as_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("HOUSTON_HOSPITALS_PATH", str(tmp_path))

    available, unavailable = build_roster(["J9354"])

    assert available == []
    assert len(unavailable) > 0
    assert all(e.ingestion_status == "not_ingested" for e in unavailable)
