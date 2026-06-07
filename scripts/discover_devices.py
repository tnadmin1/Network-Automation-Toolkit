"""
discover_devices.py
-------------------
Device discovery.

For every device in the inventory, this script:
  1. Tests connectivity and authentication (can we reach it and log in?).
  2. Gathers device facts (hostname, model, version, uptime).
  3. Discovers directly connected neighbors via CDP.

The 'show version' and 'show cdp neighbors detail' outputs are parsed into
structured data using TextFSM (use_textfsm=True). TextFSM turns raw CLI text
into Python dictionaries so we can pull out individual fields reliably —
far better than fragile string-splitting. The templates ship with Netmiko
via the ntc-templates package, so no extra install is needed.

Run from the project root:
    python scripts/discover_devices.py
"""

from nornir_netmiko import netmiko_send_command
from rich.console import Console
from rich.table import Table

from nornir_init import init_nornir

console = Console()


def gather_facts(task):
    """Run 'show version' on one device and return the parsed result."""
    return task.run(
        task=netmiko_send_command,
        command_string="show version",
        use_textfsm=True,
    ).result


def gather_cdp(task):
    """Run 'show cdp neighbors detail' on one device and return parsed result."""
    return task.run(
        task=netmiko_send_command,
        command_string="show cdp neighbors detail",
        use_textfsm=True,
    ).result


def main():
    nr = init_nornir()
    console.print(
        f"\n[bold]Discovered {len(nr.inventory.hosts)} host(s) in inventory[/bold]\n"
    )

    # --- 1 & 2: connectivity + facts ---------------------------------
    facts_results = nr.run(task=gather_facts)

    table = Table(title="Device Facts")
    for col in ("Device", "Status", "Hostname", "Model", "Version", "Uptime"):
        table.add_column(col)

    for host, result in facts_results.items():
        # result.failed is True if the connection or command raised an error
        if result.failed:
            table.add_row(host, "[red]UNREACHABLE[/red]", "-", "-", "-", "-")
            continue

        # result[0].result holds the TextFSM-parsed list of dicts
        parsed = result[0].result
        if isinstance(parsed, list) and parsed:
            info = parsed[0]
            hardware = info.get("hardware", "-")
            if isinstance(hardware, list):
                hardware = ", ".join(hardware) if hardware else "-"
            table.add_row(
                host,
                "[green]OK[/green]",
                info.get("hostname", "-"),
                hardware,
                info.get("version", "-"),
                info.get("uptime", "-"),
            )
        else:
            # Connected fine, but TextFSM couldn't parse the output
            table.add_row(host, "[yellow]PARSE FAILED[/yellow]", "-", "-", "-", "-")

    console.print(table)

    # --- 3: CDP neighbor discovery -----------------------------------
    cdp_results = nr.run(task=gather_cdp)

    cdp_table = Table(title="CDP Neighbors")
    for col in ("Device", "Local Intf", "Neighbor", "Neighbor Intf", "Platform"):
        cdp_table.add_column(col)

    found_any = False
    for host, result in cdp_results.items():
        if result.failed:
            continue
        parsed = result[0].result
        if isinstance(parsed, list) and parsed:
            for n in parsed:
                found_any = True
                cdp_table.add_row(
                    host,
                    n.get("local_port", "-"),
                    n.get("destination_host", "-"),
                    n.get("remote_port", "-"),
                    n.get("platform", "-"),
                )

    if found_any:
        console.print(cdp_table)
    else:
        console.print(
            "\n[dim]No CDP neighbors found "
            "(expected when testing against a single standalone device).[/dim]\n"
        )


if __name__ == "__main__":
    main()
