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
```

Expect 44 entries; count how many show `ingestion_status: success`.

## 3. Verify a single drug/hospital breakdown end-to-end

```bash
curl "http://localhost:8000/api/breakdowns?drugs=J9271"
```

(Substitute `J9271` — Keytruda's code — or any other of the 33 tracked
codes.) Expected outcome:
- `breakdowns` contains one entry per successfully-ingested hospital that
  publishes that code, each with `gross_charge_range`, `asp_line`,
  `asp_plus6_line`, `wac_line`, `dose_line`, and `payer_table` fully
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

## 5. Verify provenance enforcement (Principle VI)

```bash
docker compose -f docker/docker-compose.yml exec backend pytest tests/contract -v
```

Expected outcome: all contract tests pass, confirming that any record
missing a citation or formula is rejected before reaching the volume or the
API — this is the automated check required by Constitution Principle VI,
not a manual review step.

## 6. Manual re-ingestion of one hospital

```bash
curl -X POST http://localhost:8000/api/hospitals/{id}/refresh
```

Confirms the manual-refresh-only behavior (no background/automatic refresh
job runs) per the spec's Clarifications.
