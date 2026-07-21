# Phase 1 Data Model: Houston Oncology Drug Pricing Intelligence

Entities derived from `spec.md` Key Entities section, expanded with the
provenance fields Constitution Principles IV/VI require on every record.

## Drug

One of the 33 tracked oncology drugs (source: `drugs_list.tsv` for
code/name/category, `oncology_top5_asp_reference.json` for ASP, plus
per-drug FDA label dose and WAC research — see T005a).

| Field | Type | Notes |
|---|---|---|
| `code` | string | HCPCS/Q-code, unique identifier |
| `name` | string | Generic drug name |
| `category` | enum | One of the 7 categories (Chemotherapy, Immunotherapy, Targeted Therapy, Hormone Therapy, Supportive Care, Antibody-Drug Conjugates, Cellular and Gene Therapy) |
| `dose_pattern` | enum | `fixed` \| `mg_per_kg` \| `mg_per_m2` |
| `dose_value` | number | Label-sourced dose rate (mg for fixed; mg/kg or mg/m² rate otherwise) |
| `dose_regimen_cited` | string | Exact regimen/indication cited, required when label has >1 approved option (Principle III) |
| `dose_source` | citation | FDA label link + access date |
| `asp_value` | number \| null | CMS ASP payment-limit figure; null if not publicly available |
| `asp_source` | citation \| `{available: false, reason}` | CMS ASP file name/link + effective quarter + access date, or an explicit not-available marker |
| `wac_value` | number \| null | True WAC/list benchmark only; null if not publicly available |
| `wac_source` | citation \| `{available: false, reason}` | Source link + access date, or an explicit not-available marker. A cash/self-pay price (e.g. SingleCare, GoodRx, Drugs.com Price Guide) is never a valid substitute for WAC anywhere in this app — a drug with no public WAC gets `{available: false}`, not a cash price |

**Validation rules**: `dose_source` is always a mandatory non-null citation
(dose is core to the feature, always sourced per Principle III). `asp_source`
and `wac_source` are each mandatory but MAY resolve to the explicit
`{available: false, reason: "not publicly available"}` marker instead of a
citation when that benchmark genuinely isn't published anywhere (per Edge
Cases) — a bare missing field with no marker is what Principle VI rejects,
not the presence of the not-available state. `dose_regimen_cited` mandatory
when the drug's label defines more than one approved regimen/indication
(Principle III).

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
| `gross_charge` | {min, max, source} \| {available: false, reason} | From Charge Record, with `source_file` + `retrieved_at` citation |
| `asp` | {value, source} \| {available: false, reason} | From Drug.asp_value/asp_source; renders "not publicly available" when not available |
| `asp_plus6_line` | {value, formula, source} \| {available: false, reason} | Renders the not-available marker (never zero/blank) when `asp` is not available, since the formula has nothing to compute from — the key is always present |
| `asp_minus27_line` | {value, formula, source} \| omitted | Present only if `Hospital.enrollment_340b == enrolled` AND `asp` is available; `formula = "ASP - 27% (industry-standard 340B estimate)"`, `source` = `340B_pricing_research.md` citation |
| `wac` | {value, source} \| {available: false, reason} | From Drug.wac_value/wac_source; renders "not publicly available" when not available |
| `dose` | {reference_dose: {value, unit, regimen_cited, formula, source}} | From Drug dose fields; explicitly labeled illustrative reference dose (70kg / 1.7m² reference), never a hospital-specific actual dose |
| `payer_rates` | array | Every payer/plan row from the Charge Record, each with `billing_setting`, `verified` (Principle II double-check result), `markup_ratio = rate / asp_value`, `markup_ratio_flag` (`formula = "markup_ratio > 3"`, boolean, per FR-005), and its own source citation. Unverified rows still appear here (each carries `verified: false`) but the frontend renders only the verified subset in the visible payer table, listing unverified rows separately via `unverified_exclusions` |
| `unverified_exclusions` | array | Payer/plan rows whose Principle II double-check disagreed, each with `payer_name`, `plan_name`, `reason`, `verification_checks` |
| `cgt_risk_flag` | boolean \| omitted | Present only for CGT-category drugs (Q2041/Q2042/Q2055/Q2054/Q2056), comparing against $269,139 / $314,231 DRG payment reference |
| `margin_verdict.medicare_vs_wac` | {profit, formula, source} \| {available: false, reason} | Always computed when `asp_plus6_line` and `wac` are both available, regardless of 340B enrollment — `profit = asp_plus6_line.value - wac.value`; the acquisition-cost comparison every hospital can be measured against, not just 340B-enrolled ones |
| `margin_verdict.medicare_buy_and_bill` | {profit, formula, source} | Present only when `asp_minus27_line` is present (340B-enrolled); `profit = asp_plus6_line.value - asp_minus27_line.value` |
| `margin_verdict.highest_commercial` | {rate, profit, formula, source, payer_name, plan_name} \| {available: false, reason} | Present only when `asp_minus27_line` is present; highest verified payer rate among rows whose `plan_name` does not contain "medicare" |
| `margin_verdict.lowest_medicare_managed` | {rate, profit, formula, source, payer_name, plan_name} \| {available: false, reason} | Present only when `asp_minus27_line` is present; lowest verified payer rate among rows whose `plan_name` contains "medicare" |
| `per_dose` | object \| omitted | Present only when `dose.reference_dose.value` is available; mirrors `hospital_charge_range`, `asp`, `wac`, `asp_plus6_line`, `asp_minus27_line` (when 340B-enrolled), and `margin_verdict` scaled from per-mg/per-unit to per-reference-dose using `dose.reference_dose.value`/`unit`, each carrying its own `formula` and `source` per Principle IV |

**Validation rules**: Every leaf value carries a citation object
(`{source, access_date}` minimum) and every calculated value carries its
`formula` string — enforced by the same Principle VI contract-test layer
before the breakdown is returned by the API (not just at ingestion time,
since breakdowns are computed on read). `margin_verdict.medicare_vs_wac` is
independent of 340B enrollment (Principle I — WAC is a public list price);
the other three `margin_verdict` scenarios and all of `per_dose` are gated on
`Hospital.enrollment_340b == enrolled` only where they depend on
`asp_minus27_line`.

## Canonical Payer Group (frontend, display-only)

Not part of the API response or the persisted data model — computed
client-side in `frontend/app.js` from the set of raw `payer_name` strings
present in a given API response's `payer_rates` rows, purely to drive the
payer checkbox list (both the per-hospital payer-table filter and the
payer-comparison page's global payer checklist) and is discarded on reload.

| Field | Type | Notes |
|---|---|---|
| raw payer name | string | As stored in the Charge Record, unmodified |
| canonical label | string | The most-frequent (tie-break: longest) raw spelling within a merged group; used as the checkbox label |

**Grouping rule**: two raw names merge into one canonical group only when
either (a) one name's token set is a subset of the other's and every
"leftover" token in the larger name is a generic descriptor (e.g. "health",
"network", "managed", "ppo") rather than a second brand/proper-noun word, or
(b) their whitespace-stripped compact forms share a prefix relationship with
the leftover suffix also restricted to that same generic-descriptor
whitelist. This asymmetric restriction exists specifically to prevent
transitive false merges through a compound/joint-venture name (e.g. "Aetna"
and "Kelsey" must never merge just because both independently match
"Aetna-Kelsey Care"). This grouping never changes a row's underlying
`payer_name`, `verified` status, or citation — it only changes which
checkbox a row's `verified` rate responds to.

## Citation (shared value object)

| Field | Type | Notes |
|---|---|---|
| `source` | string | File name (hospital MRF) or URL (FDA label, CMS ASP file, HRSA OPAIS, WAC/list doc) |
| `access_date` \| `retrieved_at` | date | When the source was read |

Used embedded in every other entity's provenance fields — never a bare
number without one.
