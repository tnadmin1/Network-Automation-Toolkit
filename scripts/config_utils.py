"""
config_utils.py
---------------
Reusable helpers for working with saved device configurations.

This module is intentionally network-free: it operates only on backup files
already on disk. Keeping comparison logic separate from connection logic means
we can unit-test it with no device, and reuse it in Phase 5 for compliance
checking. That separation of concerns is a deliberate design choice.
"""

import re
from difflib import unified_diff
from pathlib import Path

# ---------------------------------------------------------------------------
# Noise patterns
# ---------------------------------------------------------------------------
# Some lines change on EVERY backup even when nothing meaningful changed
# (timestamps, byte counts, etc.). If we don't strip them, a diff flags them
# as "changes" and buries the real signal. Normalizing first is what separates
# a useful comparison tool from a noisy one. Extend this list per-vendor as the
# toolkit grows (Phase 6 multi-vendor support).
NOISE_PATTERNS = [
    re.compile(r"^Building configuration"),
    re.compile(r"^Current configuration"),
    re.compile(r"^! Last configuration change"),
    re.compile(r"^! NVRAM config last updated"),
    re.compile(r"^ntp clock-period"),
]

# Backup filenames look like:  <device>_<YYYY-MM-DD>_<HHMMSS>.cfg
# The device name itself may contain hyphens or underscores, so the regex
# anchors on the trailing date/time pattern to split it off reliably.
BACKUP_RE = re.compile(
    r"^(?P<device>.+)_(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{6})\.cfg$"
)


def normalize_config(text):
    """Return the config as a list of cleaned lines with noise removed.

    - strips trailing whitespace from each line
    - drops lines matching any NOISE_PATTERN
    - drops blank lines at the very start and end
    """
    cleaned = []
    for line in text.splitlines():
        line = line.rstrip()
        if any(pattern.match(line) for pattern in NOISE_PATTERNS):
            continue
        cleaned.append(line)

    # Trim leading/trailing blank lines so they don't create phantom diffs.
    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return cleaned


def parse_backup_filename(path):
    """Return (device_name, timestamp_string) from a backup filename, or None."""
    match = BACKUP_RE.match(path.name)
    if not match:
        return None
    device = match.group("device")
    timestamp = f"{match.group('date')}_{match.group('time')}"
    return device, timestamp


def group_backups_by_device(backup_dir):
    """Return {device_name: [Path, ...]} sorted oldest-first per device.

    Because the timestamp format is zero-padded (YYYY-MM-DD_HHMMSS), sorting
    the filenames alphabetically also sorts them chronologically.
    """
    groups = {}
    for path in Path(backup_dir).glob("*.cfg"):
        parsed = parse_backup_filename(path)
        if not parsed:
            continue  # skip files that don't match the backup naming scheme
        device, _ = parsed
        groups.setdefault(device, []).append(path)

    for device in groups:
        groups[device].sort(key=lambda p: p.name)

    return groups


def generate_diff(old_path, new_path):
    """Return a unified diff (list of lines) between two backup files.

    Both files are normalized before diffing. Unified diff is the same format
    git uses, so the output is instantly familiar to any engineer.
    """
    old_lines = normalize_config(Path(old_path).read_text())
    new_lines = normalize_config(Path(new_path).read_text())
    diff = unified_diff(
        old_lines,
        new_lines,
        fromfile=Path(old_path).name,
        tofile=Path(new_path).name,
        lineterm="",
    )
    return list(diff)
