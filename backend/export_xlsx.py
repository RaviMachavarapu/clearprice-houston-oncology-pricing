"""Builds the 33-HCPCS x 44-hospital confirmation workbook straight from the
ingested houston_hospitals/*.json files. One row per (hospital, drug code)
pair that the hospital's own MRF actually contains a matched charge record
for — hospitals missing a given code simply have no row for it. Every value
is copied verbatim from the ingested record; nothing here is computed or
inferred (Constitution Principle III).
"""

from __future__ import annotations

import json

from openpyxl import Workbook

from src.config import houston_hospitals_dir
from src.reference_data.drugs import load_drugs

OUTPUT_PATH = "../docker/houston_oncology_hcpcs_confirmation.xlsx"

_HEADERS = [
    "hospital_id",
    "hospital_name",
    "hospital_ingestion_status",
    "drug_code",
    "drug_name",
    "gross_charge_min",
    "gross_charge_max",
    "payer_rate_count",
    "verified_payer_rate_count",
    "min_verified_payer_rate",
    "max_verified_payer_rate",
    "source_file",
    "retrieved_at",
]


def main() -> None:
    drug_names = {d.code: d.name for d in load_drugs()}

    wb = Workbook()
    ws = wb.active
    ws.title = "hospital_drug_rows"
    ws.append(_HEADERS)

    hospital_paths = sorted(houston_hospitals_dir().glob("*.json"))
    total_rows = 0
    for path in hospital_paths:
        hospital = json.loads(path.read_text(encoding="utf-8"))
        hospital_id = hospital["hospital_id"]
        hospital_name = hospital["name"]
        status = hospital["ingestion_status"]

        for record in hospital.get("charge_records", []):
            verified_rates = [r["rate"] for r in record["payer_rates"] if r["verified"]]
            ws.append(
                [
                    hospital_id,
                    hospital_name,
                    status,
                    record["drug_code"],
                    drug_names.get(record["drug_code"], "unknown"),
                    record["gross_charge_min"],
                    record["gross_charge_max"],
                    len(record["payer_rates"]),
                    len(verified_rates),
                    min(verified_rates) if verified_rates else None,
                    max(verified_rates) if verified_rates else None,
                    record["source_file"],
                    record["retrieved_at"],
                ]
            )
            total_rows += 1

    wb.save(OUTPUT_PATH)
    print(f"wrote {total_rows} rows from {len(hospital_paths)} hospital files -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
