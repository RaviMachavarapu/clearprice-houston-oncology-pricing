from __future__ import annotations

# Cellular and Gene Therapy DRG-risk codes (Epic 4 flagging, per plan.md §6):
# these HCPCS codes are billed under DRGs whose average payment can fall far
# below the therapy's ASP/WAC, creating margin risk if a hospital doesn't
# separately negotiate. Thresholds are the relevant FY DRG average payments.
_CGT_RISK_CODES = {"Q2041", "Q2042", "Q2055", "Q2054", "Q2056"}

_DRG_AVERAGE_PAYMENT_LOW = 269_139.0
_DRG_AVERAGE_PAYMENT_HIGH = 314_231.0

_DRG_SOURCE = {
    "source": "CMS FY DRG average payment reference (research.md §6)",
    "access_date": "2026-07-16",
}


def cgt_risk_flag(drug_code: str, wac_value: float | None) -> dict:
    """Flag CGT drugs whose WAC/ASP price exceeds typical inpatient DRG
    reimbursement, per Epic 4's DRG-risk callout.

    Returns an explicit not-available marker for non-CGT codes rather than a
    bare false, so the calc engine never silently omits the field.
    """
    if drug_code not in _CGT_RISK_CODES:
        return {"available": False, "reason": "not a tracked CGT DRG-risk code"}

    if wac_value is None:
        return {"available": False, "reason": "WAC not publicly available; DRG-risk comparison cannot be made"}

    at_risk = wac_value > _DRG_AVERAGE_PAYMENT_LOW
    severity = "high" if wac_value > _DRG_AVERAGE_PAYMENT_HIGH else ("moderate" if at_risk else "low")

    return {
        "value": at_risk,
        "severity": severity,
        "formula": (
            f"WAC (${wac_value:,.2f}) compared to DRG average payment range "
            f"(${_DRG_AVERAGE_PAYMENT_LOW:,.2f}-${_DRG_AVERAGE_PAYMENT_HIGH:,.2f})"
        ),
        "source": _DRG_SOURCE,
    }
