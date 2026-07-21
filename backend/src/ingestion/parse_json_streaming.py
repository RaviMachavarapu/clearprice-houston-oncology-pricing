from __future__ import annotations

from datetime import datetime, timezone

import ijson

from src.ingestion.charge_record import ChargeRecord, PayerRate
from src.ingestion.tracked_codes import load_tracked_codes

_TRACKED_CODES = load_tracked_codes()


def _matches_tracked_code(code_information: list[dict]) -> str | None:
    for entry in code_information or []:
        code = entry.get("code")
        if code in _TRACKED_CODES:
            return code
    return None


_BOM = b"\xef\xbb\xbf"


def _open_skip_bom(file_path: str):
    f = open(file_path, "rb")
    if f.read(len(_BOM)) != _BOM:
        f.seek(0)
    return f


def stream_hospital_name(file_path: str) -> str | None:
    """Single lazy pass to read the file's own `hospital_name` field without
    buffering the whole (possibly multi-GB) JSON document in memory.
    """
    with _open_skip_bom(file_path) as f:
        for name in ijson.items(f, "hospital_name"):
            return name
    return None


def stream_json_mrf(file_path: str, hospital_id: str, source_file: str) -> list[ChargeRecord]:
    """Streaming equivalent of parse_json_mrf for MRF files too large to
    `json.loads` whole (some Houston hospital files run 1GB+). ijson parses
    the file incrementally so only the current `standard_charge_information`
    item is ever held in memory, and only items matching one of the 33
    tracked oncology drug codes are kept (plan.md Technical Context).

    Only quotes what the hospital's own file states — no computed or
    inferred values (Constitution Principle III).
    """
    retrieved_at = datetime.now(timezone.utc).date().isoformat()
    records: list[ChargeRecord] = []

    with _open_skip_bom(file_path) as f:
        for item in ijson.items(f, "standard_charge_information.item"):
            code = _matches_tracked_code(item.get("code_information", []))
            if code is None:
                continue

            gross_min = None
            gross_max = None
            payer_rates: list[PayerRate] = []

            for charge in item.get("standard_charges", []):
                setting = charge.get("setting", "unknown")
                if charge.get("gross_charge") is not None:
                    value = float(charge["gross_charge"])
                    gross_min = value if gross_min is None else min(gross_min, value)
                    gross_max = value if gross_max is None else max(gross_max, value)

                for payer_info in charge.get("payers_information", []):
                    rate = payer_info.get("standard_charge_dollar")
                    if rate is None:
                        continue
                    payer_rates.append(
                        PayerRate(
                            payer_name=payer_info.get("payer_name", "unknown"),
                            plan_name=payer_info.get("plan_name", "unknown"),
                            billing_setting=payer_info.get("billing_class", setting),
                            rate=float(rate),
                        )
                    )

            records.append(
                ChargeRecord(
                    hospital_id=hospital_id,
                    drug_code=code,
                    gross_charge_min=gross_min,
                    gross_charge_max=gross_max,
                    source_file=source_file,
                    retrieved_at=retrieved_at,
                    payer_rates=payer_rates,
                )
            )

    return records
