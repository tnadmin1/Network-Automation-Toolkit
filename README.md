# network-automation-toolkit

> Enterprise-grade network automation for multi-vendor infrastructure environments.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Ansible](https://img.shields.io/badge/Ansible-2.14+-EE0000?style=flat-square&logo=ansible&logoColor=white)
![Cisco](https://img.shields.io/badge/Cisco-IOS%20%7C%20IOS--XE-1BA0D7?style=flat-square&logo=cisco&logoColor=white)
![Juniper](https://img.shields.io/badge/Juniper-JunOS-84B135?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Complete-success?style=flat-square)

---

## Overview

`network-automation-toolkit` is a production-oriented Python automation framework for managing Cisco IOS/IOS-XE and Juniper JunOS devices at scale. Built on Netmiko, Nornir, Ansible, and Jinja2, this toolkit demonstrates enterprise automation patterns applicable to large-scale infrastructure, federal/DoD-adjacent environments, and multi-vendor network deployments.

The project is built incrementally across multiple phases, with each phase demonstrating a discrete, deployable capability. Architecture decisions are documented throughout to support code review, knowledge transfer, and professional portfolio presentation.

Validated against live Cisco IOS hardware (C5915 router, C2020 switch). Configuration changes follow a backup → change → verify workflow with role-based targeting and dry-run previews.

---

## Capability Roadmap

| Capability | Phase | Status |
|---|---|---|
| Inventory management and device discovery | Phase 2 | Complete |
| Device configuration backup | Phase 2 | Complete |
| Config diff and comparison | Phase 3 | Complete |
| Bulk VLAN management | Phase 3 | Complete |
| Interface auditing | Phase 4 | Complete |
| Device health checks | Phase 4 | Complete |
| Compliance validation | Phase 5 | Complete |
| Multi-vendor support (Cisco + Juniper) | Phase 5 | Complete |
| Report export (CSV / Markdown) | Phase 4 | Complete |
| Topology generation | Phase 6 | Complete |
| Terraform integration (cloud) | Phase 7 | Complete |

---

## Network Topology 

Auto Generated from live CDP data: 
<img width="641" height="266" alt="image" src="https://github.com/user-attachments/assets/87efbd8f-3fbc-4200-99c9-934d18297686" />

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Core language | Python 3.11+ | Automation logic and orchestration |
| SSH connectivity | Netmiko | Vendor-abstracted device SSH sessions |
| Concurrent execution | Nornir | Task parallelism across device fleets |
| Config management | Ansible | Idempotent playbook-based configuration |
| Templating | Jinja2 | Dynamic config generation from variables |
| Version control | Git / GitHub | Code management and portfolio hosting |
| Target platforms | Cisco IOS/IOS-XE, JunOS | Multi-vendor device support |
| Infrastructure-as-Code | Terraform | Provision AWS cloud network (VPC, subnets, gateways) |

---

## Repository Structure

```text
network-automation-toolkit/
├── backups/          # Timestamped device configuration backups (git-ignored)
├── configs/          # Source-of-truth data: VLANs, compliance baseline
├── inventory/        # Device inventory (hosts, groups, defaults)
├── scripts/          # Python automation scripts (Netmiko, Nornir)
├── templates/        # Jinja2 configuration templates
├── reports/          # Generated audit/diff/compliance reports (git-ignored)
├── tests/            # Pytest suite (25 tests, runs without hardware)
├── docs/             # Architecture documentation
├── diagrams/         # Generated network topology diagrams
├── examples/         # Annotated example output for reference
├── terraform/        # Infrastructure-as-code: AWS VPC provisioning
├── .env.example      # Credential template (real .env is git-ignored)
├── bootstrap.sh      # Project setup script
├── config.yaml       # Nornir configuration
├── requirements.txt  # Pinned Python dependencies
└── README.md
```

---

## Prerequisites

- Python 3.11 or higher
- Git 2.30+
- Network access to target devices, or a lab environment (GNS3 / EVE-NG / CML recommended)
- Ansible 2.14+ (installed via `requirements.txt`)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/tnadmin1/Network-Automation-Toolkit.git
cd network-automation-toolkit

# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows (PowerShell)

# Install all dependencies
pip install -r requirements.txt
```

---

## Configuration

Device credentials are **never stored in this repository**. Connection parameters are loaded from environment variables or a local `.env` file (git-ignored).

```bash
# Copy the example credentials file and populate it
cp .env.example .env
# Edit .env with your device credentials — this file is git-ignored
```

For production environments, integrate with a secrets manager such as HashiCorp Vault, AWS Secrets Manager, or Ansible Vault.

---

## Security Notes

- Device credentials must never be committed to version control.
- `.env` is listed in `.gitignore` and is never tracked.
- For sensitive environments (cleared / federal), use Ansible Vault encryption for all variable files containing credentials.
- All scripts log actions with timestamps to support audit trail requirements.

---

## Lab Environment

Scripts are tested against:
- Cisco IOS/IOS-XE (CML, GNS3, or physical hardware)
- Juniper vSRX / vQFX (EVE-NG or physical hardware)
- Linux hosts (Ubuntu 22.04 LTS)
- Juniper JunOS (config format validated via unit tests, pending live hardware)
- AWS (live VPC provisioning via Terraform)

---

## Commands 

## Commands

```bash
python scripts/discover_devices.py                 # connectivity, facts, CDP neighbors
python scripts/backup_configs.py                   # timestamped running-config backup
python scripts/compare_configs.py                  # diff the two most recent backups per device
python scripts/push_vlans.py                       # preview VLAN config
python scripts/push_vlans.py --apply               # push VLANs to switches (role-filtered)
python scripts/interface_audit.py                  # interface status audit
python scripts/health_check.py                     # device health (uptime/CPU/memory)
python scripts/compliance_check.py                 # validate devices against baseline
python scripts/generate_topology.py                # generate network diagram from CDP
cd terraform && terraform init && terraform plan   # provision AWS network (IaC)
```

## Example of Config Backup and Backup Differential Comparison
 <img width="601" height="572" alt="image" src="https://github.com/user-attachments/assets/19a0553d-bdd3-473d-8d15-8d53889626a7" />

---

## Example of Interface Audit and Device Health Check with Multiple Reports for Comparison

<img width="589" height="740" alt="image" src="https://github.com/user-attachments/assets/859422e9-68ca-4bc9-a070-3e40517aaf39" />

---

## Example of Compliance Check and Compliance Report

<img width="1223" height="743" alt="image" src="https://github.com/user-attachments/assets/bfdca309-8d22-432e-89d6-beeceb9f97be" />

---

## Design Decisions

### Why Netmiko over Paramiko
- Device abstraction
- Better multi-vendor support

### Why SQLite instead of PostgreSQL
- Local execution
- Easy portability

### Why YAML inventory
- Human readable
- Git-friendly

### Impact:
- Reduced manual backup time from ~45 min to <5 min
- Enables change rollback
- Supports compliance validation

---

## License

MIT — see [LICENSE](LICENSE) for details.
