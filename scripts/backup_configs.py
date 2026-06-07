"""
backup_configs.py
-----------------
Configuration backup.

For every device in the inventory, this script:
  1. Connects and pulls the running configuration.
  2. Saves it to  backups/<device>_<timestamp>.cfg

Backups are timestamped so you build a history over time. Phase 3 will add
a comparison tool that diffs any two of these files to show exactly what
changed between two points in time.

Note: the backups/ directory is git-ignored (see .gitignore) so device
configs are never accidentally pushed to a public repo. That's deliberate —
real configs contain sensitive details. To showcase output in your portfolio,
commit a single SANITIZED sample to examples/ instead.

Run from the project root:
    python scripts/backup_configs.py
"""

from datetime import datetime
from pathlib import Path

from nornir_netmiko import netmiko_send_command
from rich.console import Console

from nornir_init import init_nornir

console = Console()
BACKUP_DIR = Path("backups")


def backup_running_config(task):
    """Pull 'show running-config' from a single device."""
    return task.run(
        task=netmiko_send_command,
        command_string="show running-config",
    ).result


def main():
    nr = init_nornir()
    BACKUP_DIR.mkdir(exist_ok=True)

    # One timestamp for the whole run so all files from this run match.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    console.print(
        f"\n[bold]Backing up {len(nr.inventory.hosts)} device(s) "
        f"at {timestamp}...[/bold]\n"
    )

    results = nr.run(task=backup_running_config)

    success = 0
    for host, result in results.items():
        if result.failed:
            console.print(f"  [red]FAILED[/red]   {host} — could not retrieve config")
            continue

        config_text = result[0].result
        filename = BACKUP_DIR / f"{host}_{timestamp}.cfg"
        filename.write_text(config_text)
        line_count = len(config_text.splitlines())
        console.print(
            f"  [green]OK[/green]       {host} — {line_count} lines -> {filename}"
        )
        success += 1

    console.print(
        f"\n[bold]Backup complete: {success}/{len(nr.inventory.hosts)} "
        f"device(s) succeeded.[/bold]\n"
    )


if __name__ == "__main__":
    main()
