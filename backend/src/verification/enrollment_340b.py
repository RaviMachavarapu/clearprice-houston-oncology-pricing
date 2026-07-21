from __future__ import annotations

import json
import re
import difflib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from functools import lru_cache

_CE_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[2]
    / "src" / "reference_data" / "340b_covered_entities" / "OPA_CE_DAILY_PUBLIC.JSON"
)
_SNAPSHOT_SOURCE = (
    "HRSA 340B OPAIS Covered Entity Daily Export (JSON), "
    "downloaded 2026-07-17 from https://340bopais.hrsa.gov/Reports"
)

_MATCH_THRESHOLD = 0.90

_STOPWORDS = re.compile(
    r"\b(hospital|medical center|medical cnter|medical cntr|health system|"
    r"healthcare|clinic|inc|llc|system|of texas|the|campus|st\.|saint)\b",
    re.IGNORECASE,
)


def _normalize(name: str) -> str:
    n = _STOPWORDS.sub(" ", name.lower())
    n = re.sub(r"[^a-z0-9]+", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def _char_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def _token_overlap(a: str, b: str) -> float:
    """Overlap coefficient (|intersection| / smaller set size). Correctly
    scores a short name that is a strict subset of a longer legal name (e.g.
    our "Ben Taub Hospital" vs HRSA's "Harris Health System Ben Taub
    Hospital") as a strong match. Only sound for site-level `subName`
    records — a parent `name` record like "MEMORIAL HERMANN HOSPITAL SYSTEM"
    reduces, after stopword-stripping, to just the brand words ("memorial
    hermann"), which would trivially subset-match every sibling facility
    under that brand, so this is deliberately NOT used against the `name`
    field (see `_token_similarity`).
    """
    ta, tb = set(a.split()), set(b.split())
    if len(ta) < 2 or len(tb) < 2:
        # A single-token overlap (e.g. "Northwest") is not meaningful signal
        # on its own — refuse to award a high score off one shared word.
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def _token_jaccard(a: str, b: str) -> float:
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _token_similarity(a: str, b: str, field: str) -> float:
    """Word-token matching — a genuinely different method from the
    character-level SequenceMatcher, so the two verification passes aren't
    just the same algorithm run twice. Uses overlap coefficient for
    site-level `subName` matches (tolerates a dropped org-level prefix) and
    plain Jaccard for parent `name` matches (avoids the brand-word subset
    trap described in `_token_overlap`).
    """
    return _token_overlap(a, b) if field == "subName" else _token_jaccard(a, b)


@lru_cache(maxsize=1)
def _load_tx_entities() -> list[dict]:
    with open(_CE_SNAPSHOT_PATH, encoding="utf-8-sig") as f:
        data = json.load(f)
    return [c for c in data["coveredEntities"] if c.get("streetAddress", {}).get("state") == "TX"]


def _best_match(query: str, method: str) -> tuple[float, dict, str, str] | None:
    q_norm = _normalize(query)
    best = None
    best_score = 0.0
    for c in _load_tx_entities():
        for field in ("subName", "name"):
            label = c.get(field)
            if not label:
                continue
            label_norm = _normalize(label)
            score = (
                _char_similarity(q_norm, label_norm)
                if method == "char_similarity"
                else _token_similarity(q_norm, label_norm, field)
            )
            if score > best_score:
                best_score = score
                best = (score, c, field, label)
    return best


@dataclass
class EnrollmentCheck:
    result: str  # "enrolled" | "not_enrolled" | "no_match"
    source: str
    checked_at: str
    method: str | None = None
    matched_entity_name: str | None = None
    medicare_provider_number: str | None = None
    match_score: float | None = None


def _query_local_snapshot(hospital_name: str, method: str) -> EnrollmentCheck:
    """One independent match pass against the real, locally-stored HRSA OPAIS
    covered-entity export. Only reports "enrolled"/"not_enrolled" when a
    confident (>= _MATCH_THRESHOLD) match is found — those are positive
    claims backed by an actual matched HRSA record and its `participating`
    flag. Below the threshold we cannot confidently identify this hospital in
    the registry at all, so the honest result is "no_match" — NOT
    "not_enrolled", since that would assert a fact (absence) we have no
    evidence for (Constitution Principle II/III: never present an inferred
    absence as a sourced fact).
    """
    now = datetime.now(timezone.utc).isoformat()
    match = _best_match(hospital_name, method)
    if match is None or match[0] < _MATCH_THRESHOLD:
        score = match[0] if match else 0.0
        label = match[3] if match else None
        return EnrollmentCheck(
            result="no_match",
            source=_SNAPSHOT_SOURCE,
            checked_at=now,
            method=method,
            matched_entity_name=label,
            match_score=round(score, 3),
        )

    score, entity, _field, label = match
    ccn = entity.get("medicareProviderNumber")
    # Multiple registrations can share one CCN with differing `participating`
    # flags (e.g. an inactive DSH registration alongside an active RRC one for
    # the same facility) — treat the facility as enrolled if ANY registration
    # under this CCN is currently participating.
    same_ccn = [c for c in _load_tx_entities() if c.get("medicareProviderNumber") == ccn] if ccn else [entity]
    participating = any(str(c.get("participating")).upper() == "TRUE" for c in same_ccn)

    return EnrollmentCheck(
        result="enrolled" if participating else "not_enrolled",
        source=_SNAPSHOT_SOURCE,
        checked_at=now,
        method=method,
        matched_entity_name=label,
        medicare_provider_number=ccn,
        match_score=round(score, 3),
    )


def verify_340b_enrollment(hospital_name: str) -> tuple[str, list[EnrollmentCheck]]:
    """Two independent match passes over the real HRSA OPAIS covered-entity
    snapshot — one using character-level similarity, one using word-token
    overlap — so agreement between them is a genuine cross-check rather than
    the same algorithm run twice. Both must agree to resolve
    enrolled/not_enrolled; disagreement forces `unverified` (Constitution
    Principle II — never guessed or averaged).
    """
    checks: list[EnrollmentCheck] = [
        _query_local_snapshot(hospital_name, "char_similarity"),
        _query_local_snapshot(hospital_name, "token_overlap"),
    ]

    results = [c.result for c in checks]
    if "no_match" in results or results[0] != results[1]:
        status = "unverified"
    else:
        status = results[0]
    return status, checks
