#!/usr/bin/env bash
# ============================================================
# bootstrap.sh — initialize network-automation-toolkit
# ============================================================
# Run once after cloning the repository:
#   chmod +x bootstrap.sh && ./bootstrap.sh
#
# This script creates the directory structure, seeds empty
# directories with .gitkeep placeholders, and sets up the
# Python virtual environment.
# ============================================================

set -euo pipefail   # Exit on error, unset variable, pipe failure

# --- Color output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No color

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# --- 1. Create directory structure --------------------------
log "Creating directory structure..."
dirs=(backups configs inventory scripts templates reports tests docs diagrams examples)
for dir in "${dirs[@]}"; do
    mkdir -p "$dir"
    # .gitkeep: professional convention for tracking empty dirs
    touch "${dir}/.gitkeep"
    echo "    created: ${dir}/"
done

# --- 2. Create credentials example file ---------------------
log "Creating credentials template..."
cat > inventory/credentials.env.example << 'EOF'
# Copy this file to credentials.env and populate with real values.
# credentials.env is excluded from git — NEVER commit real credentials.

NETWORK_USERNAME=your_username
NETWORK_PASSWORD=your_password
NETWORK_ENABLE_SECRET=your_enable_secret
EOF

# --- 3. Create Python virtual environment -------------------
log "Creating Python virtual environment (.venv)..."
python3 -m venv .venv

log "Activating virtual environment and installing dependencies..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# --- 4. Configure git settings for this project -------------
log "Configuring git..."
git config core.autocrlf input          # Unix line endings on commit
git config core.fileMode true           # Track file permission changes
git config pull.rebase false            # Standard merge on pull

# --- 5. Create placeholder docs -----------------------------
log "Creating documentation placeholders..."
cat > docs/architecture.md << 'EOF'
# Architecture

> Documentation added incrementally with each phase.

## Data Flow

Inventory → Logic Engine → Templates → Outputs

See README.md for the full pipeline diagram.
EOF

echo ""
log "Bootstrap complete."
echo ""
echo "  Next steps:"
echo "  1. Activate your environment:  source .venv/bin/activate"
echo "  2. Copy credentials template:  cp inventory/credentials.env.example inventory/credentials.env"
echo "  3. Make your first commit:     git add -A && git commit -m 'feat: initialize project structure'"
echo ""
warn "Never commit inventory/credentials.env — it is already in .gitignore"
