"""
generate_topology.py
--------------------
Generate a current network topology diagram from live device data.

For every device, this collects CDP neighbors, reconciles the reported
hostnames with your inventory names, deduplicates the links, and writes a
Mermaid diagram. GitHub renders the Markdown version as a live picture, so you
can embed it directly in your README.

(LLDP support is the natural extension for non-Cisco neighbors: collect
'show lldp neighbors detail' the same way and merge the links.)

Run from the project root:
    python scripts/generate_topology.py
"""

from datetime import datetime
from pathlib import Path

from nornir_netmiko import netmiko_send_command
from rich.console import Console
from rich.table import Table

from nornir_init import init_nornir
from topology_utils import build_hostname_map, build_links, render_mermaid

console = Console()
DIAGRAM_DIR = Path("diagrams")


def main():
    nr = init_nornir()

    # 1. Gather each device's hostname so CDP neighbor names can be reconciled
    #    back to the inventory names used everywhere else in the toolkit.
    versions = nr.run(
        task=netmiko_send_command, command_string="show version", use_textfsm=True
    )
    device_hostnames = {}
    for host in nr.inventory.hosts:
        if versions[host].failed:
            continue
        parsed = versions[host][0].result
        if isinstance(parsed, list) and parsed:
            device_hostnames[host] = parsed[0].get("hostname", host)
    hostname_map = build_hostname_map(device_hostnames)

    # 2. Gather CDP neighbors from every device.
    cdp = nr.run(
        task=netmiko_send_command,
        command_string="show cdp neighbors detail",
        use_textfsm=True,
    )
    cdp_per_device = {}
    for host in nr.inventory.hosts:
        if cdp[host].failed:
            cdp_per_device[host] = []
            continue
        parsed = cdp[host][0].result
        cdp_per_device[host] = parsed if isinstance(parsed, list) else []

    # 3. Build the deduplicated link list.
    links = build_links(cdp_per_device, hostname_map)

    # --- terminal output ---
    table = Table(title="Discovered Links")
    for col in ("Device A", "Port A", "Device B", "Port B"):
        table.add_column(col)
    for node_a, port_a, node_b, port_b in links:
        table.add_row(node_a, port_a, node_b, port_b)
    console.print(table)
    console.print(f"\nDiscovered {len(links)} link(s).")

    if not links:
        console.print("No CDP neighbors found — nothing to diagram.\n", style="yellow")
        return

    # 4. Render and save the Mermaid diagram. Stable filenames (no timestamp)
    #    so the README can always point at the current topology.
    mermaid = render_mermaid(links)
    DIAGRAM_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    (DIAGRAM_DIR / "topology.mmd").write_text(mermaid + "\n")
    (DIAGRAM_DIR / "topology.md").write_text(
        f"# Network Topology\n\n_Generated {ts} from live CDP data._\n\n"
        f"```mermaid\n{mermaid}\n```\n"
    )

    console.print("\n[bold]Mermaid diagram source:[/bold]\n")
    console.print(mermaid, markup=False)
    console.print(
        "\nSaved to diagrams/topology.md and diagrams/topology.mmd.\n"
        "The .md file renders as a live diagram on GitHub — embed it in your README.\n",
        style="dim",
    )


if __name__ == "__main__":
    main()
