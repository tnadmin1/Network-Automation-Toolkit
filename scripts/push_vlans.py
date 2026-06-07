"""
push_vlans.py
-------------
Bulk VLAN management — define VLANs once as data, push them to many devices.

Pipeline:
    configs/vlans.yaml (desired state)
        -> templates/vlans.j2 (Jinja2)
        -> rendered IOS config
        -> pushed to every device in the inventory

Two modes:
    DRY RUN (default):  renders the VLAN config and prints exactly what WOULD
        be sent. Connects to nothing, changes nothing. ALWAYS run this first.
    APPLY (--apply):    takes a pre-change backup, pushes the config, then takes
        a post-change backup so you can diff the result with compare_configs.py.
        Prompts for confirmation before making any change.

Run from the project root:
    python scripts/push_vlans.py            # safe preview (dry run)
    python scripts/push_vlans.py --apply    # actually push (asks to confirm)
"""

import argparse
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from nornir_netmiko import netmiko_send_config
from rich.console import Console

from nornir_init import init_nornir
from backup_configs import backup_running_config  # reuse the Phase 2 backup task

console = Console()
VLAN_DATA = Path("configs/vlans.yaml")
TEMPLATE_DIR = Path("templates")
BACKUP_DIR = Path("backups")


def load_vlan_data(path=VLAN_DATA):
    """Load the desired VLAN state from YAML."""
    return yaml.safe_load(Path(path).read_text())


def render_vlans(vlans, template_dir=TEMPLATE_DIR):
    """Render the vlans.j2 template into a config string from a VLAN list.

    Kept as a small pure function (data in, string out) so it can be unit
    tested without a device.
    """
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("vlans.j2")
    return template.render(vlans=vlans)


def save_results_as_backup(results, run_ts):
    """Save each device's running-config result to backups/ using the standard
    naming scheme, so compare_configs.py can diff these like any other backup.
    """
    BACKUP_DIR.mkdir(exist_ok=True)
    for host, result in results.items():
        if result.failed:
            continue
        config_text = result[0].result
        (BACKUP_DIR / f"{host}_{run_ts}.cfg").write_text(config_text)


def main():
    parser = argparse.ArgumentParser(description="Bulk VLAN management")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually push config to devices (default is a safe dry run).",
    )
    parser.add_argument(
        "--role",
        default="switch",
        help="Only target hosts whose inventory data role matches (default: switch).",
    )
    args = parser.parse_args()

    # 1. Render desired VLAN config from data + template
    data = load_vlan_data()
    vlans = data["vlans"]
    rendered = render_vlans(vlans)
    config_lines = [line for line in rendered.splitlines() if line.strip()]

    console.print(f"\n[bold]Desired VLAN configuration ({len(vlans)} VLANs):[/bold]")
    for line in config_lines:
        console.print("  " + line, style="cyan", markup=False)

    # 2. DRY RUN — show what would happen and stop
    if not args.apply:
        console.print(
            "\n[yellow]DRY RUN[/yellow] — nothing was pushed. "
            "Re-run with [cyan]--apply[/cyan] to push these VLANs.\n"
        )
        return

# 3. APPLY — confirm, back up, push, back up again
    nr = init_nornir()

    # Filter to only the devices whose role matches (VLANs belong on switches).
    targets = nr.filter(filter_func=lambda host: host.get("role") == args.role)

    if not targets.inventory.hosts:
        console.print(
            f"\n[red]No hosts with role '{args.role}' found in inventory.[/red] "
            "Nothing to push.\n"
        )
        return

    hosts = ", ".join(targets.inventory.hosts)
    console.print(
        f"\n[bold red]APPLY MODE[/bold red] — role '[cyan]{args.role}[/cyan]' "
        f"— target device(s): {hosts}"
    )
    if input("Type 'yes' to push these VLANs: ").strip().lower() != "yes":
        console.print("Aborted. No changes made.\n")
        return

    # Pre-change backup = your rollback point
    pre_ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    console.print("\nTaking pre-change backup...")
    save_results_as_backup(targets.run(task=backup_running_config), pre_ts)

    # Push the VLAN configuration
    console.print("Pushing VLAN configuration...")
    push_results = targets.run(task=netmiko_send_config, config_commands=config_lines)
    for host, result in push_results.items():
        status = "[red]FAILED[/red]" if result.failed else "[green]OK[/green]"
        console.print(f"  {status}  {host}")

    # Post-change backup = lets compare_configs.py show exactly what changed
    post_ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    console.print("Taking post-change backup...")
    save_results_as_backup(targets.run(task=backup_running_config), post_ts)

    console.print(
        "\n[bold]Done.[/bold] Run [cyan]python scripts/compare_configs.py[/cyan] "
        "to see exactly what changed.\n"
    )


if __name__ == "__main__":
    main()
