from __future__ import annotations

from src.ingestion.ingest_hospital import ingest_hospital
from src.reference_data.hospitals import load_hospitals


def run_all() -> None:
    """Manual, one-shot ingestion run over all 44 Houston hospitals (no
    scheduler, per spec Clarifications). Invoke with:
        python -m src.ingestion.run_all
    """
    hospitals = load_hospitals()
    succeeded = 0
    failed = 0

    for hospital in hospitals:
        result = ingest_hospital(hospital)
        status = result["ingestion_status"]
        if status == "success":
            succeeded += 1
            print(f"[OK]     {hospital.id}: {len(result['charge_records'])} charge records", flush=True)
        else:
            failed += 1
            print(f"[FAILED] {hospital.id}: {status}", flush=True)

    print(f"\n{succeeded}/{len(hospitals)} hospitals ingested successfully, {failed} failed.", flush=True)


if __name__ == "__main__":
    run_all()
