#!/usr/bin/env python3
"""
Data Validation Script for NHL Playoff Prediction Framework
Validates data quality after pipeline runs to prevent silent failures.

Usage: python scripts/validate_data.py
       python scripts/validate_data.py --allow-warnings
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    from league_calendar import get_data_activity_context
except ModuleNotFoundError:  # pragma: no cover - import fallback for direct module loading in tests
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from league_calendar import get_data_activity_context

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
REQUIRED_TEAMS = 32
MAX_DATA_AGE_HOURS = 168  # 7 days
DEFAULT_REFRESH_HEARTBEAT_PATH = REPORTS_DIR / "data_refresh_heartbeat.json"
SCHEDULED_BREAK_ACCEPTABLE_SOURCE_HEALTH = {"healthy", "expected_static"}
CRITICAL_BREAK_SOURCES = {
    "NST": "nst",
    "NHL API": "nhl_api",
    "Odds": "odds",
}

# Expected ranges for key metrics
METRIC_RANGES = {
    "hdcfPct": (35, 65),      # HDCF% should be 35-65%
    "cfPct": (40, 60),        # CF% should be 40-60%
    "pdo": (0.95, 1.05),      # PDO should be 95-105 (or 0.95-1.05)
    "ppPct": (10, 35),        # PP% should be 10-35%
    "pkPct": (70, 95),        # PK% should be 70-95%
    "gsax": (-40, 40),        # GSAx should be -40 to +40 (elite goalies can exceed ±30)
}

def load_json(filepath):
    """Load a JSON file."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return None

def _parse_iso_utc(raw: str) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _load_refresh_heartbeat(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    return load_json(path)


def _heartbeat_age_hours(heartbeat: Optional[Dict[str, Any]]) -> Optional[float]:
    if not heartbeat:
        return None
    generated_at = _parse_iso_utc(str(heartbeat.get("generatedAt", "")))
    if generated_at is None:
        return None
    return (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600.0


def _source_heartbeat_allows_stale(
    source_name: str,
    source_key: Optional[str],
    calendar_context: Dict[str, Any],
    refresh_heartbeat: Optional[Dict[str, Any]],
) -> bool:
    if calendar_context.get("activityState") != "scheduled_break":
        return False
    if not source_key or not refresh_heartbeat:
        return False

    max_age_hours = int(calendar_context.get("heartbeatMaxAgeHours") or 0)
    age_hours = _heartbeat_age_hours(refresh_heartbeat)
    if age_hours is None or age_hours > max_age_hours:
        return False

    source_row = (refresh_heartbeat.get("sources") or {}).get(source_key)
    if not isinstance(source_row, dict):
        return False

    health = str(source_row.get("health", "")).lower()
    return health in SCHEDULED_BREAK_ACCEPTABLE_SOURCE_HEALTH


def _build_scheduled_break_heartbeat_issues(
    calendar_context: Dict[str, Any], refresh_heartbeat: Optional[Dict[str, Any]]
) -> List[str]:
    if calendar_context.get("activityState") != "scheduled_break":
        return []

    issues: List[str] = []
    max_age_hours = int(calendar_context.get("heartbeatMaxAgeHours") or 24)
    window_name = str(calendar_context.get("windowName") or "scheduled break")

    if refresh_heartbeat is None:
        issues.append(
            f"  ⚠️  Refresh heartbeat missing during {window_name} (expected within {max_age_hours}h)"
        )
        return issues

    age_hours = _heartbeat_age_hours(refresh_heartbeat)
    if age_hours is None:
        issues.append(f"  ⚠️  Refresh heartbeat timestamp invalid during {window_name}")
    elif age_hours > max_age_hours:
        issues.append(
            f"  ⚠️  Refresh heartbeat is stale ({age_hours:.1f}h old; max {max_age_hours}h) during {window_name}"
        )

    source_rows = refresh_heartbeat.get("sources") or {}
    for source_name, source_key in CRITICAL_BREAK_SOURCES.items():
        row = source_rows.get(source_key)
        if not isinstance(row, dict):
            issues.append(
                f"  ⚠️  {source_name}: No refresh health row in heartbeat during {window_name}"
            )
            continue
        health = str(row.get("health", "")).lower()
        if health not in SCHEDULED_BREAK_ACCEPTABLE_SOURCE_HEALTH:
            issues.append(
                f"  ⚠️  {source_name}: Refresh health is {health or 'unknown'} during {window_name}"
            )

    return issues


def check_data_freshness(
    metadata: Dict[str, Any],
    source_name: str,
    source_key: Optional[str],
    calendar_context: Dict[str, Any],
    refresh_heartbeat: Optional[Dict[str, Any]],
):
    """Check if data is within acceptable age."""
    issues = []
    fetched_at = metadata.get("fetchedAt", "") or metadata.get("generatedAt", "")

    if not fetched_at:
        issues.append(f"  ⚠️  {source_name}: No fetchedAt timestamp")
        return issues

    try:
        # Parse ISO timestamp
        fetch_time = datetime.fromisoformat(fetched_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        age = datetime.now(timezone.utc) - fetch_time

        if age > timedelta(hours=MAX_DATA_AGE_HOURS):
            if _source_heartbeat_allows_stale(source_name, source_key, calendar_context, refresh_heartbeat):
                window = str(calendar_context.get("windowName") or "scheduled break")
                print(
                    f"  ↷ {source_name}: data age {age.days}d accepted during {window} with healthy refresh heartbeat"
                )
                return issues
            issues.append(f"  ⚠️  {source_name}: Data is {age.days} days old (fetched: {fetched_at[:10]})")
    except Exception as e:
        issues.append(f"  ⚠️  {source_name}: Could not parse timestamp: {fetched_at}")

    return issues

def check_team_count(data, source_name, expected=REQUIRED_TEAMS):
    """Check if all teams are present."""
    issues = []
    teams = data.get("teams", {})
    count = len(teams) if isinstance(teams, dict) else len(teams)

    if count != expected:
        issues.append(f"  ❌ {source_name}: Expected {expected} teams, got {count}")
    else:
        print(f"  ✓ {source_name}: {count} teams")

    return issues

def check_metric_ranges(teams_data, source_name):
    """Check if metrics are within expected ranges."""
    issues = []

    teams = teams_data if isinstance(teams_data, dict) else {t["team"]: t for t in teams_data}

    for metric, (min_val, max_val) in METRIC_RANGES.items():
        all_default = True
        out_of_range = []
        missing = []

        for abbrev, team in teams.items():
            val = team.get(metric)

            if val is None:
                missing.append(abbrev)
                continue

            # Check if value is at default (50 for percentages, 100 for PDO)
            default_val = 50 if "Pct" in metric else (100 if metric == "pdo" else 0)
            if val != default_val:
                all_default = False

            # Check range
            if not (min_val <= val <= max_val):
                out_of_range.append(f"{abbrev}={val}")

        if all_default and metric in ["hdcfPct", "cfPct"]:
            issues.append(f"  ❌ {source_name}: {metric} = default for ALL teams (data not populated)")
        elif len(missing) == REQUIRED_TEAMS:
            pass  # Metric not in this source
        elif out_of_range:
            issues.append(f"  ⚠️  {source_name}: {metric} out of range: {', '.join(out_of_range[:5])}")

    return issues

def validate_nst(calendar_context, refresh_heartbeat):
    """Validate NST stats file."""
    print("\n📊 Validating NST Stats...")
    issues = []

    data = load_json(DATA_DIR / "nst_stats.json")
    if not data:
        issues.append("  ❌ NST: File not found or invalid JSON")
        return issues

    issues.extend(check_data_freshness(data.get("_metadata", {}), "NST", "nst", calendar_context, refresh_heartbeat))
    issues.extend(check_team_count(data, "NST"))
    issues.extend(check_metric_ranges(data.get("teams", {}), "NST"))

    # Specific NST checks
    teams = data.get("teams", {})
    hdcf_values = [t.get("hdcfPct", 50) for t in teams.values()]
    if all(v == 50 for v in hdcf_values):
        issues.append("  ❌ NST: HDCF% is 50.0 for all teams (scraper failed)")
    else:
        print(f"  ✓ NST: HDCF% range: {min(hdcf_values):.1f}% - {max(hdcf_values):.1f}%")

    return issues

def validate_nhl_api(calendar_context, refresh_heartbeat):
    """Validate NHL API standings file."""
    print("\n📊 Validating NHL API Stats...")
    issues = []

    data = load_json(DATA_DIR / "nhl_standings.json")
    if not data:
        issues.append("  ❌ NHL API: File not found or invalid JSON")
        return issues

    issues.extend(check_data_freshness(data.get("_metadata", {}), "NHL API", "nhl_api", calendar_context, refresh_heartbeat))
    issues.extend(check_team_count(data, "NHL API"))

    # Check PP% and PK%
    teams = data.get("teams", {})
    pp_values = [t.get("ppPct", 0) for t in teams.values()]
    pk_values = [t.get("pkPct", 0) for t in teams.values()]

    if all(v == 0 for v in pp_values):
        issues.append("  ❌ NHL API: PP% is 0 for all teams (parsing bug)")
    else:
        print(f"  ✓ NHL API: PP% range: {min(pp_values):.1f}% - {max(pp_values):.1f}%")

    if all(v == 0 for v in pk_values):
        issues.append("  ❌ NHL API: PK% is 0 for all teams (parsing bug)")
    else:
        print(f"  ✓ NHL API: PK% range: {min(pk_values):.1f}% - {max(pk_values):.1f}%")

    return issues

def validate_moneypuck(calendar_context, refresh_heartbeat):
    """Validate MoneyPuck stats file."""
    print("\n📊 Validating MoneyPuck Stats...")
    issues = []

    data = load_json(DATA_DIR / "moneypuck_stats.json")
    if not data:
        issues.append("  ❌ MoneyPuck: File not found or invalid JSON")
        return issues

    issues.extend(
        check_data_freshness(
            data.get("_metadata", {}),
            "MoneyPuck",
            "moneypuck",
            calendar_context,
            refresh_heartbeat,
        )
    )
    issues.extend(check_team_count(data, "MoneyPuck"))

    # Check GSAx
    teams = data.get("teams", {})
    gsax_values = [t.get("gsax", 0) for t in teams.values()]

    if all(v == 0 for v in gsax_values):
        issues.append("  ❌ MoneyPuck: GSAx is 0 for all teams")
    else:
        print(f"  ✓ MoneyPuck: GSAx range: {min(gsax_values):.1f} - {max(gsax_values):.1f}")

    return issues

def validate_merged(calendar_context, refresh_heartbeat):
    """Validate merged teams.json file."""
    print("\n📊 Validating Merged Teams Data...")
    issues = []

    data = load_json(DATA_DIR / "teams.json")
    if not data:
        issues.append("  ❌ Merged: File not found or invalid JSON")
        return issues

    issues.extend(
        check_data_freshness(data.get("_metadata", {}), "Merged", "merge", calendar_context, refresh_heartbeat)
    )

    teams = data.get("teams", [])
    if isinstance(teams, list):
        issues.extend(check_team_count({"teams": {t["team"]: t for t in teams}}, "Merged"))
        issues.extend(check_metric_ranges({t["team"]: t for t in teams}, "Merged"))

    return issues

def _is_warning(issue):
    return issue.strip().startswith("⚠️")


def _is_error(issue):
    return issue.strip().startswith("❌")


def main():
    parser = argparse.ArgumentParser(
        description="Validate NHL data pipeline outputs."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Fail on warnings in addition to errors (default: enabled)."
    )
    parser.add_argument(
        "--allow-warnings",
        dest="strict",
        action="store_false",
        help="Treat warnings as non-fatal for exploratory/local runs."
    )
    parser.add_argument(
        "--break-aware",
        dest="break_aware",
        action="store_true",
        default=True,
        help="Use league-calendar-aware freshness behavior (default: enabled).",
    )
    parser.add_argument(
        "--no-break-aware",
        dest="break_aware",
        action="store_false",
        help="Disable league-calendar-aware freshness behavior.",
    )
    parser.add_argument(
        "--refresh-heartbeat",
        type=Path,
        default=DEFAULT_REFRESH_HEARTBEAT_PATH,
        help=f"Path to refresh heartbeat JSON (default: {DEFAULT_REFRESH_HEARTBEAT_PATH}).",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("NHL Playoff Framework - Data Validation")
    print("=" * 60)

    all_issues: List[str] = []
    if args.break_aware:
        calendar_context = get_data_activity_context()
        refresh_heartbeat = _load_refresh_heartbeat(args.refresh_heartbeat)
        if calendar_context.get("activityState") == "scheduled_break":
            print(
                "ℹ️  Scheduled break mode active:"
                f" {calendar_context.get('windowName')} ({calendar_context.get('windowStart')} to {calendar_context.get('windowEnd')})"
            )
        all_issues.extend(_build_scheduled_break_heartbeat_issues(calendar_context, refresh_heartbeat))
    else:
        calendar_context = {"activityState": "regular_season"}
        refresh_heartbeat = None

    all_issues.extend(validate_nst(calendar_context, refresh_heartbeat))
    all_issues.extend(validate_nhl_api(calendar_context, refresh_heartbeat))
    all_issues.extend(validate_moneypuck(calendar_context, refresh_heartbeat))
    all_issues.extend(validate_merged(calendar_context, refresh_heartbeat))

    print("\n" + "=" * 60)

    fatal_issues = [issue for issue in all_issues if _is_error(issue)]
    warning_issues = [issue for issue in all_issues if _is_warning(issue)]

    should_fail = bool(fatal_issues) or (args.strict and bool(warning_issues))

    if should_fail:
        print(f"❌ VALIDATION FAILED - {len(all_issues)} issue(s) found:\n")
        for issue in all_issues:
            print(issue)
        if warning_issues and not fatal_issues:
            print("\n⚠️  Strict mode treats warnings as failures.")
        else:
            print("\n⚠️  Fix issues before using predictions!")
        sys.exit(1)
    elif warning_issues:
        print(f"⚠️  VALIDATION PASSED WITH WARNINGS - {len(warning_issues)} warning(s):\n")
        for issue in warning_issues:
            print(issue)
        print("\n✅ Core data integrity checks passed.")
        sys.exit(0)
    else:
        print("✅ ALL VALIDATIONS PASSED")
        print("   Data pipeline is healthy. Predictions should be reliable.")
        sys.exit(0)

if __name__ == "__main__":
    main()
