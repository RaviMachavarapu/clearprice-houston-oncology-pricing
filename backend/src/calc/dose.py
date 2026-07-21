from __future__ import annotations

from src.reference_data.drugs import Drug

_REFERENCE_WEIGHT_KG = 70.0
_REFERENCE_BSA_M2 = 1.7


def dose_line(drug: Drug) -> dict:
    """Assemble the reference-patient dose line for a drug (FR-006):

    - fixed: dose_value as-is (includes CGT single-infusion cell doses)
    - mg_per_kg: dose_value * 70kg reference weight
    - mg_per_m2: dose_value * 1.7m^2 reference BSA

    Always carries dose_regimen_cited and the FDA-label dose_source citation.
    """
    if drug.dose_pattern == "fixed":
        total_dose = drug.dose_value
        formula = f"fixed dose: {drug.dose_value}"
    elif drug.dose_pattern == "mg_per_kg":
        total_dose = drug.dose_value * _REFERENCE_WEIGHT_KG
        formula = f"{drug.dose_value} mg/kg * {_REFERENCE_WEIGHT_KG}kg reference weight"
    elif drug.dose_pattern == "mg_per_m2":
        total_dose = drug.dose_value * _REFERENCE_BSA_M2
        formula = f"{drug.dose_value} mg/m^2 * {_REFERENCE_BSA_M2}m^2 reference BSA"
    else:
        raise ValueError(f"Unknown dose_pattern: {drug.dose_pattern}")

    unit = "dose" if drug.category == "Cellular and Gene Therapy" else "mg"

    return {
        "dose_pattern": drug.dose_pattern,
        "reference_dose": {
            "value": round(total_dose, 4),
            "unit": unit,
            "formula": formula,
            "source": drug.dose_source.to_dict(),
        },
        "dose_regimen_cited": drug.dose_regimen_cited,
    }
