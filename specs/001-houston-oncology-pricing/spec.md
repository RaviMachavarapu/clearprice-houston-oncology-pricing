# Feature Specification: Houston Oncology Drug Pricing Intelligence

**Feature Branch**: `001-houston-oncology-pricing`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Build an application from hospital MRF (machine-readable file)
price transparency data, scoped to Houston-area hospitals, that lets a user pick
one or more of 33 oncology drugs by checkbox and see, per hospital that publishes
that drug, a full pricing/reimbursement breakdown (matching the worked example
in ClearPrice_Build_Methodology.html §4) — hospital charge, Medicare ASP
benchmark, WAC benchmark, 340B acquisition estimate where applicable, and
payer-by-payer rates — with every number sourced and cited, no assumed or
hallucinated figures, and 340B enrollment plus payer-scheme presence verified
twice per hospital before being used in any calculation." Full detail already
worked out and approved in
`docs/superpowers/specs/2026-07-15-clearprice-houston-oncology-pricing-design.md`.

## Clarifications

### Session 2026-07-15

- Q: Is this a single-user local tool or does it need login/access control for multiple people? → A: Single-user, no login — runs locally for the user's own research/analysis use.
- Q: How often should ingested hospital MRF data and 340B enrollment status be refreshed once the app is running? → A: Manual re-run only — data refreshes only when the user deliberately re-runs ingestion; no automatic background schedule.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select drugs, see which Houston hospitals publish them (Priority: P1)

A user (e.g. a hospital finance analyst, a patient advocate, or a researcher)
checks one or more of the 33 oncology drugs from a categorized list. The app
shows, for each selected drug, which Houston-area hospitals actually publish a
charge for that drug in their own price-transparency file — and, separately,
which hospitals don't (rather than silently omitting them).

**Why this priority**: This is the entry point to every other capability in the
app. Without it there is no way to reach the pricing breakdown at all.

**Independent Test**: Can be fully tested by checking a single drug and
confirming the resulting hospital list matches exactly what that drug's own
ingested hospital data contains — no more, no fewer.

**Acceptance Scenarios**:

1. **Given** the drug checklist is showing all 33 drugs grouped by category,
   **When** the user checks one drug, **Then** the app shows only the hospitals
   that publish a charge for that specific drug.
2. **Given** a hospital's data could not be ingested (broken link, unparseable
   file), **When** that hospital is relevant to a selected drug, **Then** the
   hospital still appears in the list marked as unavailable, not silently
   dropped.
3. **Given** the user checks multiple drugs at once, **When** results are
   shown, **Then** hospitals are grouped so it's clear which hospitals publish
   which of the selected drugs.

---

### User Story 2 - View the full pricing/reimbursement breakdown for a drug at a hospital (Priority: P1)

For any selected drug at any hospital that publishes it, the user opens a
detailed breakdown: the hospital's own charge range, the Medicare ASP payment
benchmark, the calculated Medicare reimbursement (ASP+6%), the WAC/list
benchmark, the 340B acquisition-cost estimate and spread (only if that hospital
is verified 340B-enrolled), the markup ratio, and every payer/plan rate that
specific hospital actually publishes for that drug — each figure shown with an
adult-dose scale-up sourced to that drug's own FDA label, and a citation next
to every number.

**Why this priority**: This is the core deliverable the user asked for — the
actual pricing intelligence, not just a list of hospitals.

**Independent Test**: Can be fully tested by opening one drug/hospital
breakdown and confirming every displayed number has a visible source citation
or, for calculated values, a visible formula — with no figure appearing that
isn't traceable to a cited source.

**Acceptance Scenarios**:

1. **Given** a hospital verified as 340B-enrolled, **When** its breakdown for a
   selected drug is shown, **Then** the 340B acquisition-cost line and spread
   appear, labeled as an industry-average estimate rather than the hospital's
   actual confidential ceiling price.
2. **Given** a hospital not verified as 340B-enrolled (or unverified), **When**
   its breakdown is shown, **Then** the 340B line does not appear at all.
3. **Given** a drug whose standard adult dosing is weight- or
   body-surface-area-based rather than fixed, **When** its dose-scaled "/dose"
   figure is shown, **Then** it is explicitly labeled as an illustrative
   reference calculation, not the hospital's actual patient dose.
4. **Given** the user selects N drugs, **When** results render, **Then** every
   hospital that publishes each selected drug gets its own full breakdown for
   that drug (not one example hospital standing in for all).

---

### User Story 3 - Trust that a shown number reflects real, verified data (Priority: P2)

The user can see, for any given hospital, whether its 340B enrollment status
and its published payer schemes were independently double-checked, and can
distinguish a confirmed figure from one marked unverified or unavailable.

**Why this priority**: Directly serves the user's explicit requirement that no
number be an assumption — this is the trust layer that makes Stories 1 and 2
credible rather than just plausible-looking.

**Independent Test**: Can be tested by finding a hospital/payer-scheme
combination that the two independent verification checks disagree on, and
confirming it renders as unverified/excluded rather than being silently
included with a guessed value.

**Acceptance Scenarios**:

1. **Given** a hospital's 340B status was checked twice and both checks agree,
   **When** its breakdown renders, **Then** the 340B-dependent line reflects
   that agreed status.
2. **Given** the two checks disagree, **When** the breakdown renders, **Then**
   the 340B line is omitted and marked unverified rather than guessed.
3. **Given** a named payer/plan scheme (e.g. a specific Aetna or BCBS plan) is
   not present in a hospital's own published file, **When** that hospital's
   payer table renders, **Then** that scheme does not appear for that hospital
   — no other hospital's or category's rate is substituted for it.

---

### User Story 4 - Compare hospitals by drug and payer across the whole Houston roster (Priority: P2)

A user picks one or more of the 33 drugs (same category-checkbox UI as Story
1) and one or more payers, drawn from the full set of payer/plan names seen
across every ingested hospital (not just one hospital's file), and sees the
list of hospitals that publish at least one selected drug with a verified
rate from at least one selected payer. Expanding a hospital shows its full
Story-2 breakdown for the matching drug(s); the "All payer-specific
negotiated rates" section for that hospital/drug is collapsed behind an
explicit "Show other payers for this drug at this hospital" checkbox rather
than shown automatically, so the page's primary focus stays on the
user-selected payer comparison rather than every payer at once.

**Why this priority**: Extends Story 1/2's single-hospital drug lookup into a
cross-hospital, payer-driven comparison — valuable once the core breakdown
(Story 1/2) and trust layer (Story 3) exist, but not required for the app's
core promise of a sourced, per-hospital breakdown.

**Independent Test**: Select one drug and one payer known (from ingested
data) to be published, verified, at exactly N hospitals; confirm the
resulting hospital list has exactly N entries, and that a hospital's payer
table stays collapsed until its toggle checkbox is checked.

**Acceptance Scenarios**:

1. **Given** the payer comparison page's payer checklist, **When** it loads,
   **Then** it shows one checkbox per distinct payer across all ingested
   hospitals, with "Select all" / "Clear all" actions, and no payer appears
   twice under two different spellings of the same name (see dedup rule
   below).
2. **Given** the user selects drugs and payers, **When** results render,
   **Then** only hospitals with a verified rate from at least one selected
   payer for at least one selected drug appear.
3. **Given** a matching hospital is expanded, **When** its breakdown first
   renders, **Then** the "All payer-specific negotiated rates" section is
   hidden until the user checks "Show other payers for this drug at this
   hospital".
4. **Given** a payer's name is spelled differently across hospitals (e.g.
   "United" at one hospital, "UnitedHealthcare" at another, "Triwest Health
   Alliance" vs. "Triwest Healthcare Alliance"), **When** the user selects
   that payer's checkbox once, **Then** hospitals publishing either spelling
   are included in the results, and the payer checklist shows one checkbox
   for it, not one per spelling.
5. **Given** two distinct payers happen to share a generic descriptor word
   (e.g. "Aetna-Kelsey Care" vs. standalone "Aetna" and standalone "Kelsey"),
   **When** the dedup logic groups payer names, **Then** "Aetna" and "Kelsey"
   are never merged into the same checkbox on the strength of a third,
   different compound/joint-venture name alone.

---

### Edge Cases

- What happens when a selected drug is published by zero Houston hospitals? The
  app states that plainly rather than showing an empty or misleading result.
- What happens when a hospital's MRF link that worked at last check is now
  dead? That hospital shows as data-unavailable for the affected drugs rather
  than being silently excluded from the hospital roster entirely.
- What happens when a drug's FDA label lists more than one approved adult
  regimen? The specific regimen/indication used for the dose figure is stated
  next to it.
- What happens when a hospital publishes a payer/plan scheme that doesn't
  match any of the named schemes seen in another hospital's file? It is shown
  under its own name as that hospital publishes it — payer scheme names are
  not normalized or forced to match a fixed universal list.
- What happens when a drug's WAC/list benchmark or CMS ASP entry isn't
  available for some reason? That field shows "not publicly available" rather
  than a blank or a zero.
- What happens when the same payer is spelled differently across two or more
  hospitals' own MRFs (alias, abbreviation, or concatenation, e.g. "United" /
  "UnitedHealthcare", "Independent Med System" / "Independent Medical
  System")? On the payer-comparison page and on each hospital's own payer
  table, the UI groups these under one canonical checkbox/label for
  selection and display purposes only — this is a display-layer grouping,
  not a change to any hospital's underlying Charge Record (Principle III):
  each row still carries its own hospital's original `payer_name` and
  citation, only the checkbox/label the user selects from is merged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present all 33 tracked oncology drugs as
  selectable checkboxes, grouped by their 7 categories (Chemotherapy,
  Immunotherapy, Targeted Therapy, Hormone Therapy, Supportive Care,
  Antibody-Drug Conjugates, Cellular and Gene Therapy).
- **FR-002**: For each drug the user selects, the system MUST show only the
  Houston-area hospitals (from the locked 44-hospital scope) that publish a
  charge for that drug in their own ingested MRF data.
- **FR-003**: The system MUST show a hospital as data-unavailable for a given
  drug (rather than silently omitting it from the roster) specifically when
  that hospital's MRF could not be ingested (broken link, unparseable file).
  A hospital that was successfully ingested but genuinely does not publish a
  given drug is not shown for that drug at all (per FR-002) — this is a normal
  absence, not an unavailable/failure status.
- **FR-004**: For every selected drug, the system MUST render one full
  pricing/reimbursement breakdown per hospital that publishes it — not a
  single representative example applied to all hospitals.
- **FR-005**: Each breakdown MUST include: the hospital's own charge range for
  that drug, the CMS Medicare Part B ASP payment benchmark, the calculated
  ASP+6% Medicare reimbursement figure with its formula shown, the WAC/list
  benchmark, the markup ratio (per-payer rate ÷ ASP) with a flag when it
  exceeds 3x, and every payer/plan rate that specific hospital publishes for
  that drug.
- **FR-006**: The system MUST include a 340B acquisition-cost estimate and
  spread in a hospital's breakdown only when that hospital's 340B enrollment
  has been independently verified twice with agreement; it MUST label this
  line as an industry-average estimate, not the hospital's actual ceiling
  price.
- **FR-007**: The system MUST omit the 340B line entirely for hospitals that
  are not 340B-enrolled or whose enrollment status is unverified (the two
  checks disagreed).
- **FR-008**: The system MUST verify, independently twice, that a specific
  named payer/plan scheme is actually present in a hospital's own published
  data before including that scheme's rate in any calculation; disagreement
  between the two checks excludes that scheme's rate for that hospital rather
  than guessing.
- **FR-009**: The system MUST source each drug's adult dose scale-up
  independently from that specific drug's own FDA prescribing label — never
  reused or inferred from another drug's regimen.
- **FR-010**: For drugs dosed by body weight or body-surface-area rather than a
  fixed amount, the system MUST label the resulting "/dose" figure as an
  illustrative reference calculation (using a disclosed standard reference
  body weight or body-surface-area), not the hospital's actual patient dose.
- **FR-011**: When a drug's FDA label carries more than one approved adult
  regimen or indication, the system MUST state which specific one was used for
  the shown dose figure.
- **FR-012**: Every dollar figure, dose figure, or ratio the system displays
  MUST carry a visible citation to its source (a hospital's MRF file name and
  retrieval date, or an external source link and access date); every
  calculated (non-quoted) figure MUST show its formula alongside the citation.
- **FR-013**: The system MUST NOT display a figure that has no traceable
  source; where a value is not published or not available, the system MUST
  show that fact explicitly rather than leaving the field blank or defaulting
  to zero.
- **FR-014**: The system MUST reject storing or displaying any record that is
  missing its required source citation or, for calculated values, its formula
  — this check runs automatically, not as a manual review step.
- **FR-015**: The scope of hospitals is fixed to the 44 Houston-area hospitals
  already reviewed and locked in the approved design; hospitals outside this
  set are out of scope for this feature.
- **FR-016**: The system MUST provide a payer-comparison view, separate from
  the per-hospital drug view (FR-001-FR-005), where the user selects drugs
  (same category-checkbox UI) and payers (checkboxes covering every distinct
  payer name seen across all ingested hospitals, with Select-all/Clear-all
  actions), and sees only hospitals with a verified rate from at least one
  selected payer for at least one selected drug.
- **FR-017**: On the payer-comparison view only, the system MUST hide a
  hospital's "All payer-specific negotiated rates" section behind an explicit
  opt-in checkbox ("Show other payers for this drug at this hospital") rather
  than displaying it automatically on expansion; the per-hospital drug view
  (FR-001-FR-005) is unaffected and continues to show this section directly.
- **FR-018**: Where the same payer's name is spelled or formatted differently
  across hospitals' own MRFs (case, whitespace, abbreviation, or
  concatenation variants), the system MUST present one canonical
  checkbox/label for that payer in the payer checklist and in each hospital's
  payer table, and MUST treat a selection of that checkbox as matching every
  hospital's variant spelling — without altering, merging, or re-attributing
  any hospital's own underlying Charge Record or its citation (Principle
  III). Two distinct payer names MUST NOT be merged solely because both
  separately share a substring with a third, different compound/joint-venture
  payer name.
- **FR-019**: In addition to the 340B-dependent margin scenarios (FR-006), the
  system MUST always compute and show a Medicare-reimbursement-vs-WAC margin
  comparison (ASP+6% reimbursement against the drug's WAC acquisition cost)
  whenever both the ASP and WAC benchmarks are available, independent of the
  hospital's 340B enrollment status, since WAC — not the 340B ceiling price —
  is the acquisition cost a non-340B hospital actually pays.

### Key Entities

- **Drug**: One of the 33 tracked oncology drugs. Attributes: name, HCPCS/Q
  code, category, FDA-label dosing pattern (fixed / weight-based /
  BSA-based) and the specific adult regimen cited, CMS ASP benchmark, WAC/list
  benchmark citation.
- **Hospital**: One of the 44 locked Houston-area hospitals. Attributes: name,
  MRF source file/link, last ingestion status (success / failed with reason),
  340B enrollment status (enrolled / not enrolled / unverified) with its
  verification date and source.
- **Charge Record**: One hospital's published rate for one drug under one
  named payer/plan scheme. Attributes: hospital, drug, payer/plan name, rate,
  billing setting, source file + retrieval date.
- **Pricing Breakdown**: The computed, per-hospital, per-drug view combining a
  hospital's charge records with the drug's benchmarks — the full output shown
  to the user for User Story 2. Includes both the always-available WAC-margin
  scenario (FR-019) and, when 340B-enrolled, the three 340B-margin scenarios
  (FR-006).
- **Canonical Payer Group** (display-layer only, User Story 4): A set of raw
  `payer_name` spellings across one or more hospitals' Charge Records that
  refer to the same real payer, collapsed to a single checkbox/label in the
  payer checklist and in each hospital's payer table. Does not modify or
  merge the underlying Charge Records — purely a selection/display grouping
  (Principle III still applies to the underlying data).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from opening the app to viewing a full pricing
  breakdown for a chosen drug at a chosen hospital in 3 clicks or fewer.
- **SC-002**: 100% of numeric figures shown anywhere in the app carry a visible
  source citation or formula — zero unsourced figures in any rendered view.
- **SC-003**: 100% of hospitals shown as 340B-dependent-line-included have a
  recorded double-check with agreement; 0% of hospitals show that line based
  on a single, unconfirmed check.
- **SC-004**: For a drug published by M of the 44 hospitals, selecting that
  drug produces exactly M full breakdowns — no fewer (silently dropped) and no
  more (fabricated hospitals).
- **SC-005**: A user can distinguish, without needing to ask anyone, whether a
  given hospital's data for a given drug is confirmed, unverified, or
  unavailable, directly from what's on screen.

## Assumptions

- The 44-hospital Houston-area scope and inclusion/exclusion criteria already
  reviewed and approved in
  `docs/superpowers/specs/2026-07-15-clearprice-houston-oncology-pricing-design.md`
  §2 are treated as final for this feature; re-litigating which hospitals
  belong in scope is out of scope here.
- The 33-drug list and 7-category taxonomy already defined in
  `drugs_list.tsv` is treated as final for this feature.
- A cash/self-pay price (e.g. SingleCare, GoodRx, Drugs.com Price Guide) is
  never treated as a WAC benchmark anywhere in this app; where no true WAC
  citation is publicly available, the WAC field shows "not publicly
  available" rather than a cash price.
- Only Houston Methodist Hospital's MRF has been ingested and parsed as of
  this spec; ingesting the remaining 43 hospitals is required work, not
  optional, but is a data-pipeline concern rather than a user-facing scenario
  change.
- MD Anderson Cancer Center and Kelsey-Seybold Clinic — both real, prominent
  Houston oncology providers — remain excluded from the 44-hospital scope for
  v1. This is unresolved, not a reviewed decision: neither appears under any
  checked name variant in `Texas_validated_final.xlsx`'s 700-row source list,
  so no MRF link exists to ingest from. Per
  `docs/superpowers/specs/2026-07-15-clearprice-houston-oncology-pricing-design.md`
  §9, closing this gap requires locating each hospital's MRF outside that
  source file, which is out of scope for this feature.
- 340B enrollment status is sourced from HRSA's public covered-entity search
  (enrollment is public; the confidential ceiling price is not, and is
  explicitly out of scope — see `340B_pricing_research.md`).
- This feature does not involve patient-identifiable data of any kind; all
  data is hospital-published price transparency data, public regulatory
  benchmarks, and public drug labeling.
- This is a single-user local tool with no login or access control — it is not
  built for multiple concurrent users or hosted multi-tenant access.
- Ingested hospital MRF data and 340B enrollment status refresh only when the
  user deliberately re-runs ingestion; there is no automatic background
  refresh schedule. Data shown at any time reflects the state as of its last
  manual ingestion run, and the app surfaces when that was (per FR-012's
  retrieval-date citation) rather than implying it is always current.
- The seed hospital list (`houston_candidates_final.json`) has at least one
  known-bad source URL: "Baylor St. Luke's Medical Center - Houston" is mapped
  to a Dignity Health MRF link for an unrelated Arizona facility
  ("Arizona General Hospital Laveen"), which returns an HTML page rather than
  a machine-readable file. Ingestion records this hospital as failed with the
  resulting JSON-parse error rather than fabricating or guessing a corrected
  URL; a human must re-source the correct link for that hospital.
