from __future__ import annotations

import dataclasses
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

from src.config import houston_hospitals_dir
from src.ingestion.charge_record import ChargeRecord
from src.ingestion.parse_csv import parse_csv_mrf
from src.ingestion.parse_json_streaming import stream_hospital_name, stream_json_mrf
from src.ingestion.parse_xlsx import parse_xlsx_mrf
from src.ingestion.parse_zip import parse_zip_mrf
from src.reference_data.hospitals import Hospital
from src.verification.enrollment_340b import verify_340b_enrollment
from src.verification.hospital_identity import check_hospital_identity
from src.verification.payer_scheme import verify_payer_rates, verify_payer_rates_streaming
from src.verification.provenance_gate import assert_charge_record_provenance

_USER_AGENT = "ClearPrice-Houston-Oncology-Ingestion/1.0"

_SUPPORTED_TYPES = {"json", "csv", "zip", "xlsx", "xlsm"}


def _output_dir() -> Path:
    return houston_hospitals_dir()


_MAX_DOWNLOAD_ATTEMPTS = 3


def _fetch(mrf_url: str) -> httpx.Response:
    """GET the hospital's MRF file. SAS-token URLs carry their auth in the
    query string already, so a plain GET with redirects works for them too.

    Retries a handful of times on a dropped connection: some hospitals'
    hosting closes the connection mid-transfer for large files even below
    the JSON-streaming size threshold.
    """
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_DOWNLOAD_ATTEMPTS + 1):
        try:
            return httpx.get(
                mrf_url,
                headers={"User-Agent": _USER_AGENT},
                timeout=600.0,
                follow_redirects=True,
            )
        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ReadTimeout) as exc:
            last_exc = exc
            if attempt == _MAX_DOWNLOAD_ATTEMPTS:
                break
    raise last_exc


def _fetch_to_tempfile(mrf_url: str) -> str:
    """Streams the MRF response straight to disk instead of buffering it in
    memory — some Houston hospital JSON MRFs run 1GB+, large enough that
    holding the full response body (let alone the parsed object graph) in
    memory raises MemoryError.

    Retries a handful of times on a dropped connection: multi-GB transfers
    over these hospitals' hosting occasionally close mid-stream, and a plain
    re-attempt (no partial-content assumptions) is enough to get through.
    """
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_DOWNLOAD_ATTEMPTS + 1):
        try:
            with httpx.stream(
                "GET", mrf_url, headers={"User-Agent": _USER_AGENT}, timeout=600.0, follow_redirects=True
            ) as response:
                response.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=1 << 20):
                        f.write(chunk)
            return path
        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ReadTimeout) as exc:
            last_exc = exc
            if attempt == _MAX_DOWNLOAD_ATTEMPTS:
                break
    os.remove(path)
    raise last_exc


def _ingest_json_streaming(hospital: Hospital) -> list[ChargeRecord]:
    """Streaming download+parse path for JSON MRFs, used unconditionally (not
    just for the known-huge files) so there is one code path to trust rather
    than a size-based branch that could silently regress.
    """
    tmp_path = _fetch_to_tempfile(hospital.mrf_url)
    try:
        check_hospital_identity(stream_hospital_name(tmp_path), hospital.name)
        records = stream_json_mrf(tmp_path, hospital.id, source_file=hospital.mrf_url)

        all_rates = [rate for record in records for rate in record.payer_rates]
        if all_rates:
            verify_payer_rates_streaming(all_rates, tmp_path)
        for record in records:
            assert_charge_record_provenance(record)

        return records
    finally:
        os.remove(tmp_path)


def _parse(
    mrf_type: str, response: httpx.Response, hospital_id: str, hospital_name: str, source_file: str
) -> tuple[list[ChargeRecord], str]:
    if mrf_type == "csv":
        text = response.text
        return parse_csv_mrf(text, hospital_id, source_file=source_file), text
    if mrf_type == "zip":
        raw_text = response.content.decode("utf-8", errors="ignore")
        return parse_zip_mrf(response.content, hospital_id, source_file=source_file), raw_text
    if mrf_type in ("xlsx", "xlsm"):
        records, raw_text = parse_xlsx_mrf(response.content, hospital_id, source_file=source_file)
        return records, raw_text
    raise ValueError(f"Unsupported MRF type: {mrf_type}")


def _record_to_dict(record: ChargeRecord) -> dict:
    return dataclasses.asdict(record)


def ingest_hospital(hospital: Hospital) -> dict:
    """Fetch, parse, verify, and write one hospital's MRF to
    houston_hospitals/<hospital_id>.json. Never raises on ingestion failure —
    a failed hospital gets ingestion_status: "failed: <reason>" written out
    instead, so run_all.py can loop all 44 hospitals unattended.
    """
    now = datetime.now(timezone.utc).isoformat()

    enrollment_340b, enrollment_checks = verify_340b_enrollment(hospital.name)

    result: dict = {
        "hospital_id": hospital.id,
        "name": hospital.name,
        "mrf_url": hospital.mrf_url,
        "last_ingested_at": now,
        "enrollment_340b": enrollment_340b,
        "enrollment_340b_checks": [dataclasses.asdict(c) for c in enrollment_checks],
        "charge_records": [],
    }

    if hospital.mrf_type not in _SUPPORTED_TYPES:
        result["ingestion_status"] = f"failed: unsupported MRF type '{hospital.mrf_type}'"
        _write(hospital.id, result)
        return result

    try:
        if hospital.mrf_type == "json":
            records = _ingest_json_streaming(hospital)
        else:
            response = _fetch(hospital.mrf_url)
            response.raise_for_status()
            records, raw_text = _parse(
                hospital.mrf_type, response, hospital.id, hospital.name, hospital.mrf_url
            )
            all_rates = [rate for record in records for rate in record.payer_rates]
            if all_rates:
                verify_payer_rates(all_rates, raw_text)
            for record in records:
                assert_charge_record_provenance(record)

        result["ingestion_status"] = "success"
        result["charge_records"] = [_record_to_dict(r) for r in records]
    except Exception as exc:  # noqa: BLE001 - any failure here becomes a recorded status, never a crash
        detail = str(exc) or type(exc).__name__
        result["ingestion_status"] = f"failed: {detail}"

    _write(hospital.id, result)
    return result


def _write(hospital_id: str, result: dict) -> None:
    out_dir = _output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{hospital_id}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
