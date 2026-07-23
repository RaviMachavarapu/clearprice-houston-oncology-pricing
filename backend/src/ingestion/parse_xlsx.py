from __future__ import annotations

import io

import openpyxl

from src.ingestion.charge_record import ChargeRecord
from src.ingestion.tall_format import (
    find_tracked_code_column_indices,
    parse_tall_rows,
    row_matches_tracked_code,
)

_MAX_HEADER_SCAN_ROWS = 10


def _find_header_row(rows: list[tuple]) -> int | None:
    """CMS standard-charges XLSX files sometimes carry a title/notes preamble
    above the actual tall-format header row. Scan the first few rows for the
    one that looks like a real header (contains a `code|1` column).
    """
    for i, row in enumerate(rows[:_MAX_HEADER_SCAN_ROWS]):
        cells = [str(c).strip() if c is not None else "" for c in row]
        if "code|1" in cells:
            return i
    return None


def parse_xlsx_mrf(raw_bytes: bytes, hospital_id: str, source_file: str) -> tuple[list[ChargeRecord], str]:
    """Parse a hospital's CMS-standard-charges-format XLSX/XLSM MRF into Charge
    Records, filtered to the 33 tracked oncology drug codes. Reuses the same
    tall-format column rules as the CSV parser (plan.md Technical Context).

    Returns (records, raw_text) — raw_text is a flattened dump of every cell,
    used by the payer-scheme double-check verifier the same way CSV/JSON text is.
    """
    workbook = openpyxl.load_workbook(io.BytesIO(raw_bytes), read_only=True, data_only=True)
    worksheet = workbook.worksheets[0]
    all_rows = list(worksheet.iter_rows(values_only=True))

    raw_text = "\n".join(
        ",".join("" if cell is None else str(cell) for cell in row) for row in all_rows
    )

    header_idx = _find_header_row(all_rows)
    if header_idx is None:
        raise ValueError(
            "could not find CMS tall-format header row (no 'code|1' column in first "
            f"{_MAX_HEADER_SCAN_ROWS} rows) — file is not in the expected standard-charges layout"
        )

    header = [str(c).strip() if c is not None else "" for c in all_rows[header_idx]]
    code_col_indices = find_tracked_code_column_indices(header)
    dict_rows = []
    for row in all_rows[header_idx + 1 :]:
        if row_matches_tracked_code(row, code_col_indices):
            dict_rows.append({header[i]: row[i] for i in range(len(header)) if i < len(row)})

    return parse_tall_rows(dict_rows, hospital_id, source_file), raw_text
