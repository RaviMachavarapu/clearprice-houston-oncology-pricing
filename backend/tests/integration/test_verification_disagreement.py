from __future__ import annotations

import itertools

from src.verification import enrollment_340b


def test_340b_enrollment_unverified_when_two_independent_checks_disagree(monkeypatch):
    # T040: simulate the two independent HRSA OPAIS double-check passes
    # disagreeing with each other. Constitution Principle II forbids guessing
    # or averaging in this case — the result must be the explicit "unverified"
    # status, never "enrolled" or "not_enrolled".
    results = itertools.cycle(["enrolled", "not_enrolled"])
    monkeypatch.setattr(enrollment_340b, "_query_hrsa_opais", lambda name: next(results))

    status, checks = enrollment_340b.verify_340b_enrollment("Some Houston Hospital")

    assert status == "unverified"
    assert len(checks) == 2
    assert {c.result for c in checks} == {"enrolled", "not_enrolled"}


def test_340b_enrollment_agrees_when_both_checks_match(monkeypatch):
    monkeypatch.setattr(enrollment_340b, "_query_hrsa_opais", lambda name: "enrolled")

    status, checks = enrollment_340b.verify_340b_enrollment("Some Houston Hospital")

    assert status == "enrolled"
    assert all(c.result == "enrolled" for c in checks)


def test_340b_enrollment_unverified_when_either_check_errors(monkeypatch):
    results = itertools.cycle(["enrolled", "error"])
    monkeypatch.setattr(enrollment_340b, "_query_hrsa_opais", lambda name: next(results))

    status, _checks = enrollment_340b.verify_340b_enrollment("Some Houston Hospital")

    assert status == "unverified"
