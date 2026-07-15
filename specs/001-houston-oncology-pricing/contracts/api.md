# API Contracts: Houston Oncology Drug Pricing Intelligence

FastAPI JSON backend, read-only over the `houston_hospitals/` Docker volume.
No auth (single-user local tool, per spec Clarifications).

## GET /api/drugs

Returns the 33 tracked drugs for the checkbox UI.

**Response** `200`:
```json
[
  {
    "code": "string",
    "name": "string",
    "category": "string"
  }
]
```

## GET /api/hospitals

Returns all 44 locked hospitals with ingestion status (for surfacing
`ingestion failed: <reason>` per FR-003 / Principle V).

**Response** `200`:
```json
[
  {
    "id": "string",
    "name": "string",
    "ingestion_status": "success | failed: <reason>",
    "last_ingested_at": "ISO8601 datetime | null"
  }
]
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
      "gross_charge_range": {"min": 0, "max": 0, "source_file": "string", "retrieved_at": "ISO8601"},
      "asp_line": {"value": 0, "source": "string", "access_date": "date"},
      "asp_plus6_line": {"value": 0, "formula": "ASP + 6%", "source": "string", "access_date": "date"},
      "asp_minus27_line": {"value": 0, "formula": "ASP - 27% (industry-standard 340B estimate)", "source": "string", "access_date": "date"},
      "wac_line": {"value": 0, "source": "string", "access_date": "date"},
      "_comment_not_available_form": "asp_line/wac_line render as {\"available\": false, \"reason\": \"not publicly available\"} instead of the shape above when that benchmark isn't published anywhere (per spec Edge Cases); asp_plus6_line/asp_minus27_line are omitted entirely (not zero) whenever asp_line is unavailable",
      "dose_line": {"value": 0, "unit": "mg | mg/kg | mg/m2", "regimen_cited": "string", "source": "string", "access_date": "date"},
      "payer_table": [
        {"payer_name": "string", "plan_name": "string", "billing_setting": "string", "rate": 0, "markup_ratio": 0, "markup_ratio_flag": false, "source_file": "string", "retrieved_at": "ISO8601"}
      ],
      "cgt_risk_flag": true
    }
  ],
  "unavailable_hospitals": [
    {"hospital_id": "string", "hospital_name": "string", "reason": "string"}
  ]
}
```

**Errors**:
- `400` — no `drugs` param, or a code not in the 33-drug set
- Every breakdown entry is guaranteed (by the Principle VI contract-test
  layer, run at request time) to have every field populated with a source
  citation and, for calculated fields, a formula string — a breakdown that
  would be missing one is never returned; the corresponding hospital/drug
  pair is instead surfaced as `unavailable` with the specific reason
  (e.g., `"payer scheme unverified"`, `"340B enrollment unverified"` does not
  block the whole breakdown, only that one payer row or the 340B line).

## GET /api/hospitals/{id}/refresh (manual re-ingestion trigger)

Per spec Clarifications (manual-refresh-only, no automatic background
refresh): re-runs ingestion for a single hospital on demand.

**Response** `202`: `{"hospital_id": "string", "status": "ingestion started"}`
