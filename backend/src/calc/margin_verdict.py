from __future__ import annotations


def _classify(payer_rows: list[dict]) -> dict:
    verified = [row for row in payer_rows if row.get("verified")]
    commercial = [row for row in verified if "medicare" not in (row.get("plan_name") or "").lower()]
    medicare_managed = [row for row in verified if "medicare" in (row.get("plan_name") or "").lower()]
    return {"commercial": commercial, "medicare_managed": medicare_managed}


def margin_verdict(asp_plus6_line: dict, asp_minus27_line: dict, payer_rows: list[dict], unit: str = "mg") -> dict | None:
    """Three margin scenarios comparing the estimated 340B acquisition cost
    (asp_minus27_line) against: the standard Medicare Part B reimbursement,
    the hospital's own highest verified non-Medicare-plan (commercial) rate,
    and its own lowest verified Medicare-managed-plan rate. Only meaningful
    when a hospital is confirmed 340B-enrolled (asp_minus27_line present) —
    callers must gate on that before calling this.
    """
    if asp_plus6_line.get("available") is False or asp_minus27_line.get("available") is False:
        return None

    cost = asp_minus27_line["value"]
    cost_source = asp_minus27_line.get("source")
    buckets = _classify(payer_rows)

    def _scenario_from_rate(rate: float) -> dict:
        profit = round(rate - cost, 2)
        return {
            "rate": rate,
            "profit": profit,
            "formula": f"${rate}/{unit} - ${cost}/{unit} estimated 340B acquisition cost",
            "source": cost_source,
        }

    medicare_profit = round(asp_plus6_line["value"] - cost, 2)
    medicare_buy_and_bill = {
        "profit": medicare_profit,
        "formula": f"${asp_plus6_line['value']}/{unit} ASP+6% reimbursement - ${cost}/{unit} estimated 340B acquisition cost",
        "source": cost_source,
    }

    if buckets["commercial"]:
        top = max(buckets["commercial"], key=lambda row: row["rate"]["value"])
        highest_commercial = {
            **_scenario_from_rate(top["rate"]["value"]),
            "payer_name": top["payer_name"],
            "plan_name": top["plan_name"],
        }
    else:
        highest_commercial = {"available": False, "reason": "no verified non-Medicare-plan payer rows on file"}

    if buckets["medicare_managed"]:
        bottom = min(buckets["medicare_managed"], key=lambda row: row["rate"]["value"])
        lowest_medicare_managed = {
            **_scenario_from_rate(bottom["rate"]["value"]),
            "payer_name": bottom["payer_name"],
            "plan_name": bottom["plan_name"],
        }
    else:
        lowest_medicare_managed = {"available": False, "reason": "no verified Medicare-managed-plan payer rows on file"}

    return {
        "medicare_buy_and_bill": medicare_buy_and_bill,
        "highest_commercial": highest_commercial,
        "lowest_medicare_managed": lowest_medicare_managed,
    }


def wac_margin_scenario(asp_plus6_line: dict, wac_line: dict, unit: str = "mg") -> dict:
    """Medicare Part B reimbursement (ASP+6%) vs. this drug's WAC list
    acquisition cost. Unlike the three scenarios above, this does not depend
    on 340B enrollment (WAC is a public list price every hospital can be
    compared against) so it is always computed when ASP and WAC are both
    available. This is the comparison that actually surfaces real
    acquisition-cost losses (e.g. many cellular/gene therapies), since WAC —
    not the discounted 340B ceiling price — is what a non-340B hospital pays.
    """
    if asp_plus6_line.get("available") is False or wac_line.get("available") is False:
        return {"available": False, "reason": "ASP+6% reimbursement or WAC not publicly available for this drug"}

    rate = asp_plus6_line["value"]
    cost = wac_line["value"]
    profit = round(rate - cost, 2)
    return {
        "profit": profit,
        "formula": f"${rate}/{unit} ASP+6% reimbursement - ${cost}/{unit} WAC acquisition cost",
        "source": wac_line.get("source"),
    }
