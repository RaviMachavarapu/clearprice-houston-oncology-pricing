# Quickstart: Houston Oncology Drug Pricing Intelligence

## Prerequisites

- Docker Desktop running (Windows host)
- Python 3.11 available for running ingestion locally if not containerized

## 1. Bring up the stack

```bash
docker compose -f docker/docker-compose.yml up --build
```

This starts the FastAPI backend and mounts the `houston_hospitals/` volume
(empty on first run — no data has been ingested yet).

## 2. Run ingestion (manual, per hospital list)

```bash
docker compose -f docker/docker-compose.yml exec backend python -m src.ingestion.run_all
```

Expected outcome: for each of the 44 hospitals, a normalized JSON file
appears under `houston_hospitals/`, OR the hospital is recorded with
`ingestion_status: failed: <reason>`. Verify with:

```bash
curl http://localhost:8000/api/hospitals
curl http://localhost:8000/api/status
```

Expect 44 entries from `/api/hospitals`; count how many show
`ingestion_status: success`. `/api/status`'s `ingestion` block is the
single-glance check that ingestion actually ran for every locked hospital on
this machine (`complete: true`, `not_yet_ingested: []`) — since
`houston_hospitals/` is git-ignored, this is how two different machines
confirm they're looking at the same dataset rather than a partial one.

## 3. Verify a single drug/hospital breakdown end-to-end

```bash
curl "http://localhost:8000/api/breakdowns?drugs=J9271"
```

(Substitute `J9271` — Keytruda's code — or any other of the 33 tracked
codes.) Expected outcome:
- `breakdowns` contains one entry per successfully-ingested hospital that
  publishes that code, each with `gross_charge`, `asp`,
  `asp_plus6_line`, `wac`, `dose`, and `payer_rates` fully
  populated with citations (per `data-model.md`).
- `asp_minus27_line` present only for hospitals where
  `enrollment_340b == enrolled` (both HRSA checks agreed).
- `unavailable_hospitals` lists any hospital whose ingestion failed —
  distinct from a hospital that simply doesn't publish this drug (which is
  absent from the response entirely, per FR-002/FR-003).

## 4. Verify multi-drug selection in the UI

Open `frontend/index.html` (served by the backend or opened directly),
check 2+ drug checkboxes spanning different categories, confirm the results
area renders a Section-4-style breakdown block per hospital per selected
drug — not just one hospital per drug.

## 5. Verify the payer-comparison page

Open `frontend/index.html`, click the "Payer Comparison" top tab. Check 1+
drugs and 1+ payers (use "Select all"/"Clear all" to confirm the payer
checklist has no duplicate entries for known alias pairs, e.g. "United" /
"UnitedHealthcare"). Confirm the resulting hospital list only includes
hospitals with a verified rate from a selected payer for a selected drug.
Expand a hospital and confirm "All payer-specific negotiated rates" stays
hidden until "Show other payers for this drug at this hospital" is checked.

## 6. Verify provenance enforcement (Principle VI)

```bash
docker compose -f docker/docker-compose.yml exec backend pytest tests/contract -v
```

Expected outcome: all contract tests pass, confirming that any record
missing a citation or formula is rejected before reaching the volume or the
API — this is the automated check required by Constitution Principle VI,
not a manual review step.

## 7. Manual re-ingestion of one hospital

```bash
curl -X POST http://localhost:8000/api/hospitals/{id}/refresh
```

Confirms the manual-refresh-only behavior (no background/automatic refresh
job runs) per the spec's Clarifications.
