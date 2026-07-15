# Phase 1 Data Model: Houston Oncology Drug Pricing Intelligence

Entities derived from `spec.md` Key Entities section, expanded with the
provenance fields Constitution Principles IV/VI require on every record.

## Drug

One of the 33 tracked oncology drugs (source: `oncology_top5_by_category.json`
plus per-drug FDA label / CMS ASP / WAC research).

| Field | Type | Notes |
|---|---|---|
| `code` | string | HCPCS/Q-code, unique identifier |
| `name` | string | Generic drug name |
| `category` | enum | One of the 7 categories (Chemotherapy, Immunotherapy, Targeted Therapy, Hormone Therapy, Supportive Care, Antibody-Drug Conjugates, Cellular and Gene Therapy) |
| `dose_pattern` | enum | `fixed` \| `mg_per_kg` \| `mg_per_m2` |
| `dose_value` | number | Label-sourced dose rate (mg for fixed; mg/kg or mg/m² rate otherwise) |
| `dose_regimen_cited` | string | Exact regimen/indication cited, required when label has >1 approved option (Principle III) |
| `dose_source` | citation | FDA label link + access date |
| `asp_value` | number | CMS ASP payment-limit figure |
| `asp_source` | citation | CMS ASP file name/link + effective quarter + access date |
| `wac_value` | number | WAC/list benchmark |
| `wac_source` | citation | Source link + access date |

**Validation rules**: `dose_source`, `asp_source`, `wac_source` are
mandatory non-null citation objects (Principle VI rejects the record
otherwise). `dose_regimen_cited` mandatory when the drug's label defines more
than one approved regimen/indication (Principle III).

## Hospital

One of the 44 locked Houston-area hospitals (source: `houston_candidates_final.json`).

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable identifier (from source xlsx row) |
| `name` | string | Hospital name |
| `mrf_url` | string | MRF source link |
| `ingestion_status` | enum | `success` \| `failed: <reason>` |
| `last_ingested_at` | datetime | Timestamp of last successful ingestion (manual re-run only) |
| `enrollment_340b` | enum | `enrolled` \| `not_enrolled` \| `unverified` |
| `enrollment_340b_checks` | array[2] | Two independent check records: `{result, source (HRSA OPAIS URL), checked_at}` |

**Validation rules**: `enrollment_340b` = `enrolled` or `not_enrolled` only
when both entries in `enrollment_340b_checks` agree; disagreement forces
`unverified` (Principle II) and 340B calculation line is omitted for that
hospital regardless of drug.

## Charge Record

One hospital's published rate for one drug, plus its per-payer scheme rows.
Written only by ingestion, read-only afterward (Principle V).

| Field | Type | Notes |
|---|---|---|
| `hospital_id` | string | FK → Hospital |
| `drug_code` | string | FK → Drug |
| `gross_charge_min` | number | nullable |
| `gross_charge_max` | number | nullable |
| `source_file` | string | Original MRF file name |
| `retrieved_at` | datetime | Ingestion timestamp |
| `payer_rates` | array | Each: `{payer_name, plan_name, billing_setting, rate, verification_checks: [check1, check2], verified}` |

**Validation rules**: A `payer_rates` entry's `verified` is true only if both
`verification_checks` entries independently confirm the scheme's presence in
that hospital's own raw MRF file; otherwise `verified: false` and the entry
is excluded from any rendered calculation (Principle II). No `payer_rates`
entry may be copied from another hospital's Charge Record (Principle III).
`billing_setting` (e.g. inpatient/outpatient, professional/institutional) is
read directly from the hospital's own MRF row alongside `rate` — a quoted
field, not calculated, so it only needs the same `source_file`/`retrieved_at`
citation as `rate`, no formula. A hospital/drug combination with no Charge
Record at all means "not published" (FR-002) — not the same as
`ingestion_status: failed`.

## Pricing Breakdown

The Section-4-style computed output for one (drug, hospital) pair — never
persisted independently; always derived at request time from Drug, Hospital,
and Charge Record so it can never drift from its sources (Principle V).

| Field | Type | Notes |
|---|---|---|
| `drug_code` / `hospital_id` | string | Identify the pair |
| `gross_charge_range` | {min, max} | From Charge Record, with `source_file` + `retrieved_at` citation |
| `asp_line` | {value, source} | From Drug.asp_value/asp_source |
| `asp_plus6_line` | {value, formula, source} | `formula = "ASP + 6%"`, `source` = same as `asp_source` |
| `asp_minus27_line` | {value, formula, source} \| omitted | Present only if `Hospital.enrollment_340b == enrolled`; `formula = "ASP - 27% (industry-standard 340B estimate)"`, `source` = `340B_pricing_research.md` citation |
| `wac_line` | {value, source} | From Drug.wac_value/wac_source |
| `dose_line` | {value, unit, regimen_cited, source} | From Drug dose fields; explicitly labeled illustrative reference dose (70kg / 1.7m² reference), never a hospital-specific actual dose |
| `payer_table` | array | Verified `payer_rates` entries only, each with `billing_setting`, `markup_ratio = rate / asp_value`, `markup_ratio_flag` (`formula = "markup_ratio > 3"`, boolean, per FR-005), and its own source citation |
| `cgt_risk_flag` | boolean \| omitted | Present only for CGT-category drugs (Q2041/Q2042/Q2055/Q2054/Q2056), comparing against $269,139 / $314,231 DRG payment reference |

**Validation rules**: Every leaf value carries a citation object
(`{source, access_date}` minimum) and every calculated value carries its
`formula` string — enforced by the same Principle VI contract-test layer
before the breakdown is returned by the API (not just at ingestion time,
since breakdowns are computed on read).

## Citation (shared value object)

| Field | Type | Notes |
|---|---|---|
| `source` | string | File name (hospital MRF) or URL (FDA label, CMS ASP file, HRSA OPAIS, WAC/list doc) |
| `access_date` \| `retrieved_at` | date | When the source was read |

Used embedded in every other entity's provenance fields — never a bare
number without one.
