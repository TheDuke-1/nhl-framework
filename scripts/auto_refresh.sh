#!/bin/bash
# =============================================================================
# NHL Playoff Framework - Automated Daily Data Refresh
# =============================================================================
#
# This script refreshes all data sources and regenerates teams.json
# Schedule with cron (Linux/Mac) or Task Scheduler (Windows)
#
# CRON EXAMPLE (run daily at 6 AM):
#   0 6 * * * /path/to/NHL\ Playoff\ Project/scripts/auto_refresh.sh >> /path/to/logs/refresh.log 2>&1
#
# WINDOWS TASK SCHEDULER:
#   1. Open Task Scheduler
#   2. Create Basic Task > Name: "NHL Data Refresh"
#   3. Trigger: Daily at 6:00 AM
#   4. Action: Start a program
#   5. Program: python
#   6. Arguments: scripts/refresh_data.py --force
#   7. Start in: C:\path\to\NHL Playoff Project
#
# =============================================================================

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Log file
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/refresh_$(date +%Y%m%d).log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Starting NHL Data Refresh"
log "=========================================="

cd "$PROJECT_DIR"

# Check Python is available
if ! command -v python3 &> /dev/null; then
    log "ERROR: Python3 not found"
    exit 1
fi

# Run the refresh script
log "Running data refresh..."
python3 scripts/refresh_data.py 2>&1 | tee -a "$LOG_FILE"

# Check if teams.json was updated
if [ -f "data/teams.json" ]; then
    LAST_MODIFIED=$(stat -c %Y "data/teams.json" 2>/dev/null || stat -f %m "data/teams.json" 2>/dev/null)
    NOW=$(date +%s)
    AGE=$((NOW - LAST_MODIFIED))

    if [ $AGE -lt 300 ]; then  # Updated within last 5 minutes
        log "SUCCESS: teams.json updated successfully"
    else
        log "WARNING: teams.json may not have been updated"
    fi
else
    log "ERROR: teams.json not found"
    exit 1
fi

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "refresh_*.log" -mtime +30 -delete 2>/dev/null || true

log "=========================================="
log "Refresh complete"
log "=========================================="
