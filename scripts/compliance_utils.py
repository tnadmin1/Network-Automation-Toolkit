"""
compliance_utils.py
-------------------
Compliance checking logic and per-platform command mapping.

This is where the toolkit becomes genuinely multi-vendor. A compliance baseline
is defined per platform (Cisco IOS, Juniper JunOS), and the engine evaluates
each device's configuration against the rules for ITS platform. The same engine
handles both vendors because the vendor-specific details live in DATA (the
baseline) and in the command map below — not in the logic. Adding a third
vendor means adding data, not rewriting code.
"""

# Maps a platform to the command that dumps its full configuration.
# Add a vendor here and the compliance check (and, later, the backup script)
# can target it without any logic changes.
PLATFORM_CONFIG_COMMAND = {
    "cisco_ios": "show running-config",
    "juniper_junos": "show configuration | display set",
}


def check_compliance(config_text, rules):
    """Evaluate a device configuration against a list of compliance rules.

    Each rule is a dict with keys: name, type, pattern
      type "present": the pattern MUST appear in the config to PASS
      type "absent":  the pattern must NOT appear in the config to PASS

    Returns a list of dicts, each rule annotated with a "status" of PASS/FAIL.

    This is a pure function (config text + rules in, results out), so it can be
    unit-tested against sample configs from any vendor with no device involved.
    """
    config_lower = (config_text or "").lower()
    results = []

    for rule in rules:
        pattern = rule["pattern"].lower()
        found = pattern in config_lower

        if rule["type"] == "present":
            status = "PASS" if found else "FAIL"
        elif rule["type"] == "absent":
            status = "PASS" if not found else "FAIL"
        else:
            status = "UNKNOWN"

        results.append({
            "name": rule["name"],
            "type": rule["type"],
            "pattern": rule["pattern"],
            "status": status,
        })

    return results
