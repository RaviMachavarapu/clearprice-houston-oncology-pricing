from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Citation:
    """A source reference for a single value: file name or URL + when it was read.

    Per data-model.md — every non-calculated value must carry one of these,
    never a bare number.
    """

    source: str
    access_date: str  # ISO date string; retrieved_at for MRF-derived values

    def to_dict(self) -> dict:
        return {"source": self.source, "access_date": self.access_date}


@dataclass(frozen=True)
class NotAvailable:
    """Explicit not-available marker for a benchmark that genuinely isn't published.

    Per Constitution Principle I: a missing number is shown as missing, never
    interpolated or left as a bare null with no explanation.
    """

    reason: str = "not publicly available"
    available: bool = False

    def to_dict(self) -> dict:
        return {"available": False, "reason": self.reason}


SourceRef = Citation | NotAvailable


def is_valid_source(value: Optional[SourceRef]) -> bool:
    """Principle VI gate: a source field must be a real Citation or an explicit NotAvailable — never bare None."""
    return isinstance(value, (Citation, NotAvailable))
