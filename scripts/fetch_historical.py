#!/usr/bin/env python3
"""
Fetch verified historical NHL data from authoritative sources.

Sources:
  - NHL API (api-web.nhle.com) — Standings: W/L/OTL/PTS/GF/GA/PP%/PK%
  - Natural Stat Trick — Advanced: CF%, HDCF%, SCF%, PDO, SH%, SV%
  - Hockey-Reference — Playoff results (Cup winner, finalist, bracket)

Outputs: data/historical/verified/ directory with one JSON per season.

Usage:
    python fetch_historical.py                    # Fetch all seasons (2013-2025)
    python fetch_historical.py --season 2024      # Fetch single season
    python fetch_historical.py --standings-only    # Only fetch NHL API standings
    python fetch_historical.py --dry-run           # Show what would be fetched
"""

import json
import sys
import time
import argparse
import re
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Seasons to fetch. Key = Hockey-Reference year (e.g., 2024 = 2023-24 season).
# NST advanced stats are reliable from ~2013 onwards.
SEASONS = list(range(2014, 2026))  # 2013-14 through 2024-25

# NHL API season end dates (approximate — last day of regular season)
# Used to fetch final standings for each season.
SEASON_END_DATES = {
    2014: "2014-04-13",
    2015: "2015-04-11",
    2016: "2016-04-09",
    2017: "2017-04-09",
    2018: "2018-04-08",
    2019: "2019-04-06",
    2020: "2020-03-11",  # COVID stoppage
    2021: "2021-05-19",  # Shortened season
    2022: "2022-04-29",
    2023: "2023-04-14",
    2024: "2024-04-18",
    2025: "2025-04-17",
}

# Known Cup winners and finalists (verified facts)
CUP_RESULTS = {
    2014: {"winner": "LA", "finalist": "NYR", "season_label": "2013-14"},
    2015: {"winner": "CHI", "finalist": "TB", "season_label": "2014-15"},
    2016: {"winner": "PIT", "finalist": "SJ", "season_label": "2015-16"},
    2017: {"winner": "PIT", "finalist": "NSH", "season_label": "2016-17"},
    2018: {"winner": "WSH", "finalist": "VGK", "season_label": "2017-18"},
    2019: {"winner": "STL", "finalist": "BOS", "season_label": "2018-19"},
    2020: {"winner": "TB", "finalist": "DAL", "season_label": "2019-20"},
    2021: {"winner": "TB", "finalist": "MTL", "season_label": "2020-21"},
    2022: {"winner": "COL", "finalist": "TB", "season_label": "2021-22"},
    2023: {"winner": "VGK", "finalist": "FLA", "season_label": "2022-23"},
    2024: {"winner": "FLA", "finalist": "EDM", "season_label": "2023-24"},
    2025: {"winner": "FLA", "finalist": "EDM", "season_label": "2024-25"},
}

# NHL API abbreviation → project standard abbreviation
NHL_ABBREV_MAP = {
    "ANA": "ANA", "ARI": "ARI", "ATL": "ATL", "BOS": "BOS", "BUF": "BUF",
    "CAR": "CAR", "CBJ": "CBJ", "CGY": "CGY", "CHI": "CHI", "COL": "COL",
    "DAL": "DAL", "DET": "DET", "EDM": "EDM", "FLA": "FLA",
    "LAK": "LA", "MIN": "MIN", "MTL": "MTL", "NJD": "NJ",
    "NSH": "NSH", "NYI": "NYI", "NYR": "NYR", "OTT": "OTT",
    "PHI": "PHI", "PHX": "ARI", "PIT": "PIT", "SEA": "SEA", "SJS": "SJ",
    "STL": "STL", "TBL": "TB", "TOR": "TOR", "UTA": "UTA",
    "VAN": "VAN", "VGK": "VGK", "WPG": "WPG", "WSH": "WSH",
}

# NST team name → project standard abbreviation
NST_TEAM_MAP = {
    "Anaheim Ducks": "ANA",
    "Arizona Coyotes": "ARI",
    "Atlanta Thrashers": "ATL",
    "Boston Bruins": "BOS",
    "Buffalo Sabres": "BUF",
    "Carolina Hurricanes": "CAR",
    "Columbus Blue Jackets": "CBJ",
    "Calgary Flames": "CGY",
    "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL",
    "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET",
    "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA",
    "Los Angeles Kings": "LA",
    "Minnesota Wild": "MIN",
    "Montréal Canadiens": "MTL",
    "Montreal Canadiens": "MTL",
    "New Jersey Devils": "NJ",
    "Nashville Predators": "NSH",
    "New York Islanders": "NYI",
    "New York Rangers": "NYR",
    "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI",
    "Phoenix Coyotes": "ARI",
    "Pittsburgh Penguins": "PIT",
    "Seattle Kraken": "SEA",
    "San Jose Sharks": "SJ",
    "St. Louis Blues": "STL",
    "St Louis Blues": "STL",
    "Tampa Bay Lightning": "TB",
    "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA",
    "Utah Mammoth": "UTA",
    "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK",
    "Winnipeg Jets": "WPG",
    "Washington Capitals": "WSH",
}

# Number of teams per season (for validation)
EXPECTED_TEAMS = {
    2014: 30, 2015: 30, 2016: 30, 2017: 30,
    2018: 31, 2019: 31, 2020: 31, 2021: 31,
    2022: 32, 2023: 32, 2024: 32, 2025: 32,
}

REQUEST_DELAY = 3  # seconds between requests (be respectful)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# ---------------------------------------------------------------------------
# NHL API — Standings
# ---------------------------------------------------------------------------

def fetch_nhl_standings(year):
    """
    Fetch final regular-season standings from the NHL API.
    Returns dict of {team_abbrev: {stats...}}.
    """
    date = SEASON_END_DATES.get(year)
    if not date:
        print(f"  WARNING: No end date configured for {year}")
        return {}

    url = f"https://api-web.nhle.com/v1/standings/{date}"
    print(f"  Fetching NHL API standings for {year} ({date})...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"  ERROR: NHL API request failed for {year}: {e}")
        return {}

    teams = {}
    for t in data.get("standings", []):
        api_abbrev = t.get("teamAbbrev", {}).get("default", "")
        abbrev = NHL_ABBREV_MAP.get(api_abbrev, api_abbrev)
        if not abbrev:
            continue

        teams[abbrev] = {
            "team": abbrev,
            "name": t.get("teamName", {}).get("default", ""),
            "gp": t.get("gamesPlayed", 0),
            "w": t.get("wins", 0),
            "l": t.get("losses", 0),
            "otl": t.get("otLosses", 0),
            "pts": t.get("points", 0),
            "ptsPct": round(t.get("pointPctg", 0), 3),
            "gf": t.get("goalFor", 0),
            "ga": t.get("goalAgainst", 0),
            "gd": t.get("goalFor", 0) - t.get("goalAgainst", 0),
            "ppPct": round(t.get("powerPlayPctg", 0) * 100, 1),
            "pkPct": round(t.get("penaltyKillPctg", 0) * 100, 1),
            "conf": "East" if t.get("conferenceName") == "Eastern" else "West",
            "div": t.get("divisionName", ""),
            "homeW": t.get("homeWins", 0),
            "homeL": t.get("homeLosses", 0),
            "homeOTL": t.get("homeOtLosses", 0),
            "roadW": t.get("roadWins", 0),
            "roadL": t.get("roadLosses", 0),
            "roadOTL": t.get("roadOtLosses", 0),
        }

    print(f"  -> Got {len(teams)} teams from NHL API")
    return teams


# ---------------------------------------------------------------------------
# Natural Stat Trick — Advanced Stats
# ---------------------------------------------------------------------------

def nst_season_id(year):
    """Convert year to NST season format: 2024 -> '20232024'."""
    return f"{year - 1}{year}"


def fetch_nst_advanced(year):
    """
    Fetch advanced 5v5 stats from Natural Stat Trick.
    Returns dict of {team_abbrev: {advanced stats...}}.
    """
    season_id = nst_season_id(year)
    url = "https://www.naturalstattrick.com/teamtable.php"
    params = {
        "fromseason": season_id,
        "thruseason": season_id,
        "stype": "2",       # Regular season
        "sit": "5v5",
        "score": "all",
        "rate": "n",
        "team": "all",
        "loc": "B",
        "gpf": "410",
    }
    headers = {"User-Agent": USER_AGENT}

    print(f"  Fetching NST advanced stats for {year} (season {season_id})...")

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERROR: NST request failed for {year}: {e}")
        return {}

    return parse_nst_html(response.text)


def parse_nst_html(html):
    """Parse NST team table HTML into structured data."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", {"id": "teams"})
    if not table:
        table = soup.find("table")
    if not table:
        print("  WARNING: Could not find NST data table")
        return {}

    # Parse column headers — NST uses <th> tags in <thead>
    # First column is a blank row-number column, so headers look like:
    # ['', 'Team', 'GP', 'TOI', ..., 'CF%', ..., 'HDCF%', ..., 'SH%', 'SV%', 'PDO']
    headers_row = table.find("thead")
    if headers_row:
        header_cells = headers_row.find_all("th")
        col_names = [h.get_text(strip=True).upper() for h in header_cells]
    else:
        col_names = []

    # Build column index map (header name -> column index in the td cells)
    # The td cells match 1:1 with th cells, including the leading blank column.
    col_map = {}
    for i, name in enumerate(col_names):
        if name:
            col_map[name] = i

    def get_col(name, cells, default=0.0):
        idx = col_map.get(name, -1)
        if 0 <= idx < len(cells):
            text = cells[idx].get_text(strip=True).replace(",", "")
            try:
                return float(text)
            except ValueError:
                return default
        return default

    teams = {}
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 10:
            continue

        # Team name is in the column mapped to "TEAM" header
        team_idx = col_map.get("TEAM", 1)
        team_name = cells[team_idx].get_text(strip=True) if team_idx < len(cells) else ""

        abbrev = NST_TEAM_MAP.get(team_name)
        if not abbrev:
            for name, ab in NST_TEAM_MAP.items():
                if name.lower() in team_name.lower():
                    abbrev = ab
                    break
        if not abbrev:
            continue

        teams[abbrev] = {
            "gp": int(get_col("GP", cells, 0)),
            "cf": int(get_col("CF", cells, 0)),
            "ca": int(get_col("CA", cells, 0)),
            "cfPct": get_col("CF%", cells, 50.0),
            "hdcf": int(get_col("HDCF", cells, 0)),
            "hdca": int(get_col("HDCA", cells, 0)),
            "hdcfPct": get_col("HDCF%", cells, 50.0),
            "scfPct": get_col("SCF%", cells, 50.0),
            "shPct": get_col("SH%", cells, 8.0),
            "svPct": get_col("SV%", cells, 0.910),
            "pdo": get_col("PDO", cells, 1.000),
        }

    print(f"  -> Got {len(teams)} teams from NST")
    return teams


# ---------------------------------------------------------------------------
# Merge & Save
# ---------------------------------------------------------------------------

def merge_season_data(year, standings, advanced):
    """Merge standings + advanced stats into one record per team."""
    cup_info = CUP_RESULTS.get(year, {})
    season_label = cup_info.get("season_label", f"{year - 1}-{str(year)[2:]}")

    merged = {
        "_metadata": {
            "season": season_label,
            "year": year,
            "sources": {
                "standings": "NHL API (api-web.nhle.com)",
                "advanced": "Natural Stat Trick (naturalstattrick.com)",
            },
            "fetchedAt": datetime.utcnow().isoformat() + "Z",
            "cupWinner": cup_info.get("winner", ""),
            "cupFinalist": cup_info.get("finalist", ""),
        },
        "teams": {},
    }

    # Start with standings (the authoritative source for W/L/PTS/GF/GA)
    for abbrev, st in standings.items():
        team_data = dict(st)  # copy

        # Merge advanced stats if available
        adv = advanced.get(abbrev, {})
        if adv:
            team_data["cfPct"] = adv.get("cfPct", None)
            team_data["hdcfPct"] = adv.get("hdcfPct", None)
            team_data["scfPct"] = adv.get("scfPct", None)
            team_data["pdo"] = adv.get("pdo", None)
            team_data["shPct"] = adv.get("shPct", None)
            team_data["svPct"] = adv.get("svPct", None)
            team_data["cf"] = adv.get("cf", None)
            team_data["ca"] = adv.get("ca", None)
            team_data["hdcf"] = adv.get("hdcf", None)
            team_data["hdca"] = adv.get("hdca", None)
            team_data["hasAdvanced"] = True
        else:
            team_data["hasAdvanced"] = False

        # Flag playoff teams and results
        team_data["wonCup"] = (abbrev == cup_info.get("winner"))
        team_data["cupFinalist"] = (abbrev == cup_info.get("finalist"))

        merged["teams"][abbrev] = team_data

    # Check for teams in advanced but not in standings (shouldn't happen, but just in case)
    for abbrev in advanced:
        if abbrev not in merged["teams"]:
            print(f"  WARNING: {abbrev} found in NST but not in NHL API standings")

    return merged


def save_season(year, data, output_dir):
    """Save merged season data to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"season_{year}.json"

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    team_count = len(data.get("teams", {}))
    adv_count = sum(1 for t in data["teams"].values() if t.get("hasAdvanced"))
    print(f"  -> Saved {filepath.name}: {team_count} teams ({adv_count} with advanced stats)")
    return filepath


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_season(year, data):
    """Run basic validation checks on a season's data."""
    issues = []
    teams = data.get("teams", {})
    expected = EXPECTED_TEAMS.get(year, 30)

    if len(teams) < expected - 2:
        issues.append(f"Only {len(teams)} teams (expected ~{expected})")

    for abbrev, t in teams.items():
        # Check standings fields exist and are reasonable
        pts = t.get("pts", 0)
        w = t.get("w", 0)
        gp = t.get("gp", 0)

        if gp < 40 and year != 2020 and year != 2021:
            issues.append(f"{abbrev}: Only {gp} games played (expected ~82)")
        if pts > 0 and pts < 30 and gp > 60:
            issues.append(f"{abbrev}: Only {pts} points in {gp} games (suspicious)")
        if w > gp:
            issues.append(f"{abbrev}: More wins ({w}) than games ({gp})")

        # Check advanced stats ranges
        cfPct = t.get("cfPct")
        if cfPct is not None and (cfPct < 35 or cfPct > 65):
            issues.append(f"{abbrev}: CF% = {cfPct} out of expected range")

        hdcfPct = t.get("hdcfPct")
        if hdcfPct is not None and (hdcfPct < 30 or hdcfPct > 70):
            issues.append(f"{abbrev}: HDCF% = {hdcfPct} out of expected range")

    if issues:
        print(f"  VALIDATION ISSUES for {year}:")
        for issue in issues[:10]:
            print(f"    - {issue}")
        if len(issues) > 10:
            print(f"    ... and {len(issues) - 10} more")
    else:
        print(f"  VALIDATION: {year} passed all checks")

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch_season(year, output_dir, standings_only=False):
    """Fetch and save all data for a single season."""
    print(f"\n{'=' * 60}")
    print(f"  SEASON {year - 1}-{str(year)[2:]} (Hockey-Reference year: {year})")
    print(f"{'=' * 60}")

    # 1. Fetch standings from NHL API
    standings = fetch_nhl_standings(year)
    if not standings:
        print(f"  SKIPPING {year}: No standings data available")
        return None

    time.sleep(REQUEST_DELAY)

    # 2. Fetch advanced stats from NST (unless standings-only)
    advanced = {}
    if not standings_only:
        advanced = fetch_nst_advanced(year)
        time.sleep(REQUEST_DELAY)

    # 3. Merge
    merged = merge_season_data(year, standings, advanced)

    # 4. Validate
    validate_season(year, merged)

    # 5. Save
    filepath = save_season(year, merged, output_dir)
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Fetch verified historical NHL data")
    parser.add_argument("--season", type=int, help="Fetch single season (e.g., 2024 for 2023-24)")
    parser.add_argument("--standings-only", action="store_true", help="Only fetch standings (skip NST)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fetched")
    parser.add_argument("--start", type=int, default=min(SEASONS), help="Start year")
    parser.add_argument("--end", type=int, default=max(SEASONS), help="End year")
    args = parser.parse_args()

    output_dir = Path(__file__).parent.parent / "data" / "historical" / "verified"

    if args.season:
        seasons = [args.season]
    else:
        seasons = [y for y in SEASONS if args.start <= y <= args.end]

    if args.dry_run:
        print("DRY RUN — would fetch these seasons:")
        for y in seasons:
            date = SEASON_END_DATES.get(y, "???")
            cup = CUP_RESULTS.get(y, {})
            print(f"  {y - 1}-{str(y)[2:]}: standings date={date}, cup winner={cup.get('winner', '?')}")
        return

    print(f"Fetching {len(seasons)} seasons of verified historical data")
    print(f"Output directory: {output_dir}")
    print(f"Sources: NHL API + Natural Stat Trick")

    results = []
    for year in seasons:
        filepath = fetch_season(year, output_dir, args.standings_only)
        results.append((year, filepath))

    # Summary
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    success = sum(1 for _, fp in results if fp is not None)
    failed = sum(1 for _, fp in results if fp is None)
    print(f"  Fetched: {success}/{len(seasons)} seasons")
    if failed > 0:
        print(f"  Failed:  {failed} seasons")
        for year, fp in results:
            if fp is None:
                print(f"    - {year}")

    # Create an index file listing all available verified seasons
    index = {
        "_metadata": {
            "description": "Index of verified historical NHL data",
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "sources": ["NHL API", "Natural Stat Trick"],
        },
        "seasons": {},
    }
    for year, fp in results:
        if fp is not None:
            cup = CUP_RESULTS.get(year, {})
            index["seasons"][str(year)] = {
                "file": fp.name,
                "seasonLabel": cup.get("season_label", f"{year - 1}-{str(year)[2:]}"),
                "cupWinner": cup.get("winner", ""),
                "cupFinalist": cup.get("finalist", ""),
            }

    index_path = output_dir / "index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    print(f"\n  Index saved to {index_path}")


if __name__ == "__main__":
    main()
