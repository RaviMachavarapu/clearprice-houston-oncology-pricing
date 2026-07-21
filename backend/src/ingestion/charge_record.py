from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PayerRate:
    payer_name: str
    plan_name: str
    billing_setting: str
    rate: float
    verification_checks: list = field(default_factory=list)
    verified: bool = False


@dataclass
class ChargeRecord:
    hospital_id: str
    drug_code: str
    gross_charge_min: float | None
    gross_charge_max: float | None
    source_file: str
    retrieved_at: str
    payer_rates: list[PayerRate] = field(default_factory=list)
