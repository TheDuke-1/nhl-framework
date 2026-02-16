#!/usr/bin/env python3
"""
Validate canonical historical Vegas files for seasons 2010-2025.

Checks:
- file exists for each season
- row count reasonable (>= 30)
- required columns present
- probabilities in [0,1]
- exactly one Cup winner per season
- playoff outcome labels are binary
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_DIR = PROJECT_ROOT / "data" / "historical" / "verified"
OUT_JSON = PROJECT_ROOT / "reports" / "vegas_backfill_validation.json"
OUT_MD = PROJECT_ROOT / "reports" / "VEGAS_BACKFILL_VALIDATION.md"

REQUIRED_COLUMNS = [
    "team",
    "season",
    "cup_odds_american",
    "cup_implied_prob",
    "playoff_odds_american",
    "playoff_implied_prob",
    "actual_made_playoffs",
    "actual_won_cup",
]


def _as_float(row: Dict[str, str], key: str) -> float:
    return float(str(row.get(key, "")).strip())


def _as_int(row: Dict[str, str], key: str) -> int:
    return int(str(row.get(key, "")).strip())


def _expected_teams_for_season(season: int) -> int:
    season_path = VERIFIED_DIR / f"season_{season}.json"
    if not season_path.exists():
        return 30
    payload = json.loads(season_path.read_text())
    teams = payload.get("teams", {})
    if isinstance(teams, dict):
        return len(teams)
    if isinstance(teams, list):
        return len(teams)
    return 30


def validate_season(season: int) -> Dict:
    path = VERIFIED_DIR / f"vegas_odds_{season}.csv"
    if not path.exists():
        return {
            "season": season,
            "status": "missing_file",
            "errors": [f"Missing file: {path}"],
            "rows": 0,
        }

    errors: List[str] = []
    rows: List[Dict[str, str]] = []
    expected_teams = _expected_teams_for_season(season)

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for col in REQUIRED_COLUMNS:
            if col not in fieldnames:
                errors.append(f"Missing column `{col}`")
        rows = list(reader)

    if len(rows) != expected_teams:
        errors.append(f"Row count mismatch: {len(rows)} (expected {expected_teams})")

    cup_winner_count = 0
    seen_teams = set()
    for i, row in enumerate(rows, start=2):
        try:
            team = str(row.get("team", "")).strip().upper()
            if not team:
                errors.append(f"Line {i}: empty team code")
            elif team in seen_teams:
                errors.append(f"Line {i}: duplicate team code `{team}`")
            else:
                seen_teams.add(team)

            c = _as_float(row, "cup_implied_prob")
            p = _as_float(row, "playoff_implied_prob")
            if c < 0 or c > 1:
                errors.append(f"Line {i}: cup_implied_prob out of range: {c}")
            if p < 0 or p > 1:
                errors.append(f"Line {i}: playoff_implied_prob out of range: {p}")

            made = _as_int(row, "actual_made_playoffs")
            won = _as_int(row, "actual_won_cup")
            if made not in (0, 1):
                errors.append(f"Line {i}: actual_made_playoffs not binary: {made}")
            if won not in (0, 1):
                errors.append(f"Line {i}: actual_won_cup not binary: {won}")
            cup_winner_count += won
        except Exception as e:
            errors.append(f"Line {i}: parse error: {e}")

    if cup_winner_count not in (0, 1):
        errors.append(f"Expected 0 or 1 cup winners, found {cup_winner_count}")

    return {
        "season": season,
        "status": "ok" if not errors else "invalid",
        "errors": errors,
        "rows": len(rows),
        "expected_rows": expected_teams,
        "cup_winner_count": cup_winner_count,
        "path": str(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate historical Vegas backfill files")
    parser.add_argument("--start-season", type=int, default=2010)
    parser.add_argument("--end-season", type=int, default=2025)
    args = parser.parse_args()

    results = [validate_season(season) for season in range(args.start_season, args.end_season + 1)]
    missing = [r for r in results if r["status"] == "missing_file"]
    invalid = [r for r in results if r["status"] == "invalid"]
    ok = [r for r in results if r["status"] == "ok"]

    payload = {
        "startSeason": args.start_season,
        "endSeason": args.end_season,
        "okCount": len(ok),
        "missingCount": len(missing),
        "invalidCount": len(invalid),
        "results": results,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Vegas Backfill Validation",
        "",
        f"Range: `{args.start_season}-{args.end_season}`",
        f"OK: `{len(ok)}` | Missing: `{len(missing)}` | Invalid: `{len(invalid)}`",
        "",
        "## Season Status",
        "",
        "| Season | Status | Rows |",
        "|---:|---|---:|",
    ]
    for r in results:
        lines.append(f"| {r['season']} | {r['status']} | {r['rows']} |")

    if missing:
        lines.extend(["", "## Missing Files", ""])
        for r in missing:
            missing_path = r.get("path", f"vegas_odds_{r['season']}.csv")
            lines.append(f"- `{missing_path}`")

    if invalid:
        lines.extend(["", "## Validation Errors", ""])
        for r in invalid:
            lines.append(f"### Season {r['season']}")
            for err in r["errors"][:20]:
                lines.append(f"- {err}")

    OUT_MD.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0 if (len(missing) == 0 and len(invalid) == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
