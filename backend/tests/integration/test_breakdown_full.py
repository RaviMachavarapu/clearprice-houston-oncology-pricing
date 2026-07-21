from __future__ import annotations

from src.calc.breakdown import build_breakdown
from src.ingestion.charge_record import ChargeRecord, PayerRate
from src.reference_data.citation import Citation
from src.reference_data.drugs import Drug
from src.reference_data.hospitals import Hospital

_CITED = Citation(source="FDA label / CMS ASP file", access_date="2026-07-16")


def _find_field(obj) -> bool:
    """A field is provenance-valid if it's either {available: False, reason}
    or carries a 'source' key (and a 'formula' key when it's a calculated field).
    """
    if isinstance(obj, dict) and obj.get("available") is False:
        return "reason" in obj
    return "source" in obj


def test_full_breakdown_every_field_has_citation_or_not_available_marker():
    drug = Drug(
        code="J9354",
        name="Trastuzumab emtansine",
        category="Antibody-Drug Conjugates",
        dose_pattern="mg_per_kg",
        dose_value=3.6,
        dose_regimen_cited="3.6 mg/kg IV every 3 weeks",
        dose_source=_CITED,
        asp_value=100.0,
        asp_source=_CITED,
        wac_value=120.0,
        wac_source=_CITED,
    )
    hospital = Hospital(
        id="ben-taub-hospital",
        name="Ben Taub Hospital",
        mrf_url="https://example.org/ben-taub.json",
        mrf_type="json",
        ingestion_status="success",
        last_ingested_at="2026-07-16T00:00:00+00:00",
        enrollment_340b="enrolled",
        enrollment_340b_checks=[],
    )
    record = ChargeRecord(
        hospital_id="ben-taub-hospital",
        drug_code="J9354",
        gross_charge_min=8000.0,
        gross_charge_max=12000.0,
        source_file="https://example.org/ben-taub.json",
        retrieved_at="2026-07-16T00:00:00+00:00",
        payer_rates=[
            PayerRate(
                payer_name="Aetna",
                plan_name="PPO",
                billing_setting="outpatient",
                rate=9500.0,
                verification_checks=[True, True],
                verified=True,
            ),
            PayerRate(
                payer_name="Unconfirmed Payer",
                plan_name="Unknown Plan",
                billing_setting="outpatient",
                rate=15000.0,
                verification_checks=[True, False],
                verified=False,
            ),
        ],
    )

    breakdown = build_breakdown(record, drug, hospital)

    # Non-calculated fields: gross_charge, asp, wac — each must carry a source
    # or an explicit not-available marker.
    assert _find_field(breakdown["gross_charge"])
    assert _find_field(breakdown["asp"])
    assert _find_field(breakdown["wac"])

    # Calculated fields must carry both a formula and a source.
    for calc_field_name in ("asp_plus6_line", "asp_minus27_line"):
        field = breakdown[calc_field_name]
        assert field.get("available") is False or ("formula" in field and "source" in field)

    assert "formula" in breakdown["dose"]["reference_dose"]
    assert "source" in breakdown["dose"]["reference_dose"]

    # Hospital is 340B-enrolled, so the ASP-27% line must be present.
    assert "asp_minus27_line" in breakdown
    assert breakdown["asp_minus27_line"]["value"] == 73.0

    # Payer rows: verified row included with a markup ratio; unverified row
    # flagged and excluded from verified totals via unverified_exclusions.
    assert len(breakdown["payer_rates"]) == 2
    verified_row = next(r for r in breakdown["payer_rates"] if r["payer_name"] == "Aetna")
    assert verified_row["verified"] is True
    assert "formula" in verified_row["markup_ratio"]

    assert len(breakdown["unverified_exclusions"]) == 1
    assert breakdown["unverified_exclusions"][0]["payer_name"] == "Unconfirmed Payer"

    # New detail-view fields: hospital_charge_range, per_dose scaling,
    # coinsurance split (not-available here since this Drug fixture doesn't
    # set coinsurance_pct), and margin_verdict (340B-enrolled hospital).
    assert breakdown["hospital_charge_range"]["outpatient"]["min"] == 9500.0
    assert breakdown["hospital_charge_range"]["outpatient"]["max"] == 9500.0
    assert breakdown["per_dose"]["asp"]["value"] == round(100.0 * (3.6 * 70.0), 2)
    assert breakdown["medicare_coinsurance_split"]["available"] is False
    assert "margin_verdict" in breakdown
    assert breakdown["margin_verdict"]["medicare_buy_and_bill"]["profit"] is not None


def test_full_breakdown_medicare_coinsurance_split_available_when_pct_present():
    drug = Drug(
        code="J9271",
        name="Pembrolizumab",
        category="Immunotherapy",
        dose_pattern="fixed",
        dose_value=200,
        dose_regimen_cited="200 mg IV every 3 weeks",
        dose_source=_CITED,
        asp_value=60.645,
        asp_source=_CITED,
        wac_value=61.36,
        wac_source=_CITED,
        hospital_description="Inj pembrolizumab",
        billing_unit_dosage="1 MG",
        coinsurance_pct=20.0,
    )
    hospital = Hospital(
        id="houston-methodist-hospital",
        name="Houston Methodist Hospital",
        mrf_url="https://example.org/methodist.json",
        mrf_type="json",
        ingestion_status="success",
        last_ingested_at="2026-07-17T00:00:00+00:00",
        enrollment_340b="enrolled",
        enrollment_340b_checks=[],
    )
    record = ChargeRecord(
        hospital_id="houston-methodist-hospital",
        drug_code="J9271",
        gross_charge_min=None,
        gross_charge_max=None,
        source_file="https://example.org/methodist.json",
        retrieved_at="2026-07-17",
        payer_rates=[
            PayerRate("Aetna", "HMO/POS/PPO", "outpatient", 131.90, [True, True], True),
            PayerRate("BCBS", "Medicare Managed Care HMO", "outpatient", 60.29, [True, True], True),
        ],
    )

    breakdown = build_breakdown(record, drug, hospital)

    assert breakdown["hospital_description"] == "Inj pembrolizumab"
    assert breakdown["billing_unit_dosage"] == "1 MG"
    split = breakdown["medicare_coinsurance_split"]
    assert split["patient_share"]["value"] == round(60.645 * 1.06 * 0.20, 2)
    assert breakdown["per_dose"]["hospital_charge_range"]["outpatient"]["min"] == round(60.29 * 200, 2)
    assert breakdown["margin_verdict"]["lowest_medicare_managed"]["payer_name"] == "BCBS"


def test_full_breakdown_omits_asp_minus27_line_when_not_enrolled():
    drug = Drug(
        code="J9354",
        name="Trastuzumab emtansine",
        category="Antibody-Drug Conjugates",
        dose_pattern="mg_per_kg",
        dose_value=3.6,
        dose_regimen_cited="3.6 mg/kg IV every 3 weeks",
        dose_source=_CITED,
        asp_value=100.0,
        asp_source=_CITED,
        wac_value=120.0,
        wac_source=_CITED,
    )
    hospital = Hospital(
        id="ben-taub-hospital",
        name="Ben Taub Hospital",
        mrf_url="https://example.org/ben-taub.json",
        mrf_type="json",
        ingestion_status="success",
        last_ingested_at="2026-07-16T00:00:00+00:00",
        enrollment_340b="not_enrolled",
        enrollment_340b_checks=[],
    )
    record = ChargeRecord(
        hospital_id="ben-taub-hospital",
        drug_code="J9354",
        gross_charge_min=8000.0,
        gross_charge_max=12000.0,
        source_file="https://example.org/ben-taub.json",
        retrieved_at="2026-07-16T00:00:00+00:00",
        payer_rates=[],
    )

    breakdown = build_breakdown(record, drug, hospital)

    assert "asp_minus27_line" not in breakdown
