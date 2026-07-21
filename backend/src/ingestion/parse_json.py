from __future__ import annotations

from datetime import datetime, timezone

from src.ingestion.charge_record import ChargeRecord, PayerRate
from src.ingestion.tracked_codes import load_tracked_codes

_TRACKED_CODES = load_tracked_codes()


def _matches_tracked_code(code_information: list[dict]) -> str | None:
    for entry in code_information or []:
        code = entry.get("code")
        if code in _TRACKED_CODES:
            return code
    return None


def parse_json_mrf(data: dict, hospital_id: str, source_file: str) -> list[ChargeRecord]:
    """Parse a hospital's CMS-standard-charges-format JSON MRF into Charge Records,
    filtered to the 33 tracked oncology drug codes (plan.md Technical Context).

    Only quotes what the hospital's own file states — no computed or inferred values
    (Constitution Principle III).
    """
    retrieved_at = datetime.now(timezone.utc).date().isoformat()
    items = data.get("standard_charge_information", [])
    records: list[ChargeRecord] = []

    for item in items:
        code = _matches_tracked_code(item.get("code_information", []))
        if code is None:
            continue

        gross_min = None
        gross_max = None
        payer_rates: list[PayerRate] = []

        for charge in item.get("standard_charges", []):
            setting = charge.get("setting", "unknown")
            if charge.get("gross_charge") is not None:
                value = charge["gross_charge"]
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
                        rate=rate,
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
