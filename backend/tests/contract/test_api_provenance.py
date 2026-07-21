from __future__ import annotations

import json

from fastapi.testclient import TestClient

from src.reference_data.hospitals import load_hospitals

_REAL_HOSPITAL_ID = load_hospitals()[0].id
_REAL_DRUG_CODE = "J9354"


def _field_has_provenance(field: dict, *, calculated: bool) -> bool:
    if field.get("available") is False:
        return bool(field.get("reason"))
    if calculated:
        return bool(field.get("formula")) and bool(field.get("source"))
    return bool(field.get("source"))


def test_get_breakdowns_never_returns_a_field_missing_provenance(tmp_path, monkeypatch):
    """End-to-end contract test: hits the real GET /api/breakdowns route (not
    build_breakdown directly) so a wiring bug in the API layer — e.g. a field
    assembled in breakdowns.py without going through the provenance gate —
    would be caught here even if the calc-engine unit tests pass.
    """
    monkeypatch.setenv("HOUSTON_HOSPITALS_PATH", str(tmp_path))

    data = {
        "hospital_id": _REAL_HOSPITAL_ID,
        "name": _REAL_HOSPITAL_ID,
        "mrf_url": f"https://example.org/{_REAL_HOSPITAL_ID}.json",
        "last_ingested_at": "2026-07-16T00:00:00+00:00",
        "enrollment_340b": "enrolled",
        "enrollment_340b_checks": [],
        "ingestion_status": "success",
        "charge_records": [
            {
                "hospital_id": _REAL_HOSPITAL_ID,
                "drug_code": _REAL_DRUG_CODE,
                "gross_charge_min": 8000.0,
                "gross_charge_max": 12000.0,
                "source_file": f"https://example.org/{_REAL_HOSPITAL_ID}.json",
                "retrieved_at": "2026-07-16T00:00:00+00:00",
                "payer_rates": [
                    {
                        "payer_name": "Aetna",
                        "plan_name": "PPO",
                        "billing_setting": "outpatient",
                        "rate": 9500.0,
                        "verification_checks": [True, True],
                        "verified": True,
                    }
                ],
            }
        ],
    }
    (tmp_path / f"{_REAL_HOSPITAL_ID}.json").write_text(json.dumps(data), encoding="utf-8")

    from src.api.main import app

    client = TestClient(app)
    response = client.get("/api/breakdowns", params={"drugs": _REAL_DRUG_CODE})
    assert response.status_code == 200
    body = response.json()

    assert len(body["breakdowns"]) == 1
    breakdown = body["breakdowns"][0]

    for field_name in ("gross_charge", "asp", "wac"):
        assert _field_has_provenance(breakdown[field_name], calculated=False), field_name

    for field_name in ("asp_plus6_line", "dose", "cgt_risk_flag"):
        field = breakdown[field_name]
        if field_name == "dose":
            field = field["reference_dose"]
        assert _field_has_provenance(field, calculated=True), field_name

    for row in breakdown["payer_rates"]:
        assert _field_has_provenance(row["markup_ratio"], calculated=True)

    if "asp_minus27_line" in breakdown:
        assert _field_has_provenance(breakdown["asp_minus27_line"], calculated=True)
