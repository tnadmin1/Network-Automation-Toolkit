"""
test_vlans.py
-------------
Tests for VLAN config rendering in push_vlans.py.

These render the REAL template with sample data, so they verify your template
logic without needing a device. If the template breaks, these catch it.

Run with:
    pytest -v
"""

import sys
from pathlib import Path

# Make the scripts/ directory importable regardless of where pytest runs.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from push_vlans import render_vlans  # noqa: E402

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def test_render_includes_vlan_ids_and_names():
    """Rendered config should contain each VLAN id and name."""
    vlans = [{"id": 10, "name": "SALES"}, {"id": 20, "name": "ENGINEERING"}]
    out = render_vlans(vlans, TEMPLATE_DIR)
    assert "vlan 10" in out
    assert "name SALES" in out
    assert "vlan 20" in out
    assert "name ENGINEERING" in out


def test_render_handles_empty_list():
    """An empty VLAN list should render to effectively nothing."""
    assert render_vlans([], TEMPLATE_DIR).strip() == ""
