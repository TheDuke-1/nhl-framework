#!/usr/bin/env python3
"""
Phase 4: audit backlog datapoint coverage across historical seasons.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKLOG_DIR = PROJECT_ROOT / "data" / "historical" / "verified" / "backlog"
OUT_JSON = PROJECT_ROOT / "reports" / "phase4_backlog_coverage.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE4_BACKLOG_COVERAGE.md"

FIELDS = [
    "goalie_usage_starter_load",
    "goalie_backup_dropoff",
    "injury_adjusted_strength",
    "score_state_adjusted_5v5_close_game",
    "schedule_travel_rest_load",
    "discipline_taken_drawn_split",
    "trade_deadline_roster_delta",
    "playoff_style_netfront_rush_forecheck",
    "coach_system_continuity",
]


def main() -> int:
    season_files = sorted(BACKLOG_DIR.glob("season_*.json"))
    if not season_files:
        raise SystemExit(f"No backlog files found in {BACKLOG_DIR}")

    field_counts = {f: {"filled": 0, "total": 0} for f in FIELDS}
    season_rows = []
    for sf in season_files:
        season = int(sf.stem.split("_")[1])
        with open(sf) as f:
            payload = json.load(f)
        teams = payload.get("teams", {})
        team_count = len(teams)

        season_cov = {}
        for field in FIELDS:
            filled = 0
            total = 0
            for _, vals in teams.items():
                total += 1
                if vals.get(field) is not None:
                    filled += 1
            field_counts[field]["filled"] += filled
            field_counts[field]["total"] += total
            season_cov[field] = round((filled / total) if total else 0.0, 3)

        season_rows.append(
            {
                "season": season,
                "teams": team_count,
                "fieldCoverage": season_cov,
            }
        )

    overall = {}
    for field, counts in field_counts.items():
        overall[field] = round((counts["filled"] / counts["total"]) if counts["total"] else 0.0, 3)

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "phase4_backlog_coverage",
        "seasonsAudited": len(season_rows),
        "overallCoverage": overall,
        "seasonCoverage": season_rows,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 4 Backlog Coverage",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"Seasons Audited: `{report['seasonsAudited']}`",
        "",
        "## Overall Coverage",
        "",
        "| Datapoint | Coverage |",
        "|---|---:|",
    ]
    for field, cov in overall.items():
        lines.append(f"| {field} | {cov:.3f} |")

    lines += [
        "",
        "## Season Coverage Snapshot",
        "",
        "| Season | Teams | Mean Coverage |",
        "|---:|---:|---:|",
    ]
    for row in season_rows:
        vals = list(row["fieldCoverage"].values())
        mean_cov = sum(vals) / len(vals) if vals else 0.0
        lines.append(f"| {row['season']} | {row['teams']} | {mean_cov:.3f} |")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
