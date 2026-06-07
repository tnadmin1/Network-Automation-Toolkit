"""
health_check.py
---------------
Device health check — gathers operational vitals across the fleet and exports
a report.

For every device in the inventory, this collects:
  - hostname and uptime  (from 'show version')
  - 5-minute CPU load    (from 'show processes cpu')
  - memory used percent  (from 'show processes memory')

Each metric is parsed defensively: if a device returns output we can't parse
(common on older IOS versions), that metric becomes "N/A" instead of crashing
the whole run. Results print to the terminal and export to CSV + Markdown.

Run from the project root:
    python scripts/health_check.py
"""

import re
from datetime import datetime
from pathlib import Path

from nornir_netmiko import netmiko_send_command
from rich.console import Console
from rich.table import Table

from nornir_init import init_nornir
from report_utils import export_csv, export_markdown

console = Console()
REPORT_DIR = Path("reports")

# Regex parsers kept module-level so they can be unit-tested with sample text.
CPU_RE = re.compile(r"five minutes:\s*(\d+)%")
MEM_RE = re.compile(r"Total:\s*(\d+)\s+Used:\s*(\d+)", re.IGNORECASE)

HEADERS = ["device", "status", "hostname", "uptime", "cpu_5min", "mem_used_pct"]


def parse_cpu(text):
    """Extract the 5-minute CPU percentage from 'show processes cpu' output."""
    match = CPU_RE.search(text or "")
    return f"{match.group(1)}%" if match else "N/A"


def parse_memory(text):
    """Compute memory-used percentage from 'show processes memory' output."""
    match = MEM_RE.search(text or "")
    if not match:
        return "N/A"
    total, used = int(match.group(1)), int(match.group(2))
    if total == 0:
        return "N/A"
    return f"{used / total * 100:.1f}%"


def main():
    nr = init_nornir()

    # Run each command across the whole fleet. Nornir reuses the SSH connection
    # per host between runs, so this is efficient.
    versions = nr.run(task=netmiko_send_command, command_string="show version", use_textfsm=True)
    cpus = nr.run(task=netmiko_send_command, command_string="show processes cpu")
    mems = nr.run(task=netmiko_send_command, command_string="show processes memory")

    rows = []
    for host in nr.inventory.hosts:
        row = {
            "device": host,
            "status": "OK",
            "hostname": "-",
            "uptime": "-",
            "cpu_5min": "-",
            "mem_used_pct": "-",
        }

        # If we couldn't even pull 'show version', the device is unreachable.
        if versions[host].failed:
            row["status"] = "UNREACHABLE"
            rows.append(row)
            continue

        parsed = versions[host][0].result
        if isinstance(parsed, list) and parsed:
            row["hostname"] = parsed[0].get("hostname", "-")
            row["uptime"] = parsed[0].get("uptime", "-")

        if not cpus[host].failed:
            row["cpu_5min"] = parse_cpu(cpus[host][0].result)
        if not mems[host].failed:
            row["mem_used_pct"] = parse_memory(mems[host][0].result)

        rows.append(row)

    # --- terminal output ---
    table = Table(title="Device Health")
    for col in HEADERS:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(row[h]) for h in HEADERS])
    console.print(table)

    # --- export reports ---
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    csv_path = export_csv(rows, HEADERS, REPORT_DIR / f"health_{ts}.csv")
    md_path = export_markdown(rows, HEADERS, REPORT_DIR / f"health_{ts}.md", "Device Health Report")
    console.print(f"\nReports saved:\n  {csv_path}\n  {md_path}\n", style="dim")


if __name__ == "__main__":
    main()
