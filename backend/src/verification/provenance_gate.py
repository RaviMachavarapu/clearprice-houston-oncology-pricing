from __future__ import annotations

from src.ingestion.charge_record import ChargeRecord


class ProvenanceError(ValueError):
    pass


def assert_charge_record_provenance(record: ChargeRecord) -> None:
    """Constitution Principle VI gate for ingestion: every Charge Record must
    carry its own source_file and retrieved_at citation before it can be
    written to houston_hospitals/ (called by T011 before any write).
    """
    if not record.source_file:
        raise ProvenanceError(f"Charge Record {record.hospital_id}/{record.drug_code} missing source_file")
    if not record.retrieved_at:
        raise ProvenanceError(f"Charge Record {record.hospital_id}/{record.drug_code} missing retrieved_at")


def assert_calculated_field_provenance(field: dict, field_name: str) -> None:
    """Constitution Principle VI gate for the calc engine: a computed Pricing
    Breakdown field must carry both `formula` and `source`, or be an explicit
    `{available: False, reason}` not-available marker — never a bare value or
    a bare null (called by Phase 4's breakdown assembler before any response
    is returned).
    """
    if field.get("available") is False:
        if not field.get("reason"):
            raise ProvenanceError(f"{field_name} marked unavailable but missing reason")
        return
    if not field.get("formula"):
        raise ProvenanceError(f"{field_name} missing formula")
    if not field.get("source"):
        raise ProvenanceError(f"{field_name} missing source")


def assert_quoted_field_provenance(field: dict, field_name: str) -> None:
    """Constitution Principle VI gate for non-calculated (quoted) Pricing
    Breakdown fields such as gross_charge/asp/wac: must carry a `source`
    citation, or be an explicit `{available: False, reason}` not-available
    marker — never a bare value or a bare null.
    """
    if field.get("available") is False:
        if not field.get("reason"):
            raise ProvenanceError(f"{field_name} marked unavailable but missing reason")
        return
    if not field.get("source"):
        raise ProvenanceError(f"{field_name} missing source")


def assert_provenance(record) -> None:
    if isinstance(record, ChargeRecord):
        assert_charge_record_provenance(record)
        return
    raise TypeError(f"assert_provenance: unsupported record type {type(record)!r}")
