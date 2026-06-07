"""
nornir_init.py
--------------
Shared initialization helper used by every script in this toolkit.

Why this file exists:
  Every script needs a Nornir object with credentials loaded. Rather than
  copy-paste that setup into each script (and risk handling secrets
  inconsistently), we centralize it here. This is the DRY principle —
  Don't Repeat Yourself — and it's exactly what a reviewer wants to see.

Responsibilities:
  1. Locate the project root so scripts work no matter where they're run from.
  2. Load device credentials from the .env file (never hard-coded).
  3. Initialize Nornir from config.yaml.
  4. Inject those credentials into the inventory at runtime.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from nornir import InitNornir
from nornir.core.inventory import ConnectionOptions


def init_nornir():
    """Return an initialized Nornir object with credentials loaded from .env."""

    # The project root is the parent of this script's folder (scripts/).
    project_root = Path(__file__).resolve().parent.parent

    # Move into the project root so the relative paths inside config.yaml
    # (e.g. "inventory/hosts.yaml") resolve correctly regardless of the
    # directory the user happened to run the script from.
    os.chdir(project_root)

    # Load NET_USERNAME / NET_PASSWORD / NET_SECRET from the .env file.
    load_dotenv(project_root / ".env")

    username = os.getenv("NET_USERNAME")
    password = os.getenv("NET_PASSWORD")
    secret = os.getenv("NET_SECRET", "")

    # Fail loudly and clearly if credentials are missing. A good script
    # tells the user exactly what's wrong instead of throwing a cryptic error.
    if not username or not password:
        raise SystemExit(
            "ERROR: NET_USERNAME and NET_PASSWORD must be set in your .env file.\n"
            "Run:  cp .env.example .env   then fill in your device credentials."
        )

    # Initialize Nornir using the config file (paths are now relative to root).
    nr = InitNornir(config_file="config.yaml")

    # Inject the credentials into the inventory defaults at runtime.
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password

    # If an enable secret was provided, hand it to the Netmiko connection.
    if secret:
        nr.inventory.defaults.connection_options["netmiko"] = ConnectionOptions(
            extras={"secret": secret}
        )

    return nr
