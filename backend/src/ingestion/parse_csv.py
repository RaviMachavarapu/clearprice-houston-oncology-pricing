from __future__ import annotations

import csv
import io

from src.ingestion.charge_record import ChargeRecord
from src.ingestion.tall_format import (
    find_tracked_code_column_indices,
    parse_tall_rows,
    row_matches_tracked_code,
)

_MAX_HEADER_SCAN_ROWS = 10


def _find_header_row(rows: list[list[str]]) -> int | None:
    """CMS standard-charges CSV files carry a 2-row hospital-identifier preamble
    above the actual tall-format header row. Scan the first few rows for the
    one that looks like a real header (contains a `code|1` column).
    """
    for i, row in enumerate(rows[:_MAX_HEADER_SCAN_ROWS]):
        cells = [c.strip() if c is not None else "" for c in row]
        if "code|1" in cells:
            return i
    return None


def parse_csv_mrf(raw_text: str, hospital_id: str, source_file: str) -> list[ChargeRecord]:
    """Parse a hospital's CMS-standard-charges-format CSV MRF into Charge Records,
    filtered to the 33 tracked oncology drug codes (plan.md Technical Context).
    """
    all_rows = list(csv.reader(io.StringIO(raw_text)))

    header_idx = _find_header_row(all_rows)
    if header_idx is None:
        raise ValueError(
            "could not find CMS tall-format header row (no 'code|1' column in first "
            f"{_MAX_HEADER_SCAN_ROWS} rows) — file is not in the expected standard-charges layout"
        )

    header = [c.strip() if c is not None else "" for c in all_rows[header_idx]]
    code_col_indices = find_tracked_code_column_indices(header)
    dict_rows = [
        {header[i]: row[i] for i in range(len(header)) if i < len(row)}
        for row in all_rows[header_idx + 1 :]
        if row_matches_tracked_code(row, code_col_indices)
    ]

    return parse_tall_rows(dict_rows, hospital_id, source_file)
