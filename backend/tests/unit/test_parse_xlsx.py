from __future__ import annotations

import io

import openpyxl

from src.ingestion.parse_xlsx import parse_xlsx_mrf


def _build_workbook(rows: list[list], preamble_rows: int = 0) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for _ in range(preamble_rows):
        ws.append(["Hospital Standard Charges - generated report"])
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


_HEADER = ["description", "code|1", "code|1|type", "setting", "standard_charge|gross", "standard_charge|Aetna|PPO|negotiated_dollar"]


def test_parses_tracked_code_and_ignores_untracked():
    data = _build_workbook(
        [
            _HEADER,
            ["Trastuzumab emtansine 100mg", "J9354", "HCPCS", "outpatient", 9000.0, 8500.0],
            ["Unrelated drug", "J0000", "HCPCS", "outpatient", 100.0, 90.0],
        ]
    )
    records, raw_text = parse_xlsx_mrf(data, "test-hospital", "https://example.org/test.xlsx")

    assert len(records) == 1
    assert records[0].drug_code == "J9354"
    assert records[0].gross_charge_min == 9000.0
    assert records[0].payer_rates[0].rate == 8500.0
    assert records[0].hospital_id == "test-hospital"
    assert "J9354" in raw_text


def test_finds_header_row_past_a_preamble():
    data = _build_workbook(
        [
            _HEADER,
            ["Trastuzumab emtansine 100mg", "J9354", "HCPCS", "outpatient", 9000.0, 8500.0],
        ],
        preamble_rows=2,
    )
    records, _raw_text = parse_xlsx_mrf(data, "test-hospital", "https://example.org/test.xlsx")
    assert len(records) == 1
    assert records[0].drug_code == "J9354"


def test_returns_empty_when_no_recognizable_header():
    data = _build_workbook([["just", "some", "notes"], ["nothing", "tabular", "here"]])
    records, _raw_text = parse_xlsx_mrf(data, "test-hospital", "https://example.org/test.xlsx")
    assert records == []
