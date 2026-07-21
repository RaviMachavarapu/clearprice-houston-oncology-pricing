import pytest

from src.verification.provenance_gate import ProvenanceError, assert_calculated_field_provenance


def test_accepts_field_with_formula_and_source():
    field = {"value": 106.0, "formula": "ASP * 1.06", "source": {"source": "cms.gov", "access_date": "2026-07-16"}}
    assert_calculated_field_provenance(field, "asp_plus6_line")


def test_rejects_field_missing_formula():
    field = {"value": 106.0, "source": {"source": "cms.gov", "access_date": "2026-07-16"}}
    with pytest.raises(ProvenanceError):
        assert_calculated_field_provenance(field, "asp_plus6_line")


def test_rejects_field_missing_source():
    field = {"value": 106.0, "formula": "ASP * 1.06"}
    with pytest.raises(ProvenanceError):
        assert_calculated_field_provenance(field, "asp_plus6_line")


def test_accepts_explicit_not_available_marker():
    field = {"available": False, "reason": "ASP not publicly available"}
    assert_calculated_field_provenance(field, "asp_plus6_line")


def test_rejects_not_available_marker_missing_reason():
    field = {"available": False}
    with pytest.raises(ProvenanceError):
        assert_calculated_field_provenance(field, "asp_plus6_line")
