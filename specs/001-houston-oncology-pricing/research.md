# Phase 0 Research: Houston Oncology Drug Pricing Intelligence

No `NEEDS CLARIFICATION` markers remain in Technical Context — scope, drug set,
hospital set, and tech stack were locked during brainstorming (design doc) and
constitution. This file records decisions/rationale/alternatives for the
choices already made, per Phase 0 output format.

## 1. MRF ingestion approach

**Decision**: Per-hospital ingestion module, one parser per source format
(JSON, CSV, ZIP-of-CSV/JSON), each normalizing into one common internal
schema restricted to the 33 tracked HCPCS/Q-codes before write.

**Rationale**: The 44 hospitals' MRFs are not uniform (mixed formats,
some behind Azure Blob SAS-token URLs, some encoded oddly like Houston
Methodist's 68.7MB JSON). A single generic parser would either fail silently
on edge cases or require assumption-filling — both forbidden by Principle I.
Per-format parsers with explicit failure states satisfy Principle V
(`ingestion failed: <reason>` surfaced, not bypassed).

**Alternatives considered**: One universal parser with format auto-detection
— rejected, higher risk of silently mis-parsing an edge-case file and
producing an unverified number. Third-party MRF-parsing libraries — none
identified that guarantee the specific 33-code filtering and citation
requirements this project needs; would still need a custom normalization
layer on top, so no net simplification.

## 2. 340B enrollment verification

**Decision**: Query HRSA's public 340B OPAIS covered-entity search twice
(two independent requests/parses), per hospital, cache result with retrieval
date and source URL. Only proceed to include the ASP−27% line if both checks
agree the hospital is enrolled.

**Rationale**: Enrollment status is publicly queryable (no login required)
directly satisfying Principle I; the double-check satisfies Principle II.
Actual 340B ceiling prices per NDC are login-gated and confidential — out of
scope; the estimate uses the industry-standard ASP−27% approximation, cited
as an estimate (per `340B_pricing_research.md`), not a real ceiling price.

**Alternatives considered**: Skipping enrollment verification and always
showing both scenarios — rejected, directly violates Principle II and the
user's explicit instruction to check enrollment before including the 340B
line. Scraping HRSA once and trusting it — rejected, violates the "verify
twice" requirement.

## 3. Payer-scheme verification

**Decision**: For each hospital, after normalization, run a second
independent pass over that hospital's own raw MRF file to confirm each named
payer/plan scheme actually appears before it's included in output. Any
scheme present in only one of the two passes is marked `unverified` and
excluded.

**Rationale**: Directly implements Principle II for payer schemes; prevents
a scheme name leaking in from another hospital's data structure or a parsing
assumption.

**Alternatives considered**: Trusting the single normalization pass — rejected
per explicit user instruction and Principle II.

## 4. Dose-scale sourcing

**Decision**: Independent FDA-label lookup per each of the 33 drugs; classify
each as fixed-dose, mg/kg (apply disclosed 70kg reference weight), or mg/m²
(apply disclosed 1.7m² reference BSA); state the exact regimen/indication
cited when a label has more than one option; never reuse another drug's
pattern or figure.

**Rationale**: Directly satisfies Principle III (no cross-inference) and the
user's explicit correction against reusing Keytruda's 200mg fixed-dose scale
for other drugs. Illustrative-reference-dose framing matches the disclosure
style already used in Section 4 of `ClearPrice_Build_Methodology.html`, which
the user asked to mirror.

**Alternatives considered**: Using each hospital's actual patient population
average weight/BSA — rejected, not knowable/verifiable per hospital
(would be an assumption, violating Principle I). Omitting dose entirely for
non-fixed-dose drugs — rejected per user's explicit requirement that every
drug show a dose scale.

## 5. Provenance enforcement mechanism

**Decision**: Contract-test layer (pytest) that runs as part of ingestion and
calculation, rejecting any record lacking its required citation/formula field
before it's written to the Docker volume or served by the API.

**Rationale**: Directly implements Constitution Principle VI, added because
the fresh-eyes review found Principles I–IV were otherwise unenforced by any
mechanism.

**Alternatives considered**: Manual review checklist only — rejected, this is
exactly the gap Principle VI was created to close.

## 6. Frontend rendering strategy for combinatorial results

**Decision**: Incremental/grouped rendering — results grouped by hospital,
one Section-4-style breakdown block rendered per hospital per selected drug,
loaded/rendered progressively rather than all at once.

**Rationale**: Up to 1,452 possible drug/hospital combinations (33 × 44);
rendering all synchronously on every checkbox change would be slow and
overwhelming. Progressive rendering keeps the UI responsive while still
showing every hospital/drug combination the user asked for (per explicit
user requirement — not just one example hospital per drug).

**Alternatives considered**: Pagination with a fixed page size — rejected as
extra UI complexity not requested; incremental/grouped rendering achieves the
same responsiveness more simply for a single-user local tool.
