#!/usr/bin/env python3
"""
Build staged advanced override files for historical seasons.

This script writes to a staging folder so data can be validated against
benchmarks before moving into active override paths.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_DIR = PROJECT_ROOT / "data" / "historical" / "verified"
STAGING_DIR = VERIFIED_DIR / "advanced_staging"
REPORT_PATH = PROJECT_ROOT / "reports" / "advanced_override_staging_report.json"


def _estimate_expected_goal_profile(goals_for: int, goals_against: int, cf_pct: float, hdcf_pct: float):
    xgf_pct_proxy = min(65.0, max(35.0, (0.65 * cf_pct) + (0.35 * hdcf_pct)))
    xgf_proxy = max(0.0, goals_for * (xgf_pct_proxy / 50.0))
    xga_proxy = max(0.0, goals_against * ((100.0 - xgf_pct_proxy) / 50.0))
    return xgf_proxy, xga_proxy, xgf_pct_proxy


def build_staging(start_season: int = 2010, end_season: int = 2024) -> dict:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "startSeason": start_season,
        "endSeason": end_season,
        "seasons": [],
        "totalRows": 0,
    }

    for season in range(start_season, end_season + 1):
        src = VERIFIED_DIR / f"season_{season}.json"
        if not src.exists():
            report["seasons"].append({"season": season, "status": "missing_source", "rows": 0})
            continue

        data = json.loads(src.read_text())
        teams = data.get("teams", {})
        if not teams:
            report["seasons"].append({"season": season, "status": "no_teams", "rows": 0})
            continue

        overrides = {}
        for team, row in teams.items():
            if not isinstance(row, dict):
                continue
            gf = int(row.get("gf") or 0)
            ga = int(row.get("ga") or 0)
            cf_pct = float(row.get("cfPct") or 50.0)
            hdcf_pct = float(row.get("hdcfPct") or 50.0)
            xgf, xga, xgf_pct = _estimate_expected_goal_profile(gf, ga, cf_pct, hdcf_pct)
            overrides[team] = {
                "xgf": round(float(xgf), 3),
                "xga": round(float(xga), 3),
                "xgfPct": round(float(xgf_pct), 3),
            }

        out = STAGING_DIR / f"season_{season}.json"
        out.write_text(json.dumps(overrides, indent=2) + "\n")
        report["seasons"].append({"season": season, "status": "written", "rows": len(overrides)})
        report["totalRows"] += len(overrides)

    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    report = build_staging()
    print(f"Staging files written: {sum(1 for s in report['seasons'] if s['status'] == 'written')}")
    print(f"Total staged rows: {report['totalRows']}")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
