import pytest

from src.ingestion.charge_record import ChargeRecord
from src.verification.provenance_gate import ProvenanceError, assert_provenance


def _record(**overrides) -> ChargeRecord:
    defaults = dict(
        hospital_id="test-hospital",
        drug_code="J9267",
        gross_charge_min=100.0,
        gross_charge_max=200.0,
        source_file="https://example.com/mrf.json",
        retrieved_at="2026-07-16",
    )
    defaults.update(overrides)
    return ChargeRecord(**defaults)


def test_accepts_record_with_source_file_and_retrieved_at():
    assert_provenance(_record())


def test_rejects_record_missing_source_file():
    with pytest.raises(ProvenanceError):
        assert_provenance(_record(source_file=""))


def test_rejects_record_missing_retrieved_at():
    with pytest.raises(ProvenanceError):
        assert_provenance(_record(retrieved_at=""))
