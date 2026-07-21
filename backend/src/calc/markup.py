from __future__ import annotations

from src.ingestion.charge_record import PayerRate
from src.reference_data.drugs import Drug

MARKUP_FLAG_THRESHOLD = 3.0


def payer_markup_row(payer_rate: PayerRate, drug: Drug, source_file: str, retrieved_at: str) -> dict:
    """Per-payer markup ratio (payer_rate / asp_value), per FR-005.

    Not aggregated across payers — each row stands on its own citation. The
    charge record's own billing_setting is carried through untouched, never
    re-derived. If the drug's ASP is not publicly available, the ratio is
    omitted (not computed against a null/None value).
    """
    row = {
        "payer_name": payer_rate.payer_name,
        "plan_name": payer_rate.plan_name,
        "billing_setting": payer_rate.billing_setting,
        "rate": {
            "value": payer_rate.rate,
            "source": {"source": source_file, "access_date": retrieved_at},
        },
        "verified": payer_rate.verified,
        "verification_checks": list(payer_rate.verification_checks),
    }

    if drug.asp_value is None or drug.asp_value == 0:
        row["markup_ratio"] = {
            "available": False,
            "reason": "ASP not publicly available; markup ratio cannot be computed",
        }
        row["markup_ratio_flag"] = False
        return row

    ratio = payer_rate.rate / drug.asp_value
    row["markup_ratio"] = {
        "value": round(ratio, 3),
        "formula": f"payer_rate (${payer_rate.rate:.2f}) / ASP (${drug.asp_value:.2f})",
        "source": {"source": source_file, "access_date": retrieved_at},
    }
    row["markup_ratio_flag"] = ratio > MARKUP_FLAG_THRESHOLD
    return row
