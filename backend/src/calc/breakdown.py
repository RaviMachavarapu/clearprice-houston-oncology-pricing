from __future__ import annotations

from src.calc.cgt_risk import cgt_risk_flag
from src.calc.charge_range import hospital_charge_range
from src.calc.coinsurance import medicare_coinsurance_split
from src.calc.dose import dose_line
from src.calc.dose_scaling import scale_to_dose
from src.calc.margin_verdict import margin_verdict, wac_margin_scenario
from src.calc.markup import payer_markup_row
from src.calc.reimbursement import asp_minus27_line, asp_plus6_line
from src.ingestion.charge_record import ChargeRecord
from src.reference_data.drugs import Drug
from src.verification.provenance_gate import (
    assert_calculated_field_provenance,
    assert_quoted_field_provenance,
)


def _gross_charge_field(record: ChargeRecord) -> dict:
    if record.gross_charge_min is None and record.gross_charge_max is None:
        return {"available": False, "reason": "gross charge not published in hospital's MRF"}
    return {
        "min": record.gross_charge_min,
        "max": record.gross_charge_max,
        "source": {"source": record.source_file, "access_date": record.retrieved_at},
    }


def _reference_price_field(value: float | None, source, label: str) -> dict:
    if value is None:
        reason = source.reason if hasattr(source, "reason") else f"{label} not publicly available"
        return {"available": False, "reason": reason}
    return {"value": value, "source": source.to_dict()}


def _gate_bucketed_field(field: dict, field_name: str) -> None:
    """Gate a charge_range/per_dose-shaped field: either a single top-level
    not-available marker, or a dict of per-setting buckets each requiring
    their own formula+source/not-available marker."""
    if field.get("available") is False:
        assert_calculated_field_provenance(field, field_name)
        return
    for setting, bucket in field.items():
        assert_calculated_field_provenance(bucket, f"{field_name}[{setting}]")


def build_breakdown(record: ChargeRecord, drug: Drug, hospital) -> dict:
    """Assemble the full Section-4-style Pricing Breakdown for one hospital/drug
    pair (FR-004 through FR-012). Every field carries a citation or an explicit
    not-available marker; every calculated field is passed through the
    Constitution Principle VI provenance gate before being included.
    """
    gross_charge = _gross_charge_field(record)
    assert_quoted_field_provenance(gross_charge, "gross_charge")
    asp_field = _reference_price_field(drug.asp_value, drug.asp_source, "ASP")
    assert_quoted_field_provenance(asp_field, "asp")
    wac_field = _reference_price_field(drug.wac_value, drug.wac_source, "WAC")
    assert_quoted_field_provenance(wac_field, "wac")

    asp6 = asp_plus6_line(drug)
    assert_calculated_field_provenance(asp6, "asp_plus6_line")

    dose = dose_line(drug)
    assert_calculated_field_provenance(dose["reference_dose"], "dose.reference_dose")

    cgt = cgt_risk_flag(drug.code, drug.wac_value)
    assert_calculated_field_provenance(cgt, "cgt_risk_flag")

    payer_rows = []
    unverified_exclusions = []
    for payer_rate in record.payer_rates:
        row = payer_markup_row(payer_rate, drug, record.source_file, record.retrieved_at)
        assert_calculated_field_provenance(row["markup_ratio"], f"markup_ratio[{payer_rate.payer_name}]")
        payer_rows.append(row)
        if not payer_rate.verified:
            unverified_exclusions.append(
                {
                    "payer_name": payer_rate.payer_name,
                    "plan_name": payer_rate.plan_name,
                    "reason": "payer/plan name could not be independently confirmed against the hospital's raw MRF (Principle II double-check failed)",
                    "verification_checks": list(payer_rate.verification_checks),
                }
            )

    charge_range = hospital_charge_range(record)
    _gate_bucketed_field(charge_range, "hospital_charge_range")

    breakdown: dict = {
        "hospital_id": hospital.id,
        "hospital_name": hospital.name,
        "drug_code": drug.code,
        "drug_name": drug.name,
        "hospital_description": drug.hospital_description,
        "billing_unit_dosage": drug.billing_unit_dosage,
        "gross_charge": gross_charge,
        "hospital_charge_range": charge_range,
        "asp": asp_field,
        "wac": wac_field,
        "asp_plus6_line": asp6,
        "dose": dose,
        "cgt_risk_flag": cgt,
        "payer_rates": payer_rows,
        "unverified_exclusions": unverified_exclusions,
        "enrollment_340b": getattr(hospital, "enrollment_340b", "unverified"),
    }

    dose_value = dose["reference_dose"].get("value")
    dose_unit = dose["reference_dose"].get("unit", "mg")
    if dose_value is not None:
        scaled_charge_range = scale_to_dose(charge_range, dose_value, dose_unit)
        scaled_asp = scale_to_dose(asp_field, dose_value, dose_unit)
        scaled_wac = scale_to_dose(wac_field, dose_value, dose_unit)
        scaled_asp6 = scale_to_dose(asp6, dose_value, dose_unit)
        _gate_bucketed_field(scaled_charge_range, "per_dose.hospital_charge_range")
        assert_calculated_field_provenance(scaled_asp, "per_dose.asp")
        assert_calculated_field_provenance(scaled_wac, "per_dose.wac")
        assert_calculated_field_provenance(scaled_asp6, "per_dose.asp_plus6_line")
        breakdown["per_dose"] = {
            "hospital_charge_range": scaled_charge_range,
            "asp": scaled_asp,
            "wac": scaled_wac,
            "asp_plus6_line": scaled_asp6,
        }

        scaled_wac_scenario = wac_margin_scenario(scaled_asp6, scaled_wac, unit="dose")
        assert_calculated_field_provenance(scaled_wac_scenario, "per_dose.margin_verdict.medicare_vs_wac")
        breakdown["per_dose"]["margin_verdict"] = {"medicare_vs_wac": scaled_wac_scenario}

    coinsurance = medicare_coinsurance_split(asp6, drug.coinsurance_pct)
    if coinsurance.get("available") is False:
        assert_calculated_field_provenance(coinsurance, "medicare_coinsurance_split")
    else:
        assert_calculated_field_provenance(coinsurance["medicare_share"], "medicare_coinsurance_split.medicare_share")
        assert_calculated_field_provenance(coinsurance["patient_share"], "medicare_coinsurance_split.patient_share")
        if dose_value is not None and "per_dose" in breakdown:
            scaled_medicare_share = scale_to_dose(coinsurance["medicare_share"], dose_value, dose_unit)
            scaled_patient_share = scale_to_dose(coinsurance["patient_share"], dose_value, dose_unit)
            assert_calculated_field_provenance(scaled_medicare_share, "per_dose.medicare_coinsurance_split.medicare_share")
            assert_calculated_field_provenance(scaled_patient_share, "per_dose.medicare_coinsurance_split.patient_share")
            breakdown["per_dose"]["medicare_coinsurance_split"] = {
                "medicare_share": scaled_medicare_share,
                "patient_share": scaled_patient_share,
            }
    breakdown["medicare_coinsurance_split"] = coinsurance

    # WAC-vs-Medicare margin: independent of 340B enrollment, since WAC is a
    # public list price every hospital can be compared against. Always
    # computed when ASP+6% and WAC are both available.
    wac_scenario = wac_margin_scenario(asp6, wac_field)
    assert_calculated_field_provenance(wac_scenario, "margin_verdict.medicare_vs_wac")
    breakdown["margin_verdict"] = {"medicare_vs_wac": wac_scenario}

    # FR-013: the 340B (ASP-27%) line only appears when both HRSA double-checks
    # agree the hospital is enrolled — never assumed, never shown as
    # `unverified`-but-included.
    if breakdown["enrollment_340b"] == "enrolled":
        asp27 = asp_minus27_line(drug)
        assert_calculated_field_provenance(asp27, "asp_minus27_line")
        breakdown["asp_minus27_line"] = asp27
        if dose_value is not None:
            scaled_asp27 = scale_to_dose(asp27, dose_value, dose_unit)
            assert_calculated_field_provenance(scaled_asp27, "per_dose.asp_minus27_line")
            breakdown["per_dose"]["asp_minus27_line"] = scaled_asp27

            scaled_payer_rows = [
                {**row, "rate": scale_to_dose(row["rate"], dose_value, dose_unit)} for row in payer_rows
            ]
            scaled_verdict = margin_verdict(scaled_asp6, scaled_asp27, scaled_payer_rows, unit="dose")
            if scaled_verdict is not None:
                assert_calculated_field_provenance(
                    scaled_verdict["medicare_buy_and_bill"], "per_dose.margin_verdict.medicare_buy_and_bill"
                )
                assert_calculated_field_provenance(
                    scaled_verdict["highest_commercial"], "per_dose.margin_verdict.highest_commercial"
                )
                assert_calculated_field_provenance(
                    scaled_verdict["lowest_medicare_managed"], "per_dose.margin_verdict.lowest_medicare_managed"
                )
                breakdown["per_dose"]["margin_verdict"].update(scaled_verdict)

        verdict = margin_verdict(asp6, asp27, payer_rows)
        if verdict is not None:
            assert_calculated_field_provenance(verdict["medicare_buy_and_bill"], "margin_verdict.medicare_buy_and_bill")
            assert_calculated_field_provenance(verdict["highest_commercial"], "margin_verdict.highest_commercial")
            assert_calculated_field_provenance(verdict["lowest_medicare_managed"], "margin_verdict.lowest_medicare_managed")
            breakdown["margin_verdict"].update(verdict)

    return breakdown
