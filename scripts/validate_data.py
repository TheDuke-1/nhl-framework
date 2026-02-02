#!/usr/bin/env python3
"""
Data Validation Script for NHL Playoff Prediction Framework
Validates data quality after pipeline runs to prevent silent failures.

Usage: python scripts/validate_data.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
REQUIRED_TEAMS = 32
MAX_DATA_AGE_HOURS = 168  # 7 days

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

def check_data_freshness(metadata, source_name):
    """Check if data is within acceptable age."""
    issues = []
    fetched_at = metadata.get("fetchedAt", "") or metadata.get("generatedAt", "")

    if not fetched_at:
        issues.append(f"  ⚠️  {source_name}: No fetchedAt timestamp")
        return issues

    try:
        # Parse ISO timestamp
        fetch_time = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        age = datetime.now(fetch_time.tzinfo) - fetch_time

        if age > timedelta(hours=MAX_DATA_AGE_HOURS):
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

def validate_nst():
    """Validate NST stats file."""
    print("\n📊 Validating NST Stats...")
    issues = []

    data = load_json(DATA_DIR / "nst_stats.json")
    if not data:
        issues.append("  ❌ NST: File not found or invalid JSON")
        return issues

    issues.extend(check_data_freshness(data.get("_metadata", {}), "NST"))
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

def validate_nhl_api():
    """Validate NHL API standings file."""
    print("\n📊 Validating NHL API Stats...")
    issues = []

    data = load_json(DATA_DIR / "nhl_standings.json")
    if not data:
        issues.append("  ❌ NHL API: File not found or invalid JSON")
        return issues

    issues.extend(check_data_freshness(data.get("_metadata", {}), "NHL API"))
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

def validate_moneypuck():
    """Validate MoneyPuck stats file."""
    print("\n📊 Validating MoneyPuck Stats...")
    issues = []

    data = load_json(DATA_DIR / "moneypuck_stats.json")
    if not data:
        issues.append("  ❌ MoneyPuck: File not found or invalid JSON")
        return issues

    issues.extend(check_data_freshness(data.get("_metadata", {}), "MoneyPuck"))
    issues.extend(check_team_count(data, "MoneyPuck"))

    # Check GSAx
    teams = data.get("teams", {})
    gsax_values = [t.get("gsax", 0) for t in teams.values()]

    if all(v == 0 for v in gsax_values):
        issues.append("  ❌ MoneyPuck: GSAx is 0 for all teams")
    else:
        print(f"  ✓ MoneyPuck: GSAx range: {min(gsax_values):.1f} - {max(gsax_values):.1f}")

    return issues

def validate_merged():
    """Validate merged teams.json file."""
    print("\n📊 Validating Merged Teams Data...")
    issues = []

    data = load_json(DATA_DIR / "teams.json")
    if not data:
        issues.append("  ❌ Merged: File not found or invalid JSON")
        return issues

    issues.extend(check_data_freshness(data.get("_metadata", {}), "Merged"))

    teams = data.get("teams", [])
    if isinstance(teams, list):
        issues.extend(check_team_count({"teams": {t["team"]: t for t in teams}}, "Merged"))
        issues.extend(check_metric_ranges({t["team"]: t for t in teams}, "Merged"))

    return issues

def main():
    print("=" * 60)
    print("NHL Playoff Framework - Data Validation")
    print("=" * 60)

    all_issues = []

    all_issues.extend(validate_nst())
    all_issues.extend(validate_nhl_api())
    all_issues.extend(validate_moneypuck())
    all_issues.extend(validate_merged())

    print("\n" + "=" * 60)

    if all_issues:
        print(f"❌ VALIDATION FAILED - {len(all_issues)} issue(s) found:\n")
        for issue in all_issues:
            print(issue)
        print("\n⚠️  Fix issues before using predictions!")
        sys.exit(1)
    else:
        print("✅ ALL VALIDATIONS PASSED")
        print("   Data pipeline is healthy. Predictions should be reliable.")
        sys.exit(0)

if __name__ == "__main__":
    main()
