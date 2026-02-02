#!/bin/bash
#
# NHL Dashboard Daily Update Script
# ==================================
# Run this script daily at 6 AM to update the dashboard with latest data.
#
# Setup with cron (run 'crontab -e' and add):
#   0 6 * * * /path/to/NHL Playoff Project/update_dashboard.sh >> /path/to/update.log 2>&1
#
# Or with launchd on macOS, create a .plist file in ~/Library/LaunchAgents/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "NHL Dashboard Update - $(date)"
echo "=========================================="

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Generate new dashboard data
echo "Generating dashboard data..."
python -m superhuman.dashboard_generator

# Check if data was generated
if [ -f "dashboard_data.json" ]; then
    echo "✅ Dashboard data generated successfully"
    echo "   Size: $(ls -lh dashboard_data.json | awk '{print $5}')"
else
    echo "❌ Failed to generate dashboard data"
    exit 1
fi

# Check for historical snapshots
SNAPSHOT_COUNT=$(ls -1 history/snapshot_*.json 2>/dev/null | wc -l)
echo "   Historical snapshots: $SNAPSHOT_COUNT"

echo ""
echo "Dashboard update complete!"
echo "=========================================="
