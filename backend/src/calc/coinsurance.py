from __future__ import annotations


def medicare_coinsurance_split(asp_plus6_line: dict, coinsurance_pct: float | None) -> dict:
    """Standard Medicare Part B coinsurance split of the ASP+6% reimbursement
    line into the Medicare-paid share and the patient-owed share, using the
    drug's own coinsurance_pct from the CMS ASP reference file (per-drug,
    not assumed to always be 20%).
    """
    if asp_plus6_line.get("available") is False:
        return {"available": False, "reason": "ASP + 6% reimbursement not available; coinsurance split cannot be computed"}
    if coinsurance_pct is None:
        return {"available": False, "reason": "coinsurance_pct not published in CMS ASP reference file for this drug"}

    reimbursement = asp_plus6_line["value"]
    patient_share = round(reimbursement * coinsurance_pct / 100, 2)
    medicare_share = round(reimbursement - patient_share, 2)
    source = asp_plus6_line.get("source")

    return {
        "coinsurance_pct": coinsurance_pct,
        "medicare_share": {
            "value": medicare_share,
            "formula": f"${reimbursement} x (1 - {coinsurance_pct}%)",
            "source": source,
        },
        "patient_share": {
            "value": patient_share,
            "formula": f"${reimbursement} x {coinsurance_pct}%",
            "source": source,
        },
    }
