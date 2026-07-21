from __future__ import annotations

from src.reference_data.citation import Citation, NotAvailable, SourceRef
from src.reference_data.drugs import Drug

ASP_PLUS6_MULTIPLIER = 1.06
ASP_MINUS27_MULTIPLIER = 0.73  # ASP - 27%


def _field(value: float | None, formula: str, source: SourceRef) -> dict:
    if value is None or isinstance(source, NotAvailable):
        reason = source.reason if isinstance(source, NotAvailable) else "ASP not publicly available"
        return {"available": False, "reason": reason}
    return {"value": round(value, 2), "formula": formula, "source": source.to_dict()}


def asp_plus6_line(drug: Drug) -> dict:
    """Medicare Part B default reimbursement: ASP + 6%. Omitted (returns an
    explicit not-available marker) rather than computed against a null ASP,
    per the not-publicly-available edge case (Constitution Principle I).
    """
    if drug.asp_value is None:
        return _field(None, "", drug.asp_source)
    value = drug.asp_value * ASP_PLUS6_MULTIPLIER
    return _field(value, f"ASP (${drug.asp_value:.2f}) * 1.06", drug.asp_source)


def asp_minus27_line(drug: Drug) -> dict:
    """340B acquisition ceiling estimate: ASP - 27.5% (approximated here as
    -27%, i.e. x0.73), only meaningful for 340B-enrolled hospitals — the
    caller (breakdown.py) omits this line entirely unless enrolled.
    """
    if drug.asp_value is None:
        return _field(None, "", drug.asp_source)
    value = drug.asp_value * ASP_MINUS27_MULTIPLIER
    return _field(value, f"ASP (${drug.asp_value:.2f}) * 0.73 (ASP - 27%)", drug.asp_source)
