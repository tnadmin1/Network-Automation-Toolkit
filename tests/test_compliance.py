"""
test_compliance.py
------------------
Tests for the multi-vendor compliance engine in compliance_utils.py.

These prove the SAME engine correctly evaluates a Cisco IOS config AND a
Juniper JunOS config against their respective baselines — with no device.
This is the unit-test evidence that the toolkit is genuinely multi-vendor,
even before a live Juniper box is available.

Run with:
    pytest -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from compliance_utils import check_compliance, PLATFORM_CONFIG_COMMAND  # noqa: E402


def _status_map(results):
    """Helper: turn the results list into {rule_name: status}."""
    return {r["name"]: r["status"] for r in results}


def test_cisco_present_and_absent_rules():
    """Cisco config should pass present/absent rules correctly."""
    config = (
        "service password-encryption\n"
        "ntp server 10.0.0.1\n"
        "line vty 0 4\n"
        " transport input ssh\n"
    )
    rules = [
        {"name": "Password encryption", "type": "present", "pattern": "service password-encryption"},
        {"name": "NTP", "type": "present", "pattern": "ntp server"},
        {"name": "No telnet", "type": "absent", "pattern": "transport input telnet"},
        {"name": "Banner", "type": "present", "pattern": "banner"},
    ]
    status = _status_map(check_compliance(config, rules))
    assert status["Password encryption"] == "PASS"
    assert status["NTP"] == "PASS"
    assert status["No telnet"] == "PASS"   # telnet not present -> compliant
    assert status["Banner"] == "FAIL"      # no banner configured -> finding


def test_juniper_rules():
    """The same engine should evaluate JunOS 'set' syntax correctly."""
    config = (
        "set system ntp server 2.2.2.2\n"
        "set system services ssh\n"
        "set system root-authentication encrypted-password xyz\n"
    )
    rules = [
        {"name": "NTP", "type": "present", "pattern": "set system ntp server"},
        {"name": "SSH", "type": "present", "pattern": "set system services ssh"},
        {"name": "No telnet", "type": "absent", "pattern": "set system services telnet"},
        {"name": "Root auth", "type": "present", "pattern": "set system root-authentication"},
    ]
    status = _status_map(check_compliance(config, rules))
    assert status["NTP"] == "PASS"
    assert status["SSH"] == "PASS"
    assert status["No telnet"] == "PASS"
    assert status["Root auth"] == "PASS"


def test_platform_command_map_covers_both_vendors():
    """The command map must know how to dump config for each supported platform."""
    assert PLATFORM_CONFIG_COMMAND["cisco_ios"] == "show running-config"
    assert "juniper_junos" in PLATFORM_CONFIG_COMMAND
