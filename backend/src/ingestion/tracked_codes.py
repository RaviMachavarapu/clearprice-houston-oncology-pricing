from __future__ import annotations

import csv
from pathlib import Path

_DRUGS_TSV = Path(__file__).parent.parent / "reference_data" / "drugs_list.tsv"


def load_tracked_codes() -> set[str]:
    """The 33 HCPCS/Q codes this feature tracks — ingestion filters to only these (plan.md Technical Context)."""
    codes = set()
    with _DRUGS_TSV.open(encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if not row:
                continue
            code_field = row[0]
            # code_field looks like: [{'code': 'J9267', 'type': 'HCPCS'}]
            start = code_field.find("'code': '")
            if start == -1:
                continue
            start += len("'code': '")
            end = code_field.find("'", start)
            codes.add(code_field[start:end])
    return codes
