from __future__ import annotations

from src.ingestion.charge_record import ChargeRecord


def hospital_charge_range(record: ChargeRecord) -> dict:
    """Min/max verified payer rate per billing setting actually present in the
    hospital's ingested record (FR-004 style aggregation). Settings are taken
    from the data as-is — never assumed to be only outpatient/inpatient.
    """
    settings: dict[str, list[float]] = {}
    for payer_rate in record.payer_rates:
        if not payer_rate.verified:
            continue
        settings.setdefault(payer_rate.billing_setting, []).append(payer_rate.rate)

    result: dict[str, dict] = {}
    for setting, rates in settings.items():
        result[setting] = {
            "min": min(rates),
            "max": max(rates),
            "payer_count": len(rates),
            "formula": f"min/max across {len(rates)} verified {setting} payer_rates",
            "source": {"source": record.source_file, "access_date": record.retrieved_at},
        }

    if not result:
        return {"available": False, "reason": "no verified payer rates on file for this hospital/drug"}
    return result
