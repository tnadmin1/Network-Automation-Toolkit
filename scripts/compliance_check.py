"""
compliance_check.py
-------------------
Compliance validation — check every device against a security/configuration
baseline and report violations.

Multi-vendor by design: the baseline (configs/compliance_baseline.yaml) defines
rules per platform. Each device is pulled using ITS platform's config command
and checked against ITS platform's rules. This runs live against Cisco IOS
today; the Juniper path is built and unit-tested, ready for a JunOS device.

A FAIL is a FINDING, not a crash — it marks a gap between how a device IS
configured and how it SHOULD be. Surfacing those gaps is the whole point.

Run from the project root:
    python scripts/compliance_check.py
"""

from datetime import datetime
from pathlib import Path

import yaml
from nornir_netmiko import netmiko_send_command
from rich.console import Console
from rich.table import Table

from nornir_init import init_nornir
from report_utils import export_csv, export_markdown
from compliance_utils import check_compliance, PLATFORM_CONFIG_COMMAND

console = Console()
BASELINE = Path("configs/compliance_baseline.yaml")
REPORT_DIR = Path("reports")
HEADERS = ["device", "platform", "rule", "status"]


def load_baseline(path=BASELINE):
    """Load the per-platform compliance baseline from YAML."""
    return yaml.safe_load(Path(path).read_text())


def get_config(task):
    """Pull the full config using the command appropriate to this platform.

    This is the multi-vendor hinge: the command is chosen from the platform map,
    so a Cisco host gets 'show running-config' and a Juniper host gets
    'show configuration | display set' — automatically, per device.
    """
    command = PLATFORM_CONFIG_COMMAND.get(task.host.platform, "show running-config")
    return task.run(task=netmiko_send_command, command_string=command).result


def main():
    nr = init_nornir()
    baseline = load_baseline()

    results = nr.run(task=get_config)

    rows = []
    for host in nr.inventory.hosts:
        platform = nr.inventory.hosts[host].platform
        rules = baseline.get(platform, [])

        if results[host].failed:
            console.print(f"\n{host}", style="bold underline")
            console.print("  UNREACHABLE", style="red")
            continue

        if not rules:
            console.print(f"\n{host} ({platform})", style="bold underline")
            console.print(f"  No baseline defined for platform '{platform}'", style="yellow")
            continue

        config_text = results[host][0].result
        checks = check_compliance(config_text, rules)

        passed = sum(1 for c in checks if c["status"] == "PASS")
        total = len(checks)
        verdict_style = "green" if passed == total else "yellow"
        console.print(f"\n{host} ({platform})", style="bold underline")
        console.print(f"  {passed}/{total} rules passed", style=verdict_style)

        for c in checks:
            rows.append({
                "device": host,
                "platform": platform,
                "rule": c["name"],
                "status": c["status"],
            })

    if not rows:
        console.print("\nNo compliance data collected.\n", style="yellow")
        return

    # --- detail table to terminal ---
    table = Table(title="Compliance Report")
    for col in HEADERS:
        table.add_column(col)
    for row in rows:
        color = "green" if row["status"] == "PASS" else "red"
        table.add_row(
            row["device"],
            row["platform"],
            row["rule"],
            f"[{color}]{row['status']}[/{color}]",
        )
    console.print(table)

    # --- export reports ---
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    csv_path = export_csv(rows, HEADERS, REPORT_DIR / f"compliance_{ts}.csv")
    md_path = export_markdown(rows, HEADERS, REPORT_DIR / f"compliance_{ts}.md", "Compliance Report")
    console.print(f"\nReports saved:\n  {csv_path}\n  {md_path}\n", style="dim")


if __name__ == "__main__":
    main()
