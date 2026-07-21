from __future__ import annotations

import difflib
import re

_MISMATCH_RATIO_THRESHOLD = 0.4


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def check_hospital_identity(mrf_hospital_name: str | None, claimed_hospital_name: str) -> None:
    """Guard against silently ingesting one hospital's MRF under another
    hospital's identity (e.g. a reference-data URL that resolves to a
    different facility's standard-charges file).

    Raises ValueError with a clear reason if the MRF's own declared
    hospital_name doesn't plausibly match the hospital we claimed to fetch.
    Skipped (no-op) when the MRF doesn't declare a hospital_name at all —
    absence of the field is not itself grounds to reject the file.
    """
    if not mrf_hospital_name:
        return

    ratio = difflib.SequenceMatcher(None, _norm(mrf_hospital_name), _norm(claimed_hospital_name)).ratio()
    if ratio < _MISMATCH_RATIO_THRESHOLD:
        raise ValueError(
            f"MRF hospital_name mismatch: file identifies as '{mrf_hospital_name}', "
            f"expected '{claimed_hospital_name}' (similarity {ratio:.2f})"
        )
