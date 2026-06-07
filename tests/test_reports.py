"""
test_reports.py
---------------
Tests for the Phase 4 reporting and parsing logic.

Covers the export helpers, the health-check regex parsers, and the interface
summary counter — all with sample data and temp files, so no device is needed.

Run with:
    pytest -v
"""

import sys
from pathlib import Path

# Make the scripts/ directory importable regardless of where pytest runs.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from report_utils import export_csv, export_markdown          # noqa: E402
from health_check import parse_cpu, parse_memory              # noqa: E402
from interface_audit import summarize_interfaces              # noqa: E402


# --- report export -------------------------------------------------------
def test_export_csv_writes_header_and_rows(tmp_path):
    rows = [{"device": "r1", "status": "OK"}, {"device": "r2", "status": "DOWN"}]
    path = export_csv(rows, ["device", "status"], tmp_path / "out.csv")
    text = path.read_text()
    assert "device,status" in text
    assert "r1,OK" in text
    assert "r2,DOWN" in text


def test_export_markdown_writes_table(tmp_path):
    rows = [{"device": "r1", "status": "OK"}]
    path = export_markdown(rows, ["device", "status"], tmp_path / "out.md", "Test")
    text = path.read_text()
    assert "# Test" in text
    assert "| device | status |" in text
    assert "| r1 | OK |" in text


# --- health parsers ------------------------------------------------------
def test_parse_cpu_extracts_five_minute_value():
    sample = "CPU utilization for five seconds: 2%/0%; one minute: 1%; five minutes: 7%"
    assert parse_cpu(sample) == "7%"


def test_parse_cpu_returns_na_when_absent():
    assert parse_cpu("no cpu info here") == "N/A"


def test_parse_memory_computes_percentage():
    # 250 used of 1000 total = 25.0%
    sample = "Processor Pool Total: 1000 Used: 250 Free: 750"
    assert parse_memory(sample) == "25.0%"


def test_parse_memory_returns_na_when_absent():
    assert parse_memory("nothing parseable") == "N/A"


# --- interface summary ---------------------------------------------------
def test_summarize_interfaces_counts_by_status():
    interfaces = [
        {"status": "up"},
        {"status": "up"},
        {"status": "down"},
        {"status": "administratively down"},
    ]
    summary = summarize_interfaces(interfaces)
    assert summary == {"total": 4, "up": 2, "down": 1, "admin_down": 1}
