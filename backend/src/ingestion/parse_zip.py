from __future__ import annotations

import io
import json
import zipfile

from src.ingestion.charge_record import ChargeRecord
from src.ingestion.parse_csv import parse_csv_mrf
from src.ingestion.parse_json import parse_json_mrf


def parse_zip_mrf(raw_bytes: bytes, hospital_id: str, source_file: str) -> list[ChargeRecord]:
    """Unpack a hospital's zipped MRF and delegate to the JSON or CSV parser
    for whichever standard-charges file is inside (plan.md: parse_zip.py
    delegates to parse_json.py/parse_csv.py).
    """
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        inner_name = next(
            (n for n in archive.namelist() if n.lower().endswith((".json", ".csv"))),
            None,
        )
        if inner_name is None:
            raise ValueError(f"No .json or .csv standard-charges file found inside {source_file}")

        content = archive.read(inner_name)

        if inner_name.lower().endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            return parse_json_mrf(data, hospital_id, source_file=f"{source_file}!{inner_name}")

        return parse_csv_mrf(
            content.decode("utf-8"), hospital_id, source_file=f"{source_file}!{inner_name}"
        )
