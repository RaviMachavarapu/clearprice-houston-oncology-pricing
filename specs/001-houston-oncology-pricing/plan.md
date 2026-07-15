# Implementation Plan: Houston Oncology Drug Pricing Intelligence

**Branch**: `001-houston-oncology-pricing` | **Date**: 2026-07-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-houston-oncology-pricing/spec.md`

## Summary

Build a single-user, local, checkbox-driven tool that lets the user select any
of 33 oncology drugs and see, for every one of the 44 locked Houston-area
hospitals that actually publishes that drug in its own MRF, a full
pricing/reimbursement breakdown (hospital charge, CMS ASP benchmark, ASP+6%
Medicare reimbursement, WAC benchmark, 340B acquisition estimate where
verified-enrolled, markup ratio, per-payer rates, and an FDA-label-sourced
adult dose scale) — every number cited, nothing assumed. Technical approach:
a Python ingestion pipeline normalizes each hospital's MRF into a common
schema and writes it to a Docker-mounted data volume (single source of
truth); a Python calculation engine reads only from that volume and applies
per-drug reference data (FDA dose, ASP, WAC) plus double-checked verification
flags (340B enrollment, payer-scheme presence); a FastAPI backend exposes the
results as JSON; a plain HTML/JS frontend (styled to match the existing
`ClearPrice_Build_Methodology.html`) renders the drug checklist and the
Section-4-style detail breakdowns.

## Technical Context

**Language/Version**: Python 3.11 (ingestion pipeline, verification, calculation engine, backend API); vanilla HTML5/CSS/JS for the frontend (no build step, no framework)

**Primary Dependencies**: FastAPI + uvicorn (backend API); httpx or requests (MRF fetch over HTTP/HTTPS, including SAS-token URLs); openpyxl (read `Texas_validated_final.xlsx`); Python's `zipfile`/`csv`/`json` stdlib (MRF parsing); a lightweight HTML fetch/parse (e.g. httpx + a minimal parser) for the HRSA 340B OPAIS public search; pytest (all testing)

**Storage**: Normalized per-hospital JSON files (one file per hospital, CMS-standard-charges-like schema restricted to the 33 tracked codes) inside a Docker-managed data volume mounted at `houston_hospitals/` — no relational database; this volume is the single source of truth per Constitution Principle V

**Testing**: pytest — contract tests enforcing Constitution Principle VI (reject any record missing a source citation or, for calculated fields, a formula) before it can reach the data volume or an API response; integration tests per hospital ingestion; unit tests for the calculation engine's formulas (ASP+6%, ASP−27%, markup ratio, dose scale-ups)

**Target Platform**: Local machine, Docker Desktop (Windows host) running the backend + data-volume containers; frontend served locally and opened in a browser — no cloud hosting, no multi-user deployment (per spec Clarifications: single-user, no login)

**Project Type**: Web application (backend API + static frontend), run entirely locally

**Performance Goals**: Interactive UI response for a typical query (a handful of selected drugs across the 44 hospitals) in a few seconds; ingestion is an offline batch job the user runs manually (per spec Clarifications: manual re-run only) and is not latency-sensitive

**Constraints**: No automatic background refresh of ingested data or 340B status (manual re-run only); no authentication/authorization layer (single-user local tool); every rendered number must carry a citation (Constitution Principle IV) enforced automatically (Principle VI) rather than only by convention; the 33-drug set and 44-hospital set are fixed inputs, not user-editable in this feature

**Scale/Scope**: 33 drugs × up to 44 hospitals = up to 1,452 possible drug/hospital breakdowns (fewer in practice, since not every hospital publishes every code); single concurrent user; ingestion touches 44 external MRF sources of mixed format (json/csv/zip/SAS-token URLs) plus one external verification source (HRSA OPAIS public search)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. No Assumptions, No Hallucination | Ingestion/calc design shows "not published" / "not publicly available" for missing data instead of interpolating; no averaging or cross-filling planned anywhere in Technical Context | PASS |
| II. Verify Twice Before Any Calculation Uses a Value | Verification module design (Phase 1 data-model) performs two independent 340B lookups and two independent payer-scheme presence checks before either value can be consumed by the calc engine | PASS |
| III. Per-Drug, Per-Hospital Sourcing — No Cross-Inference | Reference data design keeps a separate FDA-label record per drug (dose, regimen/indication) and a separate normalized extract per hospital; no shared/default lookup table that could leak one drug's or hospital's data into another's result | PASS |
| IV. Full Provenance on Every Rendered Number | Data model (Phase 1) attaches a citation field to every stored value and a formula string to every calculated field; API contracts (Phase 1) always include these alongside the number | PASS |
| V. Single Source of Truth for Ingested Data | Storage decision above: one Docker volume, ingestion is the only writer, backend/frontend are read-only consumers | PASS |
| VI. Automated Provenance Enforcement | Testing strategy above: contract tests reject any record lacking its required citation/formula before it can be written to the volume or served via the API | PASS |

No violations. Complexity Tracking table below is empty — not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-houston-oncology-pricing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── ingestion/            # per-hospital MRF fetch, parse, normalize (one module per format: json/csv/zip)
│   ├── reference_data/       # 33-drug FDA-label dose/regimen records, CMS ASP entries, WAC citations, 44-hospital list
│   ├── verification/         # 340B HRSA OPAIS double-check, payer-scheme double-check
│   ├── calc/                 # calculation engine (ASP+6%, ASP-27% estimate, markup ratio, dose scale-up)
│   └── api/                  # FastAPI routes serving drugs, hospitals, and breakdowns
└── tests/
    ├── contract/              # Principle VI enforcement tests (reject unsourced records)
    ├── integration/            # per-hospital ingestion end-to-end tests
    └── unit/                   # calc engine formula tests

frontend/
├── index.html                 # drug checklist + results shell
├── styles.css                 # matches ClearPrice_Build_Methodology.html visual style
└── app.js                     # checklist interaction, results rendering, Section-4-style detail view

houston_hospitals/             # Docker volume mount point (git-ignored) — normalized per-hospital JSON, ingestion's only output target

docker/
├── Dockerfile.backend
└── docker-compose.yml         # backend service + houston_hospitals volume
```

**Structure Decision**: Web application layout (backend + frontend), consistent
with the approved design's tech stack (§7 of the design doc) — a Python
backend serving a plain HTML/JS frontend, with ingested data isolated in its
own Docker-mounted directory rather than mixed into either the backend or
frontend source tree.

## Complexity Tracking

*No constitution violations — this section intentionally left empty.*
