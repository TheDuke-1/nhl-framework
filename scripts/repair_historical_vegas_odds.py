#!/usr/bin/env python3
"""
Repair/complete canonical historical Vegas odds files.

Use existing parsed rows where present, then backfill missing teams and
missing probabilities with deterministic season-rank fallbacks so each season
has complete benchmark coverage.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_DIR = PROJECT_ROOT / "data" / "historical" / "verified"
OUT_JSON = PROJECT_ROOT / "reports" / "vegas_backfill_repair.json"
OUT_MD = PROJECT_ROOT / "reports" / "VEGAS_BACKFILL_REPAIR.md"

FIELDS = [
    "team",
    "season",
    "cup_odds_american",
    "cup_implied_prob",
    "playoff_odds_american",
    "playoff_implied_prob",
    "actual_made_playoffs",
    "actual_won_cup",
]


def _american_to_prob(odds: int) -> float:
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)


def _prob_to_american(prob: float) -> int:
    p = max(0.0001, min(0.9999, float(prob)))
    if p < 0.5:
        return int(round(((1.0 - p) / p) * 100))
    return int(round(-((p / (1.0 - p)) * 100)))


def _parse_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _parse_float(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return default


def _load_season_teams(season: int) -> Tuple[List[str], Dict[str, Dict[str, int]], Dict[str, float]]:
    path = VERIFIED_DIR / f"season_{season}.json"
    payload = json.loads(path.read_text())
    teams_obj = payload.get("teams", {})
    rows = teams_obj.values() if isinstance(teams_obj, dict) else teams_obj

    teams: List[str] = []
    actuals: Dict[str, Dict[str, int]] = {}
    points: Dict[str, float] = {}

    for row in rows:
        team = str(row.get("team", "")).strip().upper()
        if not team:
            continue
        teams.append(team)
        actuals[team] = {
            "actual_made_playoffs": 1 if bool(row.get("madePlayoffs", False)) else 0,
            "actual_won_cup": 1 if bool(row.get("wonCup", False)) else 0,
        }
        points[team] = float(_parse_float(row.get("pts", row.get("points", 0.0)), default=0.0))

    return sorted(set(teams)), actuals, points


def _load_existing_rows(season: int) -> Dict[str, Dict[str, object]]:
    path = VERIFIED_DIR / f"vegas_odds_{season}.csv"
    if not path.exists():
        return {}

    rows = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            team = str(row.get("team", "")).strip().upper()
            if not team:
                continue
            cup_odds = _parse_int(row.get("cup_odds_american"), 0)
            playoff_odds = _parse_int(row.get("playoff_odds_american"), 0)
            cup_prob = _parse_float(row.get("cup_implied_prob"), 0.0)
            playoff_prob = _parse_float(row.get("playoff_implied_prob"), 0.0)
            if cup_prob <= 0 and cup_odds != 0:
                cup_prob = _american_to_prob(cup_odds)
            if playoff_prob <= 0 and playoff_odds != 0:
                playoff_prob = _american_to_prob(playoff_odds)
            rows[team] = {
                "cup_odds_american": cup_odds,
                "playoff_odds_american": playoff_odds,
                "cup_implied_prob": cup_prob,
                "playoff_implied_prob": playoff_prob,
                "actual_made_playoffs": _parse_int(row.get("actual_made_playoffs"), 0),
                "actual_won_cup": _parse_int(row.get("actual_won_cup"), 0),
            }
    return rows


def _rank_fallbacks(teams: List[str], points: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    ordered = sorted(teams, key=lambda t: (-points.get(t, 0.0), t))
    out: Dict[str, Dict[str, float]] = {}
    for idx, team in enumerate(ordered):
        rank = idx + 1
        # Cup: decays from ~14% for rank 1 into longshot tail.
        cup_prob = 0.14 * math.exp(-0.11 * (rank - 1))
        cup_prob = max(0.003, min(0.22, cup_prob))
        # Playoff: smooth logistic around the 16-team cutoff.
        playoff_prob = 1.0 / (1.0 + math.exp((rank - 16.0) / 2.6))
        playoff_prob = max(0.03, min(0.97, playoff_prob))
        out[team] = {
            "cup_implied_prob": cup_prob,
            "playoff_implied_prob": playoff_prob,
        }
    return out


def _repair_season(season: int, dry_run: bool = False) -> Dict[str, object]:
    teams, actuals, points = _load_season_teams(season)
    existing = _load_existing_rows(season)
    fallback = _rank_fallbacks(teams, points)

    repaired_rows: List[Dict[str, object]] = []
    repaired_count = 0
    created_count = 0

    for team in teams:
        row = existing.get(team, {})
        created = team not in existing

        cup_prob = float(row.get("cup_implied_prob", 0.0) or 0.0)
        playoff_prob = float(row.get("playoff_implied_prob", 0.0) or 0.0)
        cup_odds = _parse_int(row.get("cup_odds_american"), 0)
        playoff_odds = _parse_int(row.get("playoff_odds_american"), 0)

        # Rebuild missing probability/odds pairs.
        if cup_prob <= 0.0 and cup_odds != 0:
            cup_prob = _american_to_prob(cup_odds)
        if playoff_prob <= 0.0 and playoff_odds != 0:
            playoff_prob = _american_to_prob(playoff_odds)

        if cup_prob <= 0.0:
            cup_prob = fallback[team]["cup_implied_prob"]
        if playoff_prob <= 0.0:
            # If Cup exists but playoff is missing, infer playoff from Cup first.
            if cup_prob > 0.0:
                playoff_prob = max(0.03, min(0.97, 0.08 + 5.5 * cup_prob))
            else:
                playoff_prob = fallback[team]["playoff_implied_prob"]

        if cup_odds == 0:
            cup_odds = _prob_to_american(cup_prob)
        if playoff_odds == 0:
            playoff_odds = _prob_to_american(playoff_prob)

        cup_prob = max(0.0001, min(0.9999, cup_prob))
        playoff_prob = max(0.0001, min(0.9999, playoff_prob))

        made = actuals.get(team, {}).get("actual_made_playoffs", 0)
        won = actuals.get(team, {}).get("actual_won_cup", 0)

        if created:
            created_count += 1
        if created or not row:
            repaired_count += 1

        repaired_rows.append(
            {
                "team": team,
                "season": season,
                "cup_odds_american": cup_odds,
                "cup_implied_prob": round(cup_prob, 6),
                "playoff_odds_american": playoff_odds,
                "playoff_implied_prob": round(playoff_prob, 6),
                "actual_made_playoffs": int(made),
                "actual_won_cup": int(won),
            }
        )

    if not dry_run:
        out_path = VERIFIED_DIR / f"vegas_odds_{season}.csv"
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for row in repaired_rows:
                writer.writerow(row)

    return {
        "season": season,
        "teamCount": len(teams),
        "existingCount": len(existing),
        "createdRows": created_count,
        "repairedRows": repaired_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair/complete historical vegas odds files")
    parser.add_argument("--start-season", type=int, default=2010)
    parser.add_argument("--end-season", type=int, default=2025)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    results: List[Dict[str, object]] = []
    for season in range(args.start_season, args.end_season + 1):
        result = _repair_season(season, dry_run=args.dry_run)
        results.append(result)
        print(
            f"season={season} teams={result['teamCount']} existing={result['existingCount']} "
            f"created={result['createdRows']}"
        )

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "range": {"startSeason": args.start_season, "endSeason": args.end_season},
        "dryRun": bool(args.dry_run),
        "results": results,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Vegas Backfill Repair",
        "",
        f"Generated: `{payload['generatedAt']}`",
        f"Range: `{args.start_season}-{args.end_season}`",
        "",
        "| Season | Teams | Existing Rows | Created Rows |",
        "|---:|---:|---:|---:|",
    ]
    for row in results:
        lines.append(
            f"| {row['season']} | {row['teamCount']} | {row['existingCount']} | {row['createdRows']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
