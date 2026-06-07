"""
compare_configs.py
------------------
Compare the two most recent configuration backups for each device and report
exactly what changed.

For every device that has at least two backups in backups/, this script:
  1. Selects the two most recent backups.
  2. Normalizes both (strips timestamps and other housekeeping noise).
  3. Produces a unified diff (the same format git uses).
  4. Prints a color-coded diff to the terminal.
  5. Saves a Markdown diff report to reports/.

This is purely a filesystem operation — it does NOT connect to any device, so
it needs no credentials and runs instantly.

Run from the project root:
    python scripts/compare_configs.py
"""

from datetime import datetime
from pathlib import Path

from rich.console import Console

from config_utils import group_backups_by_device, generate_diff

console = Console()
BACKUP_DIR = Path("backups")
REPORT_DIR = Path("reports")


def print_diff(device, diff_lines):
    """Print a unified diff to the terminal with color coding.

    markup=False is set on content lines so that any square brackets inside a
    real config can't be misread as Rich style tags.
    """
    console.print(f"\n{device}", style="bold underline")

    if not diff_lines:
        console.print("  No changes between the two most recent backups.", style="green")
        return

    for line in diff_lines:
        if line.startswith("+++") or line.startswith("---"):
            style = "dim"           # file header lines
        elif line.startswith("@@"):
            style = "cyan"          # hunk location markers
        elif line.startswith("+"):
            style = "green"         # added lines
        elif line.startswith("-"):
            style = "red"           # removed lines
        else:
            style = ""              # unchanged context lines
        console.print("  " + line, style=style, markup=False)


def save_report(device, old_path, new_path, diff_lines, run_ts):
    """Write a Markdown diff report to reports/ and return its path.

    The diff is wrapped in a ```diff fenced block so it renders with red/green
    highlighting on GitHub and in Markdown viewers.
    """
    REPORT_DIR.mkdir(exist_ok=True)
    report_path = REPORT_DIR / f"{device}_diff_{run_ts}.md"

    lines = [
        f"# Config Diff Report: {device}",
        "",
        f"- **Generated:** {run_ts}",
        f"- **Previous backup:** `{old_path.name}`",
        f"- **Latest backup:** `{new_path.name}`",
        "",
    ]
    if not diff_lines:
        lines.append("**No changes** between the two most recent backups.")
    else:
        lines.append("```diff")
        lines.extend(diff_lines)
        lines.append("```")

    report_path.write_text("\n".join(lines))
    return report_path


def main():
    if not BACKUP_DIR.exists():
        raise SystemExit("No backups/ directory found. Run backup_configs.py first.")

    groups = group_backups_by_device(BACKUP_DIR)
    if not groups:
        raise SystemExit("No backup files found in backups/. Run backup_configs.py first.")

    run_ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    console.print(
        f"\n[bold]Comparing most recent backups for {len(groups)} device(s)[/bold]"
    )

    for device, files in groups.items():
        if len(files) < 2:
            console.print(f"\n{device}", style="bold underline")
            console.print(
                f"  Only {len(files)} backup found — need at least 2 to compare.",
                style="yellow",
            )
            continue

        # files is sorted oldest-first, so [-2] is the previous and [-1] is newest
        old_path, new_path = files[-2], files[-1]
        diff_lines = generate_diff(old_path, new_path)
        print_diff(device, diff_lines)
        report_path = save_report(device, old_path, new_path, diff_lines, run_ts)
        console.print(f"  report saved -> {report_path}", style="dim")

    console.print("\n[bold]Comparison complete.[/bold]\n")


if __name__ == "__main__":
    main()
