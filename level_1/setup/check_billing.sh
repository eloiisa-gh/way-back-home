#!/bin/bash
# =============================================================================
# Level 1: Billing Check Script
# =============================================================================
# This script handles installing python billing libraries and executing the
# billing-enablement.py script to link the project to an active billing account.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install Google Cloud Billing library if needed/upgrade it
pip install --upgrade --user --quiet google-cloud-billing 2>/dev/null

# Execute the python enablement script
python3 "$SCRIPT_DIR/billing-enablement.py"
