#!/usr/bin/env python3
"""
Master Data Refresh Script for NHL Playoff Framework.
Orchestrates fetching from all sources and merging into teams.json.

Usage:
    python refresh_data.py           # Refresh all data
    python refresh_data.py --force   # Force refresh even if data is fresh
    python refresh_data.py --check   # Just check data freshness

Note: Some sources (MoneyPuck) may require browser-based fetching due to
proxy restrictions. This script will report which sources need manual refresh.
"""

import argparse
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, SCRIPTS_DIR, CURRENT_SEASON, get_current_timestamp
from league_calendar import get_data_activity_context
from utils import (
    setup_logging, check_data_freshness, get_data_freshness_report,
    print_header, print_status, load_json_file, validate_teams_data
)

logger = setup_logging("refresh_data")

REFRESH_HEARTBEAT_PATH = Path(__file__).parent.parent / "reports" / "data_refresh_heartbeat.json"

# =============================================================================
# DATA SOURCE RUNNERS
# =============================================================================

def _run_script(data_key, script_name, force=False):
    """Generic runner: check freshness, run a fetch script via subprocess."""
    is_fresh, age, threshold = check_data_freshness(data_key)

    if is_fresh and not force:
        logger.info(f"{data_key} is fresh ({age:.1f}h old, threshold {threshold}h)")
        return True, "skipped (fresh)"

    logger.info(f"Fetching {data_key}...")
    script = SCRIPTS_DIR / script_name

    if not script.exists():
        logger.warning(f"Script not found: {script}")
        return False, "script not found"

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            stdout = result.stdout or ""
            if data_key == "nhl_standings":
                if "EXPECTED_STATIC_FALLBACK:" in stdout:
                    logger.info(f"{data_key} fallback check-in during scheduled break")
                    return True, "expected-static fallback check-in"
                if "BACKUP_PROVIDER_USED:" in stdout:
                    logger.info(f"{data_key} used backup provider")
                    return True, "success (backup provider)"
            logger.info(f"{data_key} fetch completed successfully")
            return True, "success"
        else:
            logger.error(f"{data_key} fetch failed: {result.stderr}")
            return False, f"failed: {result.stderr[:100]}"

    except subprocess.TimeoutExpired:
        logger.error(f"{data_key} fetch timed out")
        return False, "timeout"
    except Exception as e:
        logger.error(f"{data_key} fetch error: {e}")
        return False, str(e)

def check_moneypuck_freshness(force=False):
    """
    Check MoneyPuck data freshness.
    Note: MoneyPuck often requires browser-based fetching due to proxy blocks.
    """
    is_fresh, age, threshold = check_data_freshness("moneypuck_stats")

    if is_fresh:
        logger.info(f"MoneyPuck stats are fresh ({age:.1f}h old, threshold {threshold}h)")
        if force:
            return True, "fresh (force mode)"
        return True, "fresh"

    if age is None:
        return False, "missing - requires browser fetch"
    else:
        return False, f"stale ({age:.1f}h) - may require browser fetch"

def run_merge(force=False):
    """Run the merge script to combine all data sources."""
    logger.info("Merging data from all sources...")
    script = SCRIPTS_DIR / "merge_data.py"

    if not script.exists():
        logger.warning(f"Script not found: {script}")
        return False, "script not found"

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            logger.info("Merge completed successfully")
            # Print merge output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    logger.info(f"  {line}")
            return True, "success"
        else:
            logger.error(f"Merge failed: {result.stderr}")
            return False, f"failed: {result.stderr[:100]}"

    except subprocess.TimeoutExpired:
        logger.error("Merge timed out")
        return False, "timeout"
    except Exception as e:
        logger.error(f"Merge error: {e}")
        return False, str(e)

# =============================================================================
# VALIDATION
# =============================================================================

def validate_output():
    """Validate the merged teams.json file."""
    teams_file = DATA_DIR / "teams.json"

    if not teams_file.exists():
        return False, "teams.json not found"

    data = load_json_file(teams_file)
    teams = data.get("teams", [])

    if not teams:
        return False, "No teams in output"

    # Convert list to dict for validation
    teams_dict = {t["team"]: t for t in teams}
    is_valid, summary = validate_teams_data(teams_dict)

    if not is_valid:
        return False, f"Validation errors: {summary['issues']}"

    # Additional checks
    metadata = data.get("_metadata", {})

    return True, {
        "team_count": len(teams),
        "generated_at": metadata.get("generatedAt", "unknown"),
        "top_team": f"{teams[0]['team']} ({teams[0]['pts']} pts)" if teams else "N/A",
    }

# =============================================================================
# MAIN REFRESH LOGIC
# =============================================================================

def print_freshness_report():
    """Print data freshness status for all files."""
    print_header("Data Freshness Report")

    report = get_data_freshness_report()

    for item in report:
        if item["is_fresh"]:
            color = "green"
        elif item["age_hours"] is not None:
            color = "yellow"
        else:
            color = "red"

        print_status(
            item["file"],
            f"{item['status']} ({item['age_str']} / {item['threshold_hours']}h threshold)",
            color
        )

    return report

def refresh_all(force=False):
    """Refresh all data sources and merge."""
    print_header(f"NHL Playoff Framework - Data Refresh")
    print(f"Season: {CURRENT_SEASON}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'FORCE' if force else 'Normal'}\n")

    results = {}

    # Step 1: Check/Fetch NHL API
    print_header("Step 1: NHL API Standings", "-")
    success, msg = _run_script("nhl_standings", "fetch_nhl_api.py", force)
    results["nhl_api"] = (success, msg)
    print_status("NHL API", msg, "green" if success else "red")

    # Step 2: Check/Fetch NST
    print_header("Step 2: Natural Stat Trick", "-")
    success, msg = _run_script("nst_stats", "scrape_nst.py", force)
    results["nst"] = (success, msg)
    print_status("NST", msg, "green" if success else "red")

    # Step 3: Fetch odds/probabilities
    print_header("Step 3: Odds & Probabilities", "-")
    success, msg = _run_script("odds", "fetch_odds.py", force)
    results["odds"] = (success, msg)
    print_status("Odds", msg, "green" if success else "red")

    # Step 4: Check MoneyPuck (usually requires browser)
    print_header("Step 4: MoneyPuck", "-")
    success, msg = check_moneypuck_freshness(force)
    results["moneypuck"] = (success, msg)
    color = "green" if success else "yellow"
    print_status("MoneyPuck", msg, color)

    if not success:
        print("\n  ⚠️  MoneyPuck may need browser-based refresh")
        print("     Visit: https://moneypuck.com/teams.htm")

    # Step 5: Merge all data
    print_header("Step 5: Merge Data", "-")
    success, msg = run_merge(force)
    results["merge"] = (success, msg)
    print_status("Merge", msg, "green" if success else "red")

    # Step 6: Validate output
    print_header("Step 6: Validation", "-")
    success, validation_result = validate_output()
    results["validation"] = (success, validation_result)

    if success:
        print_status("Validation", "PASSED", "green")
        print(f"  Teams: {validation_result['team_count']}")
        print(f"  Leader: {validation_result['top_team']}")
        print(f"  Generated: {validation_result['generated_at']}")
    else:
        print_status("Validation", f"FAILED: {validation_result}", "red")

    # Summary
    print_header("Summary")
    all_success = all(r[0] for r in results.values())

    if all_success:
        print("  ✅ All data sources refreshed and merged successfully!")
    else:
        print("  ⚠️  Some issues detected:")
        for source, (success, msg) in results.items():
            if not success:
                print(f"    - {source}: {msg}")

    return all_success, results


def _classify_source_health(source: str, success: bool, message: str, scheduled_break: bool) -> str:
    msg = (message or "").lower()
    if success:
        if "expected-static" in msg:
            return "expected_static"
        if "backup provider" in msg:
            return "healthy"
        return "healthy"

    if "stale" in msg or "missing" in msg:
        return "expected_static" if scheduled_break else "stale"
    if "browser" in msg:
        return "degraded"
    if "failed" in msg or "timeout" in msg or "error" in msg:
        return "down"
    return "degraded"


def _write_refresh_heartbeat(results, run_success: bool) -> None:
    calendar = get_data_activity_context()
    scheduled_break = calendar.get("activityState") == "scheduled_break"
    now_iso = datetime.now(timezone.utc).isoformat()

    source_rows = {}
    critical_sources = {"nhl_api", "nst", "odds"}
    critical_healthy = True
    for source, row in results.items():
        success, message = row
        health = _classify_source_health(source, bool(success), str(message), scheduled_break)
        if source in critical_sources and health not in {"healthy", "expected_static"}:
            critical_healthy = False
        source_rows[source] = {
            "success": bool(success),
            "message": str(message),
            "health": health,
            "critical": source in critical_sources,
            "checkedAt": now_iso,
        }

    heartbeat = {
        "generatedAt": now_iso,
        "season": CURRENT_SEASON,
        "calendarContext": calendar,
        "overall": {
            "refreshSuccess": bool(run_success),
            "criticalHealthy": critical_healthy,
            "activityState": calendar.get("activityState"),
        },
        "sources": source_rows,
    }
    REFRESH_HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REFRESH_HEARTBEAT_PATH.write_text(json.dumps(heartbeat, indent=2) + "\n")
    logger.info(f"Saved refresh heartbeat to {REFRESH_HEARTBEAT_PATH}")

# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Refresh NHL Playoff Framework data from all sources"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force refresh even if data is fresh"
    )
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Just check data freshness, don't fetch"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Just validate existing data"
    )

    args = parser.parse_args()

    if args.check:
        print_freshness_report()
        return 0

    if args.validate:
        print_header("Data Validation")
        success, result = validate_output()
        if success:
            print_status("Validation", "PASSED", "green")
            print(f"\n  {result}")
        else:
            print_status("Validation", "FAILED", "red")
            print(f"\n  {result}")
        return 0 if success else 1

    success, results = refresh_all(force=args.force)
    _write_refresh_heartbeat(results, run_success=success)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
