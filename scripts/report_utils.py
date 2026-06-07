"""
report_utils.py
---------------
Reusable report export helpers — CSV and Markdown.

Both the health check and interface audit scripts produce a list of rows
(dicts) that need to be written out in standard formats. Centralizing the
export logic here means every report in the toolkit looks consistent, and the
export code can be unit-tested with no device involved.

CSV is for spreadsheets and importing into other tools. Markdown renders as a
clean table on GitHub and in documentation / tickets.
"""

import csv
from pathlib import Path


def export_csv(rows, headers, path):
    """Write a list of dict rows to a CSV file.

    rows    : list of dicts
    headers : list of column keys, in the order they should appear
    path    : output file path
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            # Only write the known columns; missing values become blank.
            writer.writerow({h: row.get(h, "") for h in headers})
    return path


def export_markdown(rows, headers, path, title):
    """Write a list of dict rows to a Markdown table file.

    The output renders with proper table formatting on GitHub.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# {title}",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")

    path.write_text("\n".join(lines) + "\n")
    return path
