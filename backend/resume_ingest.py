from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import houston_hospitals_dir
from src.ingestion.ingest_hospital import ingest_hospital
from src.reference_data.hospitals import load_hospitals


def _current_status(hospital_id: str) -> str | None:
    path = houston_hospitals_dir() / f"{hospital_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("ingestion_status")


def main() -> None:
    hospitals = load_hospitals()

    if len(sys.argv) > 1 and sys.argv[1] == "--ids":
        ids = set(sys.argv[2].split(","))
        targets = [h for h in hospitals if h.id in ids and _current_status(h.id) != "success"]
        print(f"{len(targets)} hospitals in this chunk still pending (not yet 'success')", flush=True)
    else:
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
        pending = [h for h in hospitals if _current_status(h.id) != "success"]
        print(f"{len(pending)} hospitals still pending (not yet 'success')", flush=True)
        targets = pending[:limit]

    for h in targets:
        print(f"ingesting {h.id} ...", flush=True)
        result = ingest_hospital(h)
        print(f"  -> {result['ingestion_status']}", flush=True)


if __name__ == "__main__":
    main()
