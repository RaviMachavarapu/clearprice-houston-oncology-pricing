from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable

from src.ingestion.charge_record import ChargeRecord, PayerRate
from src.ingestion.tracked_codes import load_tracked_codes

_TRACKED_CODES = load_tracked_codes()

# CMS "tall" format (CSV or XLSX): one or more `code|N` / `code|N|type` column pairs
# per row, a `setting`, `standard_charge|gross`, and repeating
# `standard_charge|<payer>|<plan>|negotiated_dollar` payer columns.
_CODE_COL = re.compile(r"^code\|(\d+)$")
_PAYER_COL = re.compile(r"^standard_charge\|(.+)\|(.+)\|negotiated_dollar$")


def find_tracked_code_column_indices(header: list) -> list[int]:
    """Positions in `header` that hold a `code|N` column. Lets callers check
    whether a raw row (list of cell values) matches a tracked drug code via cheap
    index lookups, without building a full column-name dict for every row first —
    the dict is only worth building for the handful of rows that actually match
    (CMS tall-format files can have hundreds of payer columns and hundreds of
    thousands of rows; dict-per-row for all of them dominates parse time).
    """
    return [i for i, c in enumerate(header) if c and _CODE_COL.match(c)]


def row_matches_tracked_code(row: list, code_col_indices: list[int]) -> bool:
    return any(i < len(row) and row[i] in _TRACKED_CODES for i in code_col_indices)


def parse_tall_rows(rows: Iterable[dict], hospital_id: str, source_file: str) -> list[ChargeRecord]:
    """Parse CMS "tall" format rows (already dict-per-row, whether sourced from a
    CSV DictReader or an Excel worksheet) into Charge Records, filtered to the 33
    tracked oncology drug codes (plan.md Technical Context).

    Only quotes what the hospital's own file states — no computed or inferred
    values (Constitution Principle III).
    """
    retrieved_at = datetime.now(timezone.utc).date().isoformat()
    rows = list(rows)
    fieldnames = [c for c in rows[0].keys() if c is not None] if rows else []

    code_cols = sorted({m.group(1) for c in fieldnames if (m := _CODE_COL.match(c))})
    payer_cols = [(c, *m.groups()) for c in fieldnames if (m := _PAYER_COL.match(c))]

    records: list[ChargeRecord] = []

    for row in rows:
        matched_code = None
        for n in code_cols:
            if row.get(f"code|{n}") in _TRACKED_CODES:
                matched_code = row[f"code|{n}"]
                break
        if matched_code is None:
            continue

        setting = row.get("setting", "unknown")
        gross_value = row.get("standard_charge|gross")
        gross = float(gross_value) if gross_value not in (None, "") else None

        payer_rates: list[PayerRate] = []
        for col, payer_name, plan_name in payer_cols:
            raw_rate = row.get(col)
            if raw_rate in (None, ""):
                continue
            payer_rates.append(
                PayerRate(
                    payer_name=payer_name,
                    plan_name=plan_name,
                    billing_setting=setting,
                    rate=float(raw_rate),
                )
            )

        records.append(
            ChargeRecord(
                hospital_id=hospital_id,
                drug_code=matched_code,
                gross_charge_min=gross,
                gross_charge_max=gross,
                source_file=source_file,
                retrieved_at=retrieved_at,
                payer_rates=payer_rates,
            )
        )

    return records
