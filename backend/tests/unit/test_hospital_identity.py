from __future__ import annotations

import pytest

from src.verification.hospital_identity import check_hospital_identity


def test_matching_name_does_not_raise():
    check_hospital_identity("Baylor St. Lukes Medical Center Houston", "Baylor St. Luke's Medical Center - Houston")


def test_missing_mrf_hospital_name_is_not_grounds_for_rejection():
    check_hospital_identity(None, "Baylor St. Luke's Medical Center - Houston")


def test_mismatched_name_raises():
    with pytest.raises(ValueError, match="mismatch"):
        check_hospital_identity("Arizona General Hospital - Laveen", "Baylor St. Luke's Medical Center - Houston")
