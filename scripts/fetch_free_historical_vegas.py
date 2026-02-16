#!/usr/bin/env python3
"""
Fetch one-time historical NHL Vegas-style futures from free public archives.

Primary free source:
- Covers / SportsOddsHistory archival pages
  - Cup futures by season: nhl-main/?a=sc&sa=nhl&y=YYYY-YYYY
  - Make/Miss playoffs by season: nhl-win/?sa=nhl&t=post&y=YYYY-YYYY

Outputs canonical files expected by this repo:
- data/historical/verified/vegas_odds_<season>.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config import NST_TEAM_MAP
from superhuman.config import HISTORICAL_DIR, normalize_team_abbrev


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36"
}

ODDS_RE = re.compile(r"([+\-−]\d{2,6}|EVEN)")


@dataclass
class TeamRow:
    team: str
    cup_odds_american: int
    playoff_odds_american: int
    actual_made_playoffs: int
    actual_won_cup: int


def american_to_probability(odds: int) -> float:
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)


def parse_odds_token(token: str) -> Optional[int]:
    token = token.strip().replace("−", "-").upper()
    if not token:
        return None
    if token == "EVEN":
        return 100
    if token.startswith("+") or token.startswith("-"):
        try:
            return int(token)
        except ValueError:
            return None
    try:
        value = int(token)
        return value if value < 0 else int(f"+{value}")
    except ValueError:
        return None


def normalize_team_name(raw: str) -> Optional[str]:
    text = raw.strip()
    if not text:
        return None

    # Direct match via known full-name map.
    if text in NST_TEAM_MAP:
        return normalize_team_abbrev(NST_TEAM_MAP[text])

    # Common normalization.
    key = text.replace(".", "").replace("  ", " ").strip().lower()
    for full_name, abbrev in NST_TEAM_MAP.items():
        k2 = full_name.replace(".", "").replace("  ", " ").strip().lower()
        if key == k2:
            return normalize_team_abbrev(abbrev)

    # Already an abbreviation.
    if 2 <= len(text) <= 4 and text.upper().isalpha():
        return normalize_team_abbrev(text.upper())

    return None


def fetch_html(url: str, timeout: int = 30) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text


def find_table_rows_with_links(soup: BeautifulSoup) -> List[List[str]]:
    rows: List[List[str]] = []
    for tr in soup.find_all("tr"):
        links = tr.find_all("a")
        if not links:
            continue
        # first link in row is team for the target tables
        team = links[0].get_text(" ", strip=True)
        tds = tr.find_all("td")
        if not tds:
            continue
        vals = [td.get_text(" ", strip=True) for td in tds]
        if not vals:
            continue
        rows.append([team] + vals)
    return rows


def fetch_cup_preseason_odds(season_label: str) -> Dict[str, int]:
    url = f"https://www.covers.com/sportsoddshistory/nhl-main/?a=sc&sa=nhl&y={season_label}"
    soup = BeautifulSoup(fetch_html(url), "html.parser")

    result: Dict[str, int] = {}
    for row in find_table_rows_with_links(soup):
        team_name = row[0]
        team = normalize_team_name(team_name)
        if not team:
            continue
        row_text = " ".join(row[1:])
        tokens = ODDS_RE.findall(row_text)
        if not tokens:
            continue
        # First listed odds correspond to earliest preseason checkpoint.
        odds = parse_odds_token(tokens[0])
        if odds is None:
            continue
        result[team] = odds

    return result


def fetch_make_miss_playoff_odds(season_label: str) -> Dict[str, tuple[int, int]]:
    url = f"https://www.covers.com/sportsoddshistory/nhl-win/?sa=nhl&t=post&y={season_label}"
    soup = BeautifulSoup(fetch_html(url), "html.parser")

    result: Dict[str, tuple[int, int]] = {}
    for tr in soup.find_all("tr"):
        team_link = tr.find("a")
        tds = tr.find_all("td")
        if not team_link or len(tds) < 4:
            continue

        team = normalize_team_name(team_link.get_text(" ", strip=True))
        if not team:
            continue

        make_txt = tds[1].get_text(" ", strip=True)
        miss_txt = tds[2].get_text(" ", strip=True)
        result_txt = tds[3].get_text(" ", strip=True).upper()

        make_odds = parse_odds_token(make_txt)
        miss_odds = parse_odds_token(miss_txt)
        if make_odds is None or miss_odds is None:
            # fallback: parse by regex in concatenated row
            joined = " ".join(td.get_text(" ", strip=True) for td in tds)
            toks = [parse_odds_token(x) for x in ODDS_RE.findall(joined)]
            toks = [x for x in toks if x is not None]
            if len(toks) >= 2:
                make_odds, miss_odds = toks[0], toks[1]
            else:
                continue

        made = 1 if "MAKE" in result_txt else 0
        result[team] = (make_odds, made)

    return result


def load_cup_winner_map(season: int) -> Dict[str, int]:
    season_file = HISTORICAL_DIR / f"season_{season}.json"
    if not season_file.exists():
        return {}
    payload = json.loads(season_file.read_text())
    teams = payload.get("teams", {})
    rows = teams.values() if isinstance(teams, dict) else teams
    out: Dict[str, int] = {}
    for row in rows:
        team = normalize_team_abbrev(str(row.get("team", "")).strip().upper())
        if not team:
            continue
        out[team] = 1 if bool(row.get("wonCup", False)) else 0
    return out


def build_season(season: int, dry_run: bool = False) -> Dict[str, int]:
    season_label = f"{season-1}-{season}"

    cup_odds = fetch_cup_preseason_odds(season_label)
    playoff_odds = fetch_make_miss_playoff_odds(season_label)
    winners = load_cup_winner_map(season)

    common_teams = sorted(set(cup_odds.keys()).intersection(playoff_odds.keys()))
    rows: List[Dict[str, object]] = []

    for team in common_teams:
        cup = cup_odds[team]
        make_odds, made = playoff_odds[team]
        rows.append(
            {
                "team": team,
                "season": season,
                "cup_odds_american": cup,
                "cup_implied_prob": round(american_to_probability(cup), 6),
                "playoff_odds_american": make_odds,
                "playoff_implied_prob": round(american_to_probability(make_odds), 6),
                "actual_made_playoffs": int(made),
                "actual_won_cup": int(winners.get(team, 0)),
            }
        )

    out_path = HISTORICAL_DIR / f"vegas_odds_{season}.csv"
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "team",
                    "season",
                    "cup_odds_american",
                    "cup_implied_prob",
                    "playoff_odds_american",
                    "playoff_implied_prob",
                    "actual_made_playoffs",
                    "actual_won_cup",
                ],
            )
            w.writeheader()
            for row in rows:
                w.writerow(row)

    return {
        "season": season,
        "season_label": season_label,
        "teams_written": len(rows),
        "out_path": str(out_path),
        "cup_only_count": len(cup_odds),
        "playoff_only_count": len(playoff_odds),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch free historical NHL futures odds and write canonical vegas files")
    parser.add_argument("--start-season", type=int, default=2010)
    parser.add_argument("--end-season", type=int, default=2025)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    reports = []
    for season in range(args.start_season, args.end_season + 1):
        try:
            rep = build_season(season, dry_run=args.dry_run)
            reports.append(rep)
            print(f"season={season} teams={rep['teams_written']} path={rep['out_path']}")
        except Exception as e:
            print(f"season={season} ERROR: {e}")

    report_path = PROJECT_ROOT / "reports" / "phase_vegas_free_source_backfill.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"generatedAt": datetime.now(timezone.utc).isoformat(), "reports": reports}, indent=2) + "\n")
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
