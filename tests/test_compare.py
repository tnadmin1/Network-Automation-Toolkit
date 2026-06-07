"""
test_compare.py
---------------
Tests for the config comparison logic in config_utils.py.

These use small config snippets and temporary files, so they run with no
network device and no real backups. Fast, deterministic, pure-logic tests
like these are exactly what belongs in a CI pipeline.

Run with:
    pytest -v
"""

import sys
from pathlib import Path

# Make the scripts/ directory importable regardless of where pytest runs.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from config_utils import normalize_config, generate_diff  # noqa: E402


def test_normalize_strips_noise():
    """Housekeeping lines (timestamps, byte counts) should be removed."""
    raw = (
        "Building configuration...\n"
        "Current configuration : 1234 bytes\n"
        "! Last configuration change at 12:00:00\n"
        "hostname ROUTER\n"
    )
    assert normalize_config(raw) == ["hostname ROUTER"]


def test_normalize_trims_blank_edges():
    """Leading and trailing blank lines should be trimmed."""
    raw = "\n\nhostname R1\n\n"
    assert normalize_config(raw) == ["hostname R1"]


def test_identical_configs_produce_no_diff(tmp_path):
    """Two identical configs should yield an empty diff."""
    cfg = "hostname R1\ninterface GigabitEthernet0/0\n description WAN\n"
    a = tmp_path / "dev_2026-01-01_000000.cfg"
    b = tmp_path / "dev_2026-01-02_000000.cfg"
    a.write_text(cfg)
    b.write_text(cfg)
    assert generate_diff(a, b) == []


def test_changed_config_shows_in_diff(tmp_path):
    """A changed line should appear as a removal and an addition."""
    a = tmp_path / "dev_2026-01-01_000000.cfg"
    b = tmp_path / "dev_2026-01-02_000000.cfg"
    a.write_text("hostname R1\n description OLD\n")
    b.write_text("hostname R1\n description NEW\n")
    diff = generate_diff(a, b)

    # The old value should appear on a removal line (single leading '-')
    assert any(line.startswith("-") and "description OLD" in line for line in diff)
    # The new value should appear on an addition line (single leading '+')
    assert any(line.startswith("+") and "description NEW" in line for line in diff)
