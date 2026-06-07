"""
interface_audit.py
------------------
Interface audit — fleet-wide view of every interface's status.

For each device, this pulls 'show ip interface brief' and reports, per
interface: name, IP address, line status, and protocol status. It also prints
a per-device summary (how many interfaces are up / down / administratively
down) — the kind of at-a-glance number useful for capacity and security
reviews. Results print to the terminal and export to CSV + Markdown.

Run from the project root:
    python scripts/interface_audit.py
"""

from datetime import datetime
from pathlib import Path

from nornir_netmiko import netmiko_send_command
from rich.console import Console
from rich.table import Table

from nornir_init import init_nornir
from report_utils import export_csv, export_markdown

console = Console()
REPORT_DIR = Path("reports")

HEADERS = ["device", "interface", "ip", "status", "protocol"]


def get_field(intf, *keys, default="-"):
    """Return the first present key from a parsed interface dict.

    TextFSM template field names vary slightly between versions (e.g. 'intf'
    vs 'interface'), so we check several candidates.
    """
    for key in keys:
        value = intf.get(key)
        if value:
            return value
    return default


def summarize_interfaces(interfaces):
    """Count interfaces by status. Pure function — unit-tested without a device."""
    summary = {"total": 0, "up": 0, "down": 0, "admin_down": 0}
    for intf in interfaces:
        status = (intf.get("status") or "").lower()
        summary["total"] += 1
        if "admin" in status:
            summary["admin_down"] += 1
        elif status == "up":
            summary["up"] += 1
        else:
            summary["down"] += 1
    return summary


def main():
    nr = init_nornir()
    results = nr.run(
        task=netmiko_send_command,
        command_string="show ip interface brief",
        use_textfsm=True,
    )

    rows = []
    for host in nr.inventory.hosts:
        if results[host].failed:
            console.print(f"\n{host}", style="bold underline")
            console.print("  UNREACHABLE", style="red")
            continue

        parsed = results[host][0].result
        if not isinstance(parsed, list) or not parsed:
            console.print(f"\n{host}", style="bold underline")
            console.print("  Could not parse interface output", style="yellow")
            continue

        # Build per-interface rows
        for intf in parsed:
            rows.append({
                "device": host,
                "interface": get_field(intf, "interface", "intf"),
                "ip": get_field(intf, "ipaddr", "ip_address", default="unassigned"),
                "status": get_field(intf, "status"),
                "protocol": get_field(intf, "proto", "protocol"),
            })

        # Per-device summary line
        summary = summarize_interfaces(parsed)
        console.print(f"\n{host}", style="bold underline")
        console.print(
            f"  total {summary['total']}  |  "
            f"[green]up {summary['up']}[/green]  |  "
            f"[red]down {summary['down']}[/red]  |  "
            f"admin-down {summary['admin_down']}"
        )

    if not rows:
        console.print("\nNo interface data collected.\n", style="yellow")
        return

    # --- full detail table to terminal ---
    table = Table(title="Interface Audit")
    for col in HEADERS:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(row[h]) for h in HEADERS])
    console.print(table)

    # --- export reports ---
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    csv_path = export_csv(rows, HEADERS, REPORT_DIR / f"interfaces_{ts}.csv")
    md_path = export_markdown(rows, HEADERS, REPORT_DIR / f"interfaces_{ts}.md", "Interface Audit Report")
    console.print(f"\nReports saved:\n  {csv_path}\n  {md_path}\n", style="dim")


if __name__ == "__main__":
    main()
