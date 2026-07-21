from __future__ import annotations

from src.calc.cgt_risk import cgt_risk_flag
from src.calc.dose import dose_line
from src.calc.markup import payer_markup_row
from src.calc.reimbursement import asp_minus27_line, asp_plus6_line
from src.ingestion.charge_record import PayerRate
from src.reference_data.citation import Citation, NotAvailable
from src.reference_data.drugs import Drug

_CITED = Citation(source="FDA label", access_date="2026-07-16")


def _drug(**overrides) -> Drug:
    base = dict(
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
    base.update(overrides)
    return Drug(**base)


def test_asp_plus6_line_applies_multiplier_and_carries_formula_and_source():
    line = asp_plus6_line(_drug(asp_value=100.0))
    assert line["value"] == 106.0
    assert "1.06" in line["formula"]
    assert line["source"] == _CITED.to_dict()


def test_asp_plus6_line_returns_not_available_when_asp_missing():
    line = asp_plus6_line(_drug(asp_value=None, asp_source=NotAvailable(reason="ASP not publicly available")))
    assert line["available"] is False
    assert line["reason"]


def test_asp_minus27_line_applies_multiplier():
    line = asp_minus27_line(_drug(asp_value=100.0))
    assert line["value"] == 73.0
    assert "0.73" in line["formula"]


def test_dose_line_mg_per_kg_uses_reference_weight():
    dose = dose_line(_drug(dose_pattern="mg_per_kg", dose_value=3.6))
    assert dose["reference_dose"]["value"] == 252.0  # 3.6 * 70kg
    assert "70" in dose["reference_dose"]["formula"]
    assert dose["reference_dose"]["source"] == _CITED.to_dict()


def test_dose_line_mg_per_m2_uses_reference_bsa():
    dose = dose_line(_drug(dose_pattern="mg_per_m2", dose_value=100.0))
    assert dose["reference_dose"]["value"] == 170.0  # 100 * 1.7m^2


def test_dose_line_fixed_uses_value_as_is():
    dose = dose_line(_drug(dose_pattern="fixed", dose_value=500.0))
    assert dose["reference_dose"]["value"] == 500.0


def test_cgt_risk_flag_not_available_for_non_cgt_code():
    flag = cgt_risk_flag("J9354", wac_value=100.0)
    assert flag["available"] is False


def test_cgt_risk_flag_high_severity_above_drg_high_threshold():
    flag = cgt_risk_flag("Q2041", wac_value=400_000.0)
    assert flag["value"] is True
    assert flag["severity"] == "high"
    assert "formula" in flag


def test_cgt_risk_flag_low_severity_below_drg_low_threshold():
    flag = cgt_risk_flag("Q2041", wac_value=100_000.0)
    assert flag["value"] is False
    assert flag["severity"] == "low"


def test_cgt_risk_flag_not_available_without_wac():
    flag = cgt_risk_flag("Q2041", wac_value=None)
    assert flag["available"] is False


def test_payer_markup_row_computes_ratio_and_flags_above_threshold():
    rate = PayerRate(
        payer_name="Aetna",
        plan_name="PPO",
        billing_setting="outpatient",
        rate=400.0,
        verification_checks=[True, True],
        verified=True,
    )
    row = payer_markup_row(rate, _drug(asp_value=100.0), "https://example.org/mrf.json", "2026-07-16T00:00:00+00:00")
    assert row["markup_ratio"]["value"] == 4.0
    assert row["markup_ratio_flag"] is True


def test_payer_markup_row_not_flagged_below_threshold():
    rate = PayerRate(
        payer_name="Aetna",
        plan_name="PPO",
        billing_setting="outpatient",
        rate=200.0,
        verification_checks=[True, True],
        verified=True,
    )
    row = payer_markup_row(rate, _drug(asp_value=100.0), "https://example.org/mrf.json", "2026-07-16T00:00:00+00:00")
    assert row["markup_ratio"]["value"] == 2.0
    assert row["markup_ratio_flag"] is False


def test_payer_markup_row_not_available_when_asp_missing():
    rate = PayerRate(
        payer_name="Aetna",
        plan_name="PPO",
        billing_setting="outpatient",
        rate=200.0,
        verification_checks=[True, True],
        verified=True,
    )
    row = payer_markup_row(rate, _drug(asp_value=None), "https://example.org/mrf.json", "2026-07-16T00:00:00+00:00")
    assert row["markup_ratio"]["available"] is False
    assert row["markup_ratio_flag"] is False
