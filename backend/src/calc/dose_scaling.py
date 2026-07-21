from __future__ import annotations


def _scale_value_field(field: dict, dose_value: float, dose_unit: str) -> dict:
    if field.get("available") is False:
        return dict(field)
    scaled = round(field["value"] * dose_value, 2)
    return {
        "value": scaled,
        "formula": f"${field['value']}/{dose_unit} x {dose_value}{dose_unit} = ${scaled}/dose",
        "source": field.get("source") or {"source": field.get("formula", "calculated"), "access_date": None},
    }


def scale_to_dose(field: dict, dose_value: float, dose_unit: str) -> dict:
    """Produce the /dose-scaled sibling of a per-mg (or per-billing-unit) field.

    Passes not-available markers through unchanged. Handles both a flat
    value-field (asp, wac, asp_plus6_line, asp_minus27_line) and the
    per-billing-setting shape returned by charge_range.hospital_charge_range
    (each setting has its own min/max to scale independently).
    """
    if field.get("available") is False:
        return dict(field)

    if "value" in field:
        return _scale_value_field(field, dose_value, dose_unit)

    # charge_range shape: {setting: {"min":..., "max":..., ...}, ...}
    scaled: dict[str, dict] = {}
    for setting, bucket in field.items():
        if bucket.get("available") is False:
            scaled[setting] = dict(bucket)
            continue
        min_scaled = round(bucket["min"] * dose_value, 2)
        max_scaled = round(bucket["max"] * dose_value, 2)
        scaled[setting] = {
            "min": min_scaled,
            "max": max_scaled,
            "payer_count": bucket["payer_count"],
            "formula": (
                f"${bucket['min']}-${bucket['max']}/{dose_unit} x {dose_value}{dose_unit} "
                f"= ${min_scaled}-${max_scaled}/dose"
            ),
            "source": bucket["source"],
        }
    return scaled
