from __future__ import annotations

import csv
import io

from src.ingestion.charge_record import ChargeRecord
from src.ingestion.tall_format import parse_tall_rows


def parse_csv_mrf(raw_text: str, hospital_id: str, source_file: str) -> list[ChargeRecord]:
    """Parse a hospital's CMS-standard-charges-format CSV MRF into Charge Records,
    filtered to the 33 tracked oncology drug codes (plan.md Technical Context).
    """
    reader = csv.DictReader(io.StringIO(raw_text))
    return parse_tall_rows(reader, hospital_id, source_file)
