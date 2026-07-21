from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .citation import Citation, NotAvailable, SourceRef

_RESEARCH_DIR = Path(__file__).parent / "fda_wac_research"
_ASP_PATH = Path(__file__).parent / "oncology_top5_asp_reference.json"
_ASP_ACCESS_DATE = "2026-07-16"

_DOSE_PATTERN_MAP = {
    "fixed": "fixed",
    "mg_per_kg": "mg_per_kg",
    "weight_based": "mg_per_kg",
    "mg_per_m2": "mg_per_m2",
    "bsa_based": "mg_per_m2",
    "single_infusion_cell_dose": "fixed",
}


@dataclass(frozen=True)
class Drug:
    code: str
    name: str
    category: str
    dose_pattern: str
    dose_value: float
    dose_regimen_cited: str
    dose_source: Citation
    asp_value: float | None
    asp_source: SourceRef
    wac_value: float | None
    wac_source: SourceRef
    hospital_description: str = ""
    billing_unit_dosage: str | None = None
    coinsurance_pct: float | None = None


def _source_ref(entry: dict) -> SourceRef:
    if entry.get("available") is False:
        return NotAvailable(reason=entry["reason"])
    return Citation(source=entry["url"], access_date=entry["access_date"])


def _load_asp_by_code() -> dict[str, dict]:
    data = json.loads(_ASP_PATH.read_text(encoding="utf-8"))
    return {d["hcpcs_code"]: d for d in data["drugs"]}


def load_drugs() -> list[Drug]:
    """Load the 33 tracked oncology drugs from the T005a category research files.

    CGT drugs (single-infusion cell therapies, e.g. Yescarta) carry
    dose_pattern="fixed", dose_value=1 — their wac_value is already the
    full per-treatment price, so no per-mg/kg/m2 multiplication applies.
    The labeled cell-dose regimen is preserved in dose_regimen_cited.
    """
    asp_by_code = _load_asp_by_code()
    drugs: list[Drug] = []

    for path in sorted(_RESEARCH_DIR.glob("*.json")):
        entries = json.loads(path.read_text(encoding="utf-8"))
        for entry in entries:
            code = entry["code"]
            raw_pattern = entry["dose_pattern"]
            dose_pattern = _DOSE_PATTERN_MAP[raw_pattern]
            dose_value = 1.0 if raw_pattern == "single_infusion_cell_dose" else entry["dose_value"]

            asp_entry = asp_by_code.get(code)
            raw_limit = asp_entry.get("payment_limit_per_unit_usd") if asp_entry else None
            if raw_limit is not None:
                asp_value = float(raw_limit)
                asp_source: SourceRef = Citation(
                    source=asp_entry["reference_source"],
                    access_date=_ASP_ACCESS_DATE,
                )
            else:
                asp_value = None
                reason = (
                    asp_entry.get("status", "not payable under CMS Part B ASP file")
                    if asp_entry is not None
                    else "not present in CMS ASP reference file"
                )
                asp_source = NotAvailable(reason=reason)

            coinsurance_raw = asp_entry.get("coinsurance_pct") if asp_entry else None
            drugs.append(
                Drug(
                    code=code,
                    name=entry["name"],
                    category=entry["category"],
                    dose_pattern=dose_pattern,
                    dose_value=dose_value,
                    dose_regimen_cited=entry["dose_regimen_cited"],
                    dose_source=Citation(
                        source=entry["dose_source"]["url"],
                        access_date=entry["dose_source"]["access_date"],
                    ),
                    asp_value=asp_value,
                    asp_source=asp_source,
                    wac_value=entry["wac_value"],
                    wac_source=_source_ref(entry["wac_source"]),
                    hospital_description=asp_entry.get("hospital_description", "") if asp_entry else "",
                    billing_unit_dosage=asp_entry.get("billing_unit_dosage") if asp_entry else None,
                    coinsurance_pct=float(coinsurance_raw) if coinsurance_raw is not None else None,
                )
            )

    return drugs
