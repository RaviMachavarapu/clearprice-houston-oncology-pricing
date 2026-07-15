<!--
Sync Impact Report
Version change: [TEMPLATE] → 1.0.0
Modified principles: n/a (initial ratification, template placeholders filled)
Added sections: all (Core Principles I-V, Additional Constraints, Development
  Workflow & Fresh-Eyes Review, Governance)
Removed sections: none
Templates requiring updates:
  ✅ .specify/templates/plan-template.md — Constitution Check section will
     reference these 5 principles (verify on next /speckit.plan run)
  ✅ .specify/templates/spec-template.md — no conflicting mandatory sections
  ✅ .specify/templates/tasks-template.md — task categorization compatible
     (data-sourcing and verification tasks fit existing task types)
  ✅ speckit command/skill files — no CLAUDE-only references found requiring
     change
Follow-up TODOs: none — all placeholders resolved from the approved design
  spec (docs/superpowers/specs/2026-07-15-clearprice-houston-oncology-pricing-design.md)
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
another hospital's file, a system-wide average, or a "typical" figure.

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
`oncology_top5_by_category.json`, across its 7 categories (Chemotherapy,
Immunotherapy, Targeted Therapy, Hormone Therapy, Supportive Care,
Antibody-Drug Conjugates, Cellular and Gene Therapy). No drug is added to or
removed from this set without an explicit, separately reviewed decision.

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
project — any point where Principle I, II, or III could be silently violated
(an assumed number, an unverified scheme, a cross-drug/cross-hospital
inference). Findings are fixed before proceeding; the review and its outcome
are reported to the project owner before the next stage begins.

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

**Version**: 1.0.0 | **Ratified**: 2026-07-15 | **Last Amended**: 2026-07-15
