"""
test_topology.py
----------------
Tests for the topology logic in topology_utils.py.

Covers hostname reconciliation, bidirectional link deduplication, and Mermaid
rendering — all with sample data, no device required.

Run with:
    pytest -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from topology_utils import (  # noqa: E402
    build_hostname_map,
    canonicalize,
    build_links,
    render_mermaid,
)


def test_build_hostname_map_normalizes_and_strips_domain():
    mapping = build_hostname_map({"c5915-rtr": "SIGDET_SFFX_RTR.localdomain"})
    assert mapping["SIGDET_SFFX_RTR"] == "c5915-rtr"


def test_canonicalize_maps_known_and_falls_back():
    mapping = {"SIGDET_SFFX_RTR": "c5915-rtr"}
    # Known neighbor (with domain + different case) resolves to inventory name
    assert canonicalize("sigdet_sffx_rtr.localdomain", mapping) == "c5915-rtr"
    # Unknown neighbor falls back to its cleaned name
    assert canonicalize("UNKNOWN-SW", mapping) == "UNKNOWN-SW"


def test_build_links_dedups_bidirectional_reports():
    hostname_map = {"SW1": "sw1", "RTR1": "rtr1"}
    cdp = {
        "rtr1": [{"local_port": "Fa0/4", "remote_port": "Fa1/8", "destination_host": "SW1"}],
        "sw1": [{"local_port": "Fa1/8", "remote_port": "Fa0/4", "destination_host": "RTR1"}],
    }
    links = build_links(cdp, hostname_map)
    # Same physical link reported from both ends collapses to one
    assert len(links) == 1
    assert links[0] == ("rtr1", "Fa0/4", "sw1", "Fa1/8")


def test_render_mermaid_has_graph_header_and_nodes():
    out = render_mermaid([("rtr1", "Fa0/4", "sw1", "Fa1/8")])
    assert out.startswith("graph LR")
    assert "rtr1" in out
    assert "sw1" in out


def test_render_mermaid_handles_empty():
    out = render_mermaid([])
    assert "graph LR" in out
    assert "No neighbors" in out
