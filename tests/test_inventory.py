"""
test_inventory.py
-----------------
Structural tests for the Nornir inventory.

These validate that the inventory files are well-formed and load correctly.
They do NOT require a live device, so they run anywhere — including in a CI
pipeline (we'll wire up GitHub Actions in a later phase). Writing tests that
don't depend on live infrastructure is a key automation skill.

Run with:
    pytest -v
"""

import os
from pathlib import Path

import pytest
from nornir import InitNornir


@pytest.fixture
def nr():
    """Initialize Nornir against the project's config.yaml."""
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)
    return InitNornir(config_file="config.yaml")


def test_inventory_has_hosts(nr):
    """The inventory should contain at least one host."""
    assert len(nr.inventory.hosts) >= 1


def test_every_host_has_platform(nr):
    """Every host must define a platform (required by Netmiko to connect)."""
    for name, host in nr.inventory.hosts.items():
        assert host.platform, f"Host '{name}' is missing a platform"


def test_every_host_has_hostname(nr):
    """Every host must define a hostname (the IP/FQDN to connect to)."""
    for name, host in nr.inventory.hosts.items():
        assert host.hostname, f"Host '{name}' is missing a hostname"


def test_cisco_group_exists(nr):
    """The cisco_ios group should be defined for shared vendor settings."""
    assert "cisco_ios" in nr.inventory.groups
