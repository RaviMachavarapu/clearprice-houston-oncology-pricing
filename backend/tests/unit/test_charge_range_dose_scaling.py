from __future__ import annotations

from src.calc.charge_range import hospital_charge_range
from src.calc.coinsurance import medicare_coinsurance_split
from src.calc.dose_scaling import scale_to_dose
from src.calc.margin_verdict import margin_verdict
from src.ingestion.charge_record import ChargeRecord, PayerRate

_SOURCE = {"source": "https://example.org/mrf.json", "access_date": "2026-07-17"}


def _record(payer_rates):
    return ChargeRecord(
        hospital_id="houston-methodist-hospital",
        drug_code="J9271",
        gross_charge_min=None,
        gross_charge_max=None,
        source_file="https://example.org/mrf.json",
        retrieved_at="2026-07-17",
        payer_rates=payer_rates,
    )


def _rate(payer, plan, setting, rate, verified=True):
    return PayerRate(
        payer_name=payer,
        plan_name=plan,
        billing_setting=setting,
        rate=rate,
        verification_checks=[True, True] if verified else [True, False],
        verified=verified,
    )


def test_hospital_charge_range_groups_by_setting_and_ignores_unverified():
    record = _record(
        [
            _rate("Aetna", "HMO", "outpatient", 131.90),
            _rate("BCBS", "Medicare Managed HMO", "outpatient", 60.29),
            _rate("Cigna", "TX HealthSpring", "inpatient", 60.29),
            _rate("Unconfirmed", "Unknown", "outpatient", 999.0, verified=False),
        ]
    )
    result = hospital_charge_range(record)
    assert result["outpatient"]["min"] == 60.29
    assert result["outpatient"]["max"] == 131.90
    assert result["outpatient"]["payer_count"] == 2
    assert result["inpatient"]["min"] == 60.29
    assert result["inpatient"]["max"] == 60.29
    assert "source" in result["outpatient"]


def test_hospital_charge_range_not_available_when_no_verified_rates():
    record = _record([_rate("Unconfirmed", "Unknown", "outpatient", 999.0, verified=False)])
    result = hospital_charge_range(record)
    assert result["available"] is False


def test_scale_to_dose_flat_field():
    field = {"value": 60.645, "source": _SOURCE}
    scaled = scale_to_dose(field, 200, "mg")
    assert scaled["value"] == 12129.0
    assert "200" in scaled["formula"]
    assert scaled["source"] == _SOURCE


def test_scale_to_dose_passes_through_not_available():
    field = {"available": False, "reason": "WAC not publicly available"}
    assert scale_to_dose(field, 200, "mg") == field


def test_scale_to_dose_bucketed_charge_range():
    field = {
        "outpatient": {"min": 60.29, "max": 318.01, "payer_count": 17, "formula": "x", "source": _SOURCE},
    }
    scaled = scale_to_dose(field, 200, "mg")
    assert scaled["outpatient"]["min"] == 12058.0
    assert scaled["outpatient"]["max"] == 63602.0


def test_medicare_coinsurance_split_standard_20pct():
    asp6 = {"value": 64.28, "formula": "$60.645 * 1.06", "source": _SOURCE}
    result = medicare_coinsurance_split(asp6, 20.0)
    assert result["patient_share"]["value"] == 12.86
    assert result["medicare_share"]["value"] == 51.42


def test_medicare_coinsurance_split_not_available_without_pct():
    asp6 = {"value": 64.28, "formula": "x", "source": _SOURCE}
    result = medicare_coinsurance_split(asp6, None)
    assert result["available"] is False


def test_margin_verdict_classifies_commercial_vs_medicare_managed():
    asp6 = {"value": 64.28, "formula": "x", "source": _SOURCE}
    asp27 = {"value": 44.27, "formula": "x", "source": _SOURCE}
    payer_rows = [
        {"payer_name": "UnitedHealthcare", "plan_name": "All Commercial Plans", "rate": {"value": 318.01}, "verified": True},
        {"payer_name": "BCBS", "plan_name": "Medicare Managed Care - HMO", "rate": {"value": 60.29}, "verified": True},
        {"payer_name": "Excluded", "plan_name": "Medicare Managed Care - HMO", "rate": {"value": 1.0}, "verified": False},
    ]
    verdict = margin_verdict(asp6, asp27, payer_rows)
    assert verdict["medicare_buy_and_bill"]["profit"] == 20.01
    assert verdict["highest_commercial"]["payer_name"] == "UnitedHealthcare"
    assert verdict["highest_commercial"]["profit"] == 273.74
    assert verdict["lowest_medicare_managed"]["payer_name"] == "BCBS"
    assert verdict["lowest_medicare_managed"]["profit"] == 16.02


def test_margin_verdict_not_available_scenario_when_no_matching_rows():
    asp6 = {"value": 64.28, "formula": "x", "source": _SOURCE}
    asp27 = {"value": 44.27, "formula": "x", "source": _SOURCE}
    payer_rows = [
        {"payer_name": "UnitedHealthcare", "plan_name": "All Commercial Plans", "rate": {"value": 318.01}, "verified": True},
    ]
    verdict = margin_verdict(asp6, asp27, payer_rows)
    assert verdict["lowest_medicare_managed"]["available"] is False
