#!/usr/bin/env python3
"""
Import historical Vegas odds CSVs into normalized benchmark files.

Input: one or more CSV files in data/historical/raw/vegas (configurable).
Output: data/historical/verified/vegas_odds_<season>.csv

The normalized output schema is:
team,season,cup_odds_american,cup_implied_prob,playoff_odds_american,playoff_implied_prob,actual_made_playoffs,actual_won_cup
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.config import HISTORICAL_DIR, normalize_team_abbrev
from scripts.config import NST_TEAM_MAP


OUTPUT_FIELDS = [
    "team",
    "season",
    "cup_odds_american",
    "cup_implied_prob",
    "playoff_odds_american",
    "playoff_implied_prob",
    "actual_made_playoffs",
    "actual_won_cup",
]


TEAM_ALIASES = {name.upper(): code for name, code in NST_TEAM_MAP.items()}
TEAM_ALIASES.update(
    {
        "LOS ANGELES KINGS": "LA",
        "SAN JOSE SHARKS": "SJ",
        "NEW JERSEY DEVILS": "NJ",
        "TAMPA BAY LIGHTNING": "TB",
        "ARIZONA COYOTES": "ARI",
        "PHOENIX COYOTES": "PHX",
        "ATLANTA THRASHERS": "ATL",
    }
)


def _norm_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", header.strip().lower()).strip("_")


def _find_field(row: Dict[str, str], candidates: List[str]) -> str:
    for key in candidates:
        if key in row and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def _parse_odds(raw: str) -> Optional[int]:
    if not raw:
        return None
    text = raw.strip().replace("−", "-").replace("—", "-").replace("+", "")
    try:
        value = int(float(text))
    except ValueError:
        return None
    return value if value < 0 else int(f"+{value}")


def _american_to_prob(odds: int) -> float:
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)


def _prob_to_american(prob: float) -> int:
    prob = max(0.0001, min(0.9999, prob))
    if prob < 0.5:
        return int(round(((1.0 - prob) / prob) * 100))
    return int(round(-((prob / (1.0 - prob)) * 100)))


def _parse_prob(raw: str) -> Optional[float]:
    if not raw:
        return None
    text = raw.strip().replace("%", "")
    try:
        value = float(text)
    except ValueError:
        return None
    if value > 1.0:
        value = value / 100.0
    return max(0.0, min(1.0, value))


def _parse_bool(raw: str) -> Optional[bool]:
    text = raw.strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def _infer_season(path: Path, sample_row: Dict[str, str]) -> Optional[int]:
    season_raw = _find_field(sample_row, ["season", "year", "season_year"])
    if season_raw:
        try:
            return int(season_raw)
        except ValueError:
            pass
    match = re.search(r"(20\d{2})", path.stem)
    if match:
        return int(match.group(1))
    return None


def _normalize_team(raw: str) -> Optional[str]:
    if not raw:
        return None
    team = raw.strip().upper()
    if team in TEAM_ALIASES:
        return normalize_team_abbrev(TEAM_ALIASES[team])
    if len(team) in (2, 3, 4):
        return normalize_team_abbrev(team)
    return None


def _load_actuals_from_verified(season: int) -> Dict[str, Dict[str, int]]:
    season_path = HISTORICAL_DIR / f"season_{season}.json"
    if not season_path.exists():
        return {}
    import json

    with open(season_path) as f:
        payload = json.load(f)

    teams_raw = payload.get("teams", {})
    rows = teams_raw.values() if isinstance(teams_raw, dict) else teams_raw
    out: Dict[str, Dict[str, int]] = {}
    for row in rows:
        team = normalize_team_abbrev(str(row.get("team", "")).strip().upper())
        if not team:
            continue
        out[team] = {
            "actual_made_playoffs": 1 if bool(row.get("madePlayoffs", False)) else 0,
            "actual_won_cup": 1 if bool(row.get("wonCup", False)) else 0,
        }
    return out


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        normalized_rows: List[Dict[str, str]] = []
        for raw_row in reader:
            row: Dict[str, str] = {}
            for k, v in raw_row.items():
                if k is None:
                    continue
                row[_norm_header(k)] = "" if v is None else str(v)
            normalized_rows.append(row)
        return normalized_rows


def _convert_rows(rows: List[Dict[str, str]], season: int) -> List[Dict[str, object]]:
    actuals = _load_actuals_from_verified(season)
    normalized: List[Dict[str, object]] = []

    for row in rows:
        team_code = _normalize_team(_find_field(row, ["team", "team_abbrev", "team_code", "abbrev", "tm"]))
        if not team_code:
            continue

        cup_odds = _parse_odds(_find_field(row, ["cup_odds_american", "cup_odds", "cup", "stanley_cup_odds"]))
        playoff_odds = _parse_odds(
            _find_field(row, ["playoff_odds_american", "playoff_odds", "playoffs_odds", "playoff"])
        )
        cup_prob = _parse_prob(_find_field(row, ["cup_implied_prob", "cup_prob", "cup_probability"]))
        playoff_prob = _parse_prob(_find_field(row, ["playoff_implied_prob", "playoff_prob", "playoff_probability"]))
        made = _parse_bool(_find_field(row, ["actual_made_playoffs", "made_playoffs"]))
        won = _parse_bool(_find_field(row, ["actual_won_cup", "won_cup"]))

        if cup_odds is None and cup_prob is None:
            continue
        if playoff_odds is None and playoff_prob is None:
            continue

        if cup_prob is None and cup_odds is not None:
            cup_prob = _american_to_prob(cup_odds)
        if playoff_prob is None and playoff_odds is not None:
            playoff_prob = _american_to_prob(playoff_odds)

        if cup_odds is None and cup_prob is not None:
            cup_odds = _prob_to_american(cup_prob)
        if playoff_odds is None and playoff_prob is not None:
            playoff_odds = _prob_to_american(playoff_prob)

        if made is None:
            made = bool(actuals.get(team_code, {}).get("actual_made_playoffs", 0))
        if won is None:
            won = bool(actuals.get(team_code, {}).get("actual_won_cup", 0))

        normalized.append(
            {
                "team": team_code,
                "season": season,
                "cup_odds_american": cup_odds,
                "cup_implied_prob": round(float(cup_prob), 6),
                "playoff_odds_american": playoff_odds,
                "playoff_implied_prob": round(float(playoff_prob), 6),
                "actual_made_playoffs": 1 if made else 0,
                "actual_won_cup": 1 if won else 0,
            }
        )

    by_team = {str(row["team"]): row for row in normalized}
    return [by_team[t] for t in sorted(by_team.keys())]


def _write_season_file(rows: List[Dict[str, object]], season: int, dry_run: bool) -> None:
    out_path = HISTORICAL_DIR / f"vegas_odds_{season}.csv"
    if dry_run:
        print(f"[DRY RUN] Would write {out_path} with {len(rows)} rows")
        return
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Wrote {out_path} ({len(rows)} rows)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import historical Vegas odds into normalized benchmark files")
    parser.add_argument("--input-dir", default="data/historical/raw/vegas")
    parser.add_argument("--glob", default="*.csv")
    parser.add_argument("--start-season", type=int, default=2010)
    parser.add_argument("--end-season", type=int, default=2025)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    input_dir = PROJECT_ROOT / args.input_dir
    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        return 1

    files = sorted(input_dir.glob(args.glob))
    if not files:
        print(f"No files matched {args.glob} in {input_dir}")
        return 1

    by_season: Dict[int, List[Dict[str, object]]] = {}

    for file_path in files:
        rows = _read_csv(file_path)
        if not rows:
            continue
        season = _infer_season(file_path, rows[0])
        if season is None:
            print(f"Skipping {file_path}: could not infer season")
            continue
        if season < args.start_season or season > args.end_season:
            continue
        normalized = _convert_rows(rows, season)
        if not normalized:
            print(f"Skipping {file_path}: no parseable rows")
            continue
        by_season[season] = normalized

    if not by_season:
        print("No parseable season files found in selected range")
        return 1

    for season in sorted(by_season.keys()):
        _write_season_file(by_season[season], season, dry_run=args.dry_run)

    print(f"Imported seasons: {', '.join(str(s) for s in sorted(by_season.keys()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
