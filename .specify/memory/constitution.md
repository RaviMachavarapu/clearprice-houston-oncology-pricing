<!--
Sync Impact Report
Version change: 1.2.0 → 1.3.0
Modified sections:
  Principle III — added an explicit carve-out: client-side, display-only
     grouping of alias/duplicate payer name spellings into one canonical
     checkbox/label (payer comparison page, per-hospital payer table filter)
     is permitted and is NOT a Principle III violation, because it never
     modifies, merges, or re-attributes any hospital's underlying Charge
     Record — each row keeps its own hospital's original payer_name and
     citation; only the selection/display grouping changes. Added the rule
     that such grouping must never transitively merge two distinct payers
     solely because both separately match a third, different
     compound/joint-venture payer name.
  Core Principles — noted that the Medicare-vs-WAC margin comparison is
     computed independent of 340B enrollment (already implemented; now
     explicit so a future reader doesn't assume all margin scenarios require
     340B verification).
Removed sections: none
Templates requiring updates:
  ✅ spec.md, plan.md, tasks.md, data-model.md, contracts/api.md,
     quickstart.md updated in this session to reflect the payer comparison
     page (User Story 4), payer-name canonicalization, and the WAC margin
     scenario.
Follow-up TODOs: none
-->

# ClearPrice Houston Oncology Pricing Constitution

## Core Principles

### I. No Assumptions, No Hallucination (NON-NEGOTIABLE)
Every price, charge, dose, reimbursement figure, or benchmark presented by this
application MUST trace to a real, checkable source: a hospital's own MRF file,
a CMS ASP payment limit file, an FDA prescribing label, or a cited research
document already in this repo. Where a number is not published anywhere, the
application MUST say so explicitly ("not published by this hospital," "not
publicly available") — it MUST NOT interpolate, average, estimate, or
carry over a value from a different drug, different hospital, or different
context to fill the gap. A missing number is always shown as missing.

### II. Verify Twice Before Any Calculation Uses a Value
Two categories of fact — a hospital's 340B enrollment status, and whether a
specific payer/plan scheme is actually published in a given hospital's own
MRF — MUST be checked independently twice before being used in any
calculation. Agreement on both checks is required to use the value.
Disagreement between the two checks results in the value being marked
`unverified` and excluded from calculation, never guessed or averaged to
resolve the conflict. This applies per hospital, per drug, per payer scheme —
not as a one-time global check.

### III. Per-Drug, Per-Hospital Sourcing — No Cross-Inference
Every one of the 33 tracked oncology drugs is sourced independently: its own
FDA label for dosing, its own CMS ASP entry for the payment benchmark, its own
WAC/list citation. No drug's dosing pattern, regimen, or price is inferred
from another drug's label or from a prior worked example (e.g. one drug's
fixed-dose regimen MUST NOT be reused as a template for a different drug).
Likewise, every one of the hospitals in scope is sourced independently from
its own MRF file — no hospital's rate, scheme list, or charge is borrowed from
another hospital's file, a system-wide average, or a "typical" figure. Where a
drug's FDA label carries more than one approved regimen or indication, the
specific regimen/indication used MUST be stated next to the figure — never
left ambiguous as to which one was cited.

*Carve-out — payer-name display grouping*: The UI MAY present two or more
raw payer-name spellings that refer to the same real payer (case, whitespace,
abbreviation, or concatenation variants — e.g. "United" / "UnitedHealthcare")
under one canonical checkbox/label for selection and display purposes. This
is not a Principle III violation as long as it never modifies, merges, or
re-attributes any hospital's underlying Charge Record — each row keeps its
own hospital's original `payer_name` and citation; only the checkbox a row
responds to changes. The grouping logic MUST NOT transitively merge two
distinct payers solely because both separately share a substring with a
third, different compound/joint-venture payer name (e.g. "Aetna" and
"Kelsey" must stay separate even though both partially match "Aetna-Kelsey
Care").

### IV. Full Provenance on Every Rendered Number
Every dollar figure, dose figure, or ratio shown in the UI carries a visible
citation next to it: the source file name and retrieval/access date for
hospital-MRF-derived data, or a source link and access date for external
references (FDA label, CMS ASP file, HRSA 340B lookup, WAC/list research
docs). Any value that is calculated rather than directly quoted (ASP+6%,
ASP−27% estimate, markup ratio, dose scale-ups) shows its formula inline next
to the citation, so a reader can verify the math without trusting it blindly.

### V. Single Source of Truth for Ingested Data
All normalized, per-hospital MRF extracts live in exactly one place: the
Docker data volume described in the approved design (mount path
`houston_hospitals/`). The ingestion pipeline is the only writer to this
volume. The backend and frontend are read-only consumers of it — no parallel
data path, cache, or local file copy is treated as authoritative. If the
volume's data is stale or a hospital's ingestion failed, that is surfaced to
the user as a status (`ingestion failed: <reason>`), not silently bypassed
with data from elsewhere.

### VI. Automated Provenance Enforcement (NON-NEGOTIABLE)
Compliance with Principles I–IV MUST NOT depend on manual diligence alone.
The ingestion pipeline and calculation engine MUST include automated checks
that reject a record before it reaches the Docker volume (Principle V) or the
UI if it lacks a required field: a source file name + retrieval date (for
hospital-MRF-derived data), a source link + access date (for FDA labels, CMS
ASP entries, HRSA 340B lookups, WAC/list citations), or an inline formula (for
any calculated value). These checks are part of the implementation's test
suite — run on every ingestion and every calculation — not a documentation-only
expectation to be checked by eye after the fact.

## Additional Constraints

**Scope (v1):** Houston-metro hospitals only — the 44 hospitals locked in the
approved design spec (`docs/superpowers/specs/2026-07-15-clearprice-houston-oncology-pricing-design.md`,
§2), selected by an explicit, reviewed inclusion/exclusion rule (acute-care or
cancer-treating, Houston-metro branch name, working MRF link at last
validation; behavioral-health/rehab-only/out-of-metro branches excluded).
Expansion to other metros/states is explicitly out of scope for v1 (tracked as
a future phase in `MRF_Intelligence_Product_BA.md` Epic 6) and MUST NOT be
implicitly assumed working in the meantime.

**Drug set:** Exactly the 33 oncology drugs already defined in
`drugs_list.tsv`, across its 7 categories (Chemotherapy,
Immunotherapy, Targeted Therapy, Hormone Therapy, Supportive Care,
Antibody-Drug Conjugates, Cellular and Gene Therapy). No drug is added to or
removed from this set without an explicit, separately reviewed decision. A
cash/self-pay price (e.g. SingleCare, GoodRx, Drugs.com Price Guide) is never
an acceptable substitute for WAC anywhere in this application — where no true
WAC is publicly available, the figure is shown as not available, never
replaced with a cash price.

**Tech stack:** Python ingestion pipeline and calculation engine, served via a
FastAPI JSON backend; a plain HTML/JS frontend (no build step) styled to match
the existing `ClearPrice_Build_Methodology.html`; normalized data stored in a
Docker volume per Principle V. Substituting a different stack requires a
constitution amendment, not an ad hoc implementation choice.

## Development Workflow & Fresh-Eyes Review

This project is built through the Spec Kit pipeline (`/speckit constitution` →
`specify` → `clarify` → `plan` → `tasks` → `implement`), one stage at a time.
Before moving from one completed stage's artifact to the next stage, a
fresh-eyes review of that artifact is required: an explicit check for
placeholders, internal contradictions, ambiguity, and — specific to this
project — any point where Principle I, II, III, or VI could be silently
violated (an assumed number, an unverified scheme, a cross-drug/cross-hospital
inference, or a provenance requirement stated but not actually enforced by an
automated check). Findings are fixed before proceeding; the review and its
outcome are reported to the project owner before the next stage begins.

## Governance

This constitution supersedes ad hoc implementation decisions for this
project. Any amendment (adding/removing a principle, changing scope,
changing the tech stack) follows the same process as a design change: propose
the amendment, run the fresh-eyes review against it, get explicit sign-off,
then update this file and bump the version below. Versioning is semantic:
MAJOR for a principle removed or redefined in a backward-incompatible way,
MINOR for a new principle or materially expanded guidance, PATCH for wording
or clarification only. All Spec Kit artifacts produced downstream (spec,
plan, tasks, implementation) are reviewed for compliance with these
principles at each stage's fresh-eyes review.

**Version**: 1.3.0 | **Ratified**: 2026-07-15 | **Last Amended**: 2026-07-21
