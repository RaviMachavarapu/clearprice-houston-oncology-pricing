# API Contracts: Houston Oncology Drug Pricing Intelligence

FastAPI JSON backend, read-only over the `houston_hospitals/` Docker volume.
No auth (single-user local tool, per spec Clarifications).

## GET /api/drugs

Returns the 33 tracked drugs for the checkbox UI.

**Response** `200`:
```json
{
  "drugs": [
    {
      "code": "string",
      "name": "string",
      "category": "string"
    }
  ]
}
```

## GET /api/hospitals

Returns all 44 locked hospitals with ingestion status (for surfacing
`ingestion failed: <reason>` per FR-003 / Principle V).

**Response** `200`:
```json
{
  "hospitals": [
    {
      "id": "string",
      "name": "string",
      "ingestion_status": "success | failed: <reason> | not_ingested",
      "last_ingested_at": "ISO8601 datetime | null",
      "enrollment_340b": "enrolled | not_enrolled | unverified",
      "enrollment_340b_checks": [
        {"result": "enrolled | not_enrolled | error", "source": "string", "checked_at": "ISO8601"}
      ]
    }
  ]
}
```

## GET /api/breakdowns?drugs={code1,code2,...}

Core query: given one or more selected drug codes, returns the Section-4-style
Pricing Breakdown (see `data-model.md`) for every hospital that both (a) was
successfully ingested and (b) publishes that drug in its own MRF (per FR-002).
Hospitals with `ingestion_status: failed` are returned separately as
unavailable status entries (per FR-003), not silently omitted.

**Query params**:
- `drugs` (required): comma-separated drug codes

**Response** `200`:
```json
{
  "breakdowns": [
    {
      "drug_code": "string",
      "hospital_id": "string",
      "hospital_name": "string",
      "gross_charge": {"min": 0, "max": 0, "source": {"source": "string", "access_date": "ISO8601"}},
      "asp": {"value": 0, "source": {"source": "string", "access_date": "date"}},
      "asp_plus6_line": {"value": 0, "formula": "ASP + 6%", "source": {"source": "string", "access_date": "date"}},
      "asp_minus27_line": {"value": 0, "formula": "ASP - 27% (industry-standard 340B estimate)", "source": {"source": "string", "access_date": "date"}},
      "wac": {"value": 0, "source": {"source": "string", "access_date": "date"}},
      "_comment_not_available_form": "gross_charge/asp/wac render as {\"available\": false, \"reason\": \"not publicly available\"} instead of the shape above when that benchmark isn't published anywhere (per spec Edge Cases); asp_plus6_line renders the same {available:false} marker (still present as a key) whenever asp is unavailable; asp_minus27_line is the only field actually omitted from the response entirely, and only when the hospital is not 340B-enrolled",
      "dose": {"reference_dose": {"value": 0, "unit": "mg | mg/kg | mg/m2", "regimen_cited": "string", "formula": "string", "source": {"source": "string", "access_date": "date"}}},
      "payer_rates": [
        {"payer_name": "string", "plan_name": "string", "billing_setting": "string", "rate": 0, "verified": true, "markup_ratio": {"value": 0, "formula": "string", "source": {"source": "string", "access_date": "ISO8601"}}, "markup_ratio_flag": false}
      ],
      "unverified_exclusions": [
        {"payer_name": "string", "plan_name": "string", "reason": "string", "verification_checks": [true, false]}
      ],
      "cgt_risk_flag": {"value": true, "formula": "string", "source": {"source": "string", "access_date": "date"}},
      "margin_verdict": {
        "medicare_vs_wac": {"profit": 0, "formula": "string", "source": {"source": "string", "access_date": "date"}},
        "_comment": "medicare_vs_wac is always present (or {available:false,reason} if asp/wac missing) regardless of 340B enrollment. medicare_buy_and_bill/highest_commercial/lowest_medicare_managed are present only when the hospital is 340B-enrolled (asp_minus27_line present)",
        "medicare_buy_and_bill": {"profit": 0, "formula": "string", "source": {"source": "string", "access_date": "date"}},
        "highest_commercial": {"rate": 0, "profit": 0, "formula": "string", "source": {"source": "string", "access_date": "date"}, "payer_name": "string", "plan_name": "string"},
        "lowest_medicare_managed": {"rate": 0, "profit": 0, "formula": "string", "source": {"source": "string", "access_date": "date"}, "payer_name": "string", "plan_name": "string"}
      },
      "per_dose": {
        "_comment": "present only when dose.reference_dose.value is available; mirrors hospital_charge_range/asp/wac/asp_plus6_line/asp_minus27_line/margin_verdict/medicare_coinsurance_split scaled to the reference dose, each with its own formula+source",
        "hospital_charge_range": {},
        "asp": {},
        "wac": {},
        "asp_plus6_line": {},
        "asp_minus27_line": {},
        "margin_verdict": {}
      }
    }
  ],
  "unavailable_hospitals": [
    {"hospital_id": "string", "name": "string", "ingestion_status": "string", "last_ingested_at": "ISO8601 | null"}
  ]
}
```

Note: `payer_rates` includes every payer/plan row, verified or not (each
carries `verified`); the frontend renders only the verified subset in the
visible payer table and lists unverified rows separately via
`unverified_exclusions`, per Constitution Principle II.

**Errors**:
- `400` — no `drugs` param, or a code not in the 33-drug set
- Every breakdown entry is guaranteed (by the Principle VI contract-test
  layer, run at request time) to have every field populated with a source
  citation and, for calculated fields, a formula string — a breakdown that
  would be missing one is never returned; the corresponding hospital/drug
  pair is instead surfaced as `unavailable` with the specific reason
  (e.g., `"payer scheme unverified"`, `"340B enrollment unverified"` does not
  block the whole breakdown, only that one payer row or the 340B line).

## POST /api/hospitals/{id}/refresh (manual re-ingestion trigger)

Per spec Clarifications (manual-refresh-only, no automatic background
refresh): re-runs ingestion for a single hospital on demand.

**Response** `200`:
```json
{
  "id": "string",
  "name": "string",
  "ingestion_status": "success | failed: <reason>",
  "last_ingested_at": "ISO8601 datetime | null"
}
```

**Errors**:
- `404` — unknown `hospital_id`
