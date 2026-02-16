#!/usr/bin/env python3
"""
Phase 4: generate backlog datapoint templates per historical season.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_DIR = PROJECT_ROOT / "data" / "historical" / "verified"
OUT_DIR = VERIFIED_DIR / "backlog"

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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    season_files = sorted(VERIFIED_DIR.glob("season_*.json"))
    generated = 0

    for sf in season_files:
        season = sf.stem.split("_")[1]
        with open(sf) as f:
            payload = json.load(f)
        teams = payload.get("teams", {})
        out_path = OUT_DIR / f"season_{season}.json"

        if out_path.exists():
            # Preserve existing values.
            continue

        template = {
            "_metadata": {
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "season": int(season),
                "type": "backlog_feature_template",
                "notes": "Populate values as data sources become available. Null means not integrated yet.",
            },
            "teams": {},
        }
        for team_code in sorted(teams.keys()):
            template["teams"][team_code] = {field: None for field in FIELDS}

        with open(out_path, "w") as f:
            json.dump(template, f, indent=2)
        generated += 1

    print(f"Generated {generated} backlog templates in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
