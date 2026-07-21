---

description: "Task list for Houston Oncology Drug Pricing Intelligence"
---

# Tasks: Houston Oncology Drug Pricing Intelligence

**Input**: Design documents from `specs/001-houston-oncology-pricing/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md (all present)

**Tests**: Not explicitly requested by the user as TDD, but Constitution Principle VI (Automated Provenance Enforcement) is NON-NEGOTIABLE, so contract tests enforcing it are mandatory foundational work, not optional.

**Organization**: Tasks grouped by user story (spec.md): US1 (P1, drug selection → hospital roster), US2 (P1, full pricing breakdown per hospital), US3 (P2, verification trust layer), US4 (P2, payer comparison page).

## Path Conventions

Web application layout per plan.md: `backend/src/`, `backend/tests/`, `frontend/`, `houston_hospitals/` (Docker volume mount), `docker/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create repository skeleton: `backend/src/{ingestion,reference_data,verification,calc,api}/`, `backend/tests/{contract,integration,unit}/`, `frontend/`, `docker/`, each with `__init__.py` where applicable
- [X] T002 Initialize Python 3.11 project in `backend/` with `pyproject.toml` / `requirements.txt` — FastAPI, uvicorn, httpx, openpyxl, pytest
- [X] T003 [P] Write `docker/Dockerfile.backend` and `docker/docker-compose.yml` mounting `houston_hospitals/` as the data volume per plan.md §Storage
- [X] T004 [P] Copy `houston_candidates_final.json`, `oncology_top5_by_category.json`, `oncology_top5_asp_reference.json`, `340B_pricing_research.md`, `drugs_list.tsv` into `backend/src/reference_data/` as the seed reference sources

**Checkpoint**: Project scaffolding runs (`docker compose up --build`) with an empty backend responding on `/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ingestion pipeline, reference data, and provenance enforcement that every user story depends on. No user story task may start before this phase is complete (Constitution Principles V, VI).

- [X] T005 Define shared `Citation` value object (source, access_date/retrieved_at) in `backend/src/reference_data/citation.py` per data-model.md
- [X] T005a Run FDA-dose + WAC research subagents, one per drug category from `drugs_list.tsv` (Chemotherapy, Immunotherapy, Targeted Therapy, Hormone Therapy, Supportive Care, Antibody-Drug Conjugates, Cellular and Gene Therapy — 7 categories, 33 drugs): (a) FDA label dose/regimen — fresh research, no existing source, each subagent cites the label directly; (b) WAC — start from `340B_pricing_research.md` per-category rows as a base, subagent re-verifies each row and fresh-researches only rows not already a true WAC citation; a row citing a cash/self-pay price (e.g. SingleCare, Drugs.com Price Guide) is NOT an acceptable WAC value anywhere in this app — replace it with a true WAC citation, or `{available: false, reason: "WAC not publicly available"}` if none exists; write consolidated findings to `backend/src/reference_data/fda_wac_research/<category>.json` (Principle III — each subagent scoped to its own category only, no cross-category lookup; blocks T006)
- [X] T006 [P] Build `Drug` reference records (33 drugs: code, name, category, dose_pattern, dose_value, dose_regimen_cited, dose_source, asp_value, asp_source, wac_value, wac_source) in `backend/src/reference_data/drugs.py` from the T005a research output, sourced individually per drug's own FDA label / CMS ASP / WAC citation (Principle III — no reuse of one drug's dose pattern for another; depends on T005a)
- [X] T007 [P] Build `Hospital` reference records (44 hospitals: id, name, mrf_url) in `backend/src/reference_data/hospitals.py` from `houston_candidates_final.json`
- [X] T008 [P] Implement JSON-format MRF parser in `backend/src/ingestion/parse_json.py`
- [X] T009 [P] Implement CSV-format MRF parser in `backend/src/ingestion/parse_csv.py`
- [X] T010 [P] Implement ZIP-format MRF parser in `backend/src/ingestion/parse_zip.py` (delegates to T008/T009 for the contained file)
- [X] T011 [US-shared] Implement per-hospital ingestion orchestrator in `backend/src/ingestion/ingest_hospital.py`: fetch MRF (handles SAS-token URLs), pick parser by format, filter to the 33 tracked codes, normalize to the Charge Record schema, write to `houston_hospitals/<hospital_id>.json`, or record `ingestion_status: failed: <reason>` (depends on T005, T007, T008, T009, T010)
- [X] T012 Implement `backend/src/ingestion/run_all.py` looping T011 over all 44 hospitals (manual invocation only, per spec Clarifications — no scheduler)
- [X] T013 Implement 340B double-check module in `backend/src/verification/enrollment_340b.py`: two independent HRSA OPAIS public-search queries per hospital, agreement required for `enrolled`/`not_enrolled`, else `unverified` (Constitution Principle II)
- [X] T014 Implement payer-scheme double-check module in `backend/src/verification/payer_scheme.py`: two independent passes over a hospital's raw MRF confirming each named payer/plan row before it is marked `verified` (Constitution Principle II)
- [X] T015 Implement Constitution Principle VI contract-test layer in `backend/src/verification/provenance_gate.py`: a function `assert_provenance(record)` that raises if any required field is missing both a citation AND an explicit `{available: false, reason}` not-available marker (per spec Edge Cases — a genuinely unpublished ASP/WAC benchmark renders "not publicly available", it is not grounds to reject the whole record), and always raises if a calculated field is missing its `formula`; called by ingestion (T011) before any write to `houston_hospitals/` and by the calc engine (Phase 4) before any breakdown is returned
- [X] T016 [P] Contract test: reject an ingested Charge Record missing `source_file`/`retrieved_at` in `backend/tests/contract/test_provenance_gate_ingestion.py`
- [X] T017 [P] Contract test: reject a computed Pricing Breakdown field missing `formula` or `source` in `backend/tests/contract/test_provenance_gate_calc.py`
- [X] T018 Setup FastAPI app skeleton, routing, and error handling in `backend/src/api/main.py`

**Checkpoint**: Running `python -m src.ingestion.run_all` produces per-hospital files (or recorded failures) under `houston_hospitals/`; provenance-gate contract tests (T016, T017) pass; FastAPI app boots.

---

## Phase 3: User Story 1 — Select drugs, see available hospitals (Priority: P1) 🎯 MVP

**Goal**: User checks one or more of the 33 drugs and sees the roster of Houston hospitals that actually publish at least one selected drug (FR-001, FR-002, FR-003).

**Independent Test**: Select a single drug known to be ingested for ≥1 hospital; confirm the returned hospital list matches exactly the hospitals whose Charge Records contain that drug code, and that hospitals with `ingestion_status: failed` are shown as unavailable rather than silently dropped.

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement `GET /api/drugs` in `backend/src/api/drugs.py`, returning the 33 reference Drug records (code, name, category)
- [X] T020 [P] [US1] Implement `GET /api/hospitals` in `backend/src/api/hospitals.py`, returning all 44 hospitals with `ingestion_status` and `last_ingested_at` (FR-003)
- [X] T021 [US1] Implement hospital-roster lookup in `backend/src/calc/roster.py`: given selected drug codes, read `houston_hospitals/*.json`, return hospitals whose Charge Records contain at least one selected code, separately listing failed-ingestion hospitals as unavailable (depends on T011, T020)
- [X] T022 [US1] Wire roster lookup into `GET /api/breakdowns` request handling (roster portion only) in `backend/src/api/breakdowns.py` (depends on T021)
- [X] T023 [P] [US1] Build `frontend/index.html` drug checklist grouped by the 7 categories (Chemotherapy, Immunotherapy, Targeted Therapy, Hormone Therapy, Supportive Care, Antibody-Drug Conjugates, Cellular and Gene Therapy), styled to match `ClearPrice_Build_Methodology.html`
- [X] T024 [US1] Implement `frontend/app.js` checkbox-change handler calling `GET /api/drugs` on load and `GET /api/breakdowns?drugs=...` on selection change, rendering the hospital roster (names only at this stage)
- [X] T025 [P] [US1] Integration test: select 2 drugs spanning different categories, verify roster response in `backend/tests/integration/test_roster.py`

**Checkpoint**: Selecting drugs in the UI shows the correct hospital roster, with unavailable/failed hospitals visibly distinguished from hospitals that simply don't publish the drug.

---

## Phase 4: User Story 2 — Full pricing breakdown per hospital (Priority: P1)

**Goal**: For every selected drug, every hospital in its roster shows the complete Section-4-style breakdown: gross charge range, ASP, ASP+6%, WAC, 340B line (if enrolled), dose scale, per-payer table with markup ratios, CGT risk flag where applicable — every figure cited (FR-004 through FR-012).

**Independent Test**: Query `/api/breakdowns?drugs=<code>` for a drug/hospital pair known to have full data; confirm every field in the response carries a source citation, calculated fields carry a formula string, and the 340B line appears only when both HRSA checks agree the hospital is enrolled.

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement ASP+6% and ASP−27% formula functions in `backend/src/calc/reimbursement.py` (depends on T006); both return `omitted` rather than computing against a null/not-available ASP value, per the not-publicly-available edge case
- [X] T027 [P] [US2] Implement markup-ratio calculation (`payer_rate / asp_value`, per-payer not aggregate) plus the FR-005 `markup_ratio_flag` (true when ratio > 3) in `backend/src/calc/markup.py`, carrying each payer row's `billing_setting` through from the Charge Record untouched
- [X] T028 [P] [US2] Implement dose-line assembly (fixed / mg_per_kg × 70kg / mg_per_m2 × 1.7m², with `dose_regimen_cited`) in `backend/src/calc/dose.py` (depends on T006)
- [X] T029 [P] [US2] Implement CGT DRG-risk flag comparison (Q2041/Q2042/Q2055/Q2054/Q2056 vs. $269,139/$314,231) in `backend/src/calc/cgt_risk.py`
- [X] T030 [US2] Implement full Pricing Breakdown assembler in `backend/src/calc/breakdown.py`: combine Charge Record + Drug reference + Hospital 340B status + T026-T029, call `assert_provenance` (T015) on every field, omit `asp_minus27_line` unless `enrolled` (depends on T013, T015, T026, T027, T028, T029)
- [X] T031 [US2] Complete `GET /api/breakdowns` in `backend/src/api/breakdowns.py` to return full breakdowns array plus `unavailable_hospitals` per contracts/api.md (depends on T030)
- [X] T032 [US2] Implement `POST /api/hospitals/{id}/refresh` manual re-ingestion endpoint in `backend/src/api/hospitals.py` (depends on T011)
- [X] T033 [P] [US2] Extend `frontend/app.js` to render one Section-4-style detail block per hospital per selected drug (readout cards, sources table, verdict block, margin-formula table, all-payer rate table, Epic 4 flagging callout) using incremental/grouped rendering per research.md §6
- [X] T034 [P] [US2] Style `frontend/styles.css` to visually match `ClearPrice_Build_Methodology.html`'s Section 4 layout
- [X] T035 [P] [US2] Integration test: full breakdown for a known drug/hospital pair asserts every field has a citation and every calculated field has a formula, in `backend/tests/integration/test_breakdown_full.py`
- [X] T036 [P] [US2] Unit tests for reimbursement/markup/dose/cgt_risk formulas in `backend/tests/unit/test_calc_formulas.py`

**Checkpoint**: Selecting drugs renders complete, fully-cited Section-4-style breakdowns for every hospital in the roster, matching the existing HTML's visual style.

---

## Phase 5: User Story 3 — Verification trust layer (Priority: P2)

**Goal**: Surface the double-check verification state itself (340B enrollment checks, payer-scheme checks) so the user can see that nothing was assumed — including cases marked `unverified` and excluded (FR-013, FR-014).

**Independent Test**: For a hospital with a deliberately mismatched double-check result (simulate disagreement), confirm the value is marked `unverified`, excluded from the breakdown's calculation, and the exclusion reason is visible in the response/UI rather than silently absent.

### Implementation for User Story 3

- [X] T037 [P] [US3] Extend breakdown assembler (T030) to include per-payer `verification_checks` detail and `unverified` exclusions with reasons in the API response
- [X] T038 [P] [US3] Extend hospital response (T020) to include `enrollment_340b_checks` detail (both check results, sources, timestamps)
- [X] T039 [US3] Extend `frontend/app.js`/UI to show a visible "verification" indicator per payer row and per 340B line (verified vs. unverified-and-excluded, with reason)
- [X] T040 [P] [US3] Integration test: simulate disagreeing 340B checks, confirm `unverified` status and exclusion from `asp_minus27_line`, in `backend/tests/integration/test_verification_disagreement.py`

**Checkpoint**: All three user stories independently functional; verification state is transparent end-to-end.

---

## Phase 6: User Story 4 — Payer comparison page (Priority: P2)

**Goal**: A second top-level page where the user selects drugs and payers
(global checklist across all ingested hospitals) and sees only matching
hospitals, with each hospital's "All payer-specific negotiated rates"
section gated behind an opt-in checkbox (FR-016 through FR-018).

**Independent Test**: Select one drug and one payer known to be verified at N
hospitals; confirm exactly N hospitals render, and that a hospital's payer
table stays hidden until its toggle is checked.

- [X] T046 [P] [US4] Implement `wac_margin_scenario` (Medicare ASP+6% vs. WAC, independent of 340B enrollment) in `backend/src/calc/margin_verdict.py`, called unconditionally from `breakdown.py`'s `margin_verdict.medicare_vs_wac` (FR-019)
- [X] T047 [US4] Wire `margin_verdict.medicare_vs_wac`, `per_dose.margin_verdict`, and the existing 340B-gated `medicare_buy_and_bill`/`highest_commercial`/`lowest_medicare_managed` scenarios into `backend/src/calc/breakdown.py`, each passed through `assert_calculated_field_provenance` (Principle VI)
- [X] T048 [P] [US4] Add `#page-payer` markup to `frontend/index.html`: drug-category checkboxes (reusing the Story-1 category-card pattern), a global payer checkbox grid with Select-all/Clear-all, and a results section
- [X] T049 [US4] Implement `frontend/app.js` payer-page state (`payerPageState`): single `GET /api/breakdowns` fetch across all drug codes, client-side filter by selected drugs AND selected payers, grouped by hospital
- [X] T050 [US4] Implement client-side payer-name canonicalization in `frontend/app.js` (`buildPayerCanonicalMap`/`tokenizePayerName`/`compactPayerKey`): token-subset and compact-prefix union-find clustering restricted by a generic-descriptor whitelist so two distinct payers never merge solely via a shared compound/joint-venture name (FR-018); applied to both the payer-comparison page's global payer checklist and the per-hospital payer table filter (Select all/Clear all, default-unchecked)
- [X] T051 [US4] Extend `renderBreakdownCard` in `frontend/app.js` with an `options.gatePayerTable` flag: on the payer-comparison page, "All payer-specific negotiated rates" renders behind a "Show other payers for this drug at this hospital" checkbox, hidden until checked; the hospital page's own call site is unaffected (FR-017)
- [X] T052 [P] [US4] Style `.payer-filter-panel`/`.payer-filter-grid`/`.payer-gate-toggle`/`.payer-gate-section` in `frontend/styles.css`

**Checkpoint**: Payer comparison page independently functional; duplicate/alias payer names verified absent against live ingested data; hospital page's payer table behavior unchanged.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T041 [P] Run full `python -m src.ingestion.run_all` against all 44 hospitals; record actual success/failure counts (design doc §10 flagged this as the long pole — only Houston Methodist parsed so far)
- [X] T042 [P] Document MD Anderson Cancer Center / Kelsey-Seybold Clinic gap resolution (or continued exclusion) in `specs/001-houston-oncology-pricing/spec.md` Assumptions, per design doc §9
- [ ] T043 Run `quickstart.md` end-to-end validation steps 1-6 and record results
- [X] T044 [P] Add `backend/tests/contract/` coverage confirming the API never returns a breakdown lacking required provenance fields (end-to-end, not just unit-level) in `backend/tests/contract/test_api_provenance.py`
- [ ] T045 Fresh-eyes review of the full implementation against Constitution Principles I-VI before calling the feature complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (ingestion, reference data, and the Principle VI provenance gate must exist first)
- **User Story 1 (Phase 3)**: Depends on Foundational only
- **User Story 2 (Phase 4)**: Depends on Foundational; reuses US1's roster lookup (T021) but is independently testable via `/api/breakdowns`
- **User Story 3 (Phase 5)**: Depends on Foundational and on US2's breakdown assembler (T030) since it extends the same response — not fully independent of US2, but independently *testable* once T030 exists
- **User Story 4 (Phase 6)**: Depends on Foundational and US2's breakdown assembler (T030) for `margin_verdict`/`per_dose`; independently testable via `/api/breakdowns` plus the payer-comparison UI once T046-T052 exist
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### Parallel Opportunities

- T006-T010 (reference data + all three parsers) are independent files, run in parallel
- T016, T017 (contract tests) parallel once T015 exists
- T019, T020 (drugs/hospitals endpoints) parallel
- T026-T029 (calc formula modules) parallel, all feed into T030
- T033, T034 (frontend rendering + styling) parallel
- T035, T036 (integration + unit tests) parallel

---

## Parallel Example: Foundational Phase

```bash
Task: "Build Drug reference records in backend/src/reference_data/drugs.py"
Task: "Build Hospital reference records in backend/src/reference_data/hospitals.py"
Task: "Implement JSON-format MRF parser in backend/src/ingestion/parse_json.py"
Task: "Implement CSV-format MRF parser in backend/src/ingestion/parse_csv.py"
Task: "Implement ZIP-format MRF parser in backend/src/ingestion/parse_zip.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational — including the provenance gate, non-negotiable per Constitution Principle VI)
2. Complete Phase 3 (User Story 1 — drug selection → hospital roster)
3. **STOP and VALIDATE**: confirm roster correctness and failed-ingestion visibility independently
4. Demo: checkbox UI showing correct hospital rosters, even before full pricing breakdowns exist

### Incremental Delivery

1. Setup + Foundational → ingestion pipeline + provenance gate operational across all 44 hospitals
2. Add User Story 1 → roster works → demo
3. Add User Story 2 → full Section-4-style breakdowns render → demo
4. Add User Story 3 → verification transparency surfaced → demo
5. Add User Story 4 → payer comparison page, WAC margin scenario, payer-name dedup → demo
6. Polish → full 44-hospital ingestion run, gap documentation, fresh-eyes final review

---

## Notes

- [P] tasks touch different files with no unmet dependencies
- [Story] label maps each task to US1/US2/US3 for traceability
- Constitution Principle VI (T015-T017) is foundational, not optional, and not deferred to Polish
- Commit after each task or logical group; fresh-eyes review at each phase checkpoint per the project's established workflow
