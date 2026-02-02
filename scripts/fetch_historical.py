#!/usr/bin/env python3
"""
Fetch verified historical NHL data from authoritative sources.

Sources:
  - NHL API (api-web.nhle.com) — Standings: W/L/OTL/PTS/GF/GA/PP%/PK%
  - Natural Stat Trick — Advanced: CF%, HDCF%, SCF%, PDO, SH%, SV%
  - Hockey-Reference — Playoff results (Cup winner, finalist, bracket)

Outputs: data/historical/verified/ directory with one JSON per season.

Usage:
    python fetch_historical.py                    # Fetch all seasons (2010-2025)
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
# NHL standings API works back to 2010. NST advanced stats reliable from ~2013.
SEASONS = list(range(2010, 2026))  # 2009-10 through 2024-25

# NHL API season end dates (approximate — last day of regular season)
# Used to fetch final standings for each season.
SEASON_END_DATES = {
    2010: "2010-04-11",
    2011: "2011-04-10",
    2012: "2012-04-07",
    2013: "2013-04-28",  # Lockout-shortened season
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
    2010: {"winner": "CHI", "finalist": "PHI", "season_label": "2009-10"},
    2011: {"winner": "BOS", "finalist": "VAN", "season_label": "2010-11"},
    2012: {"winner": "LA", "finalist": "NJ", "season_label": "2011-12"},
    2013: {"winner": "CHI", "finalist": "BOS", "season_label": "2012-13"},
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
    # 2025 (2024-25) season: playoffs not yet concluded — no Cup result
    2025: {"winner": "", "finalist": "", "season_label": "2024-25"},
}

# Playoff results: team abbreviation → rounds won
# 0=lost R1, 1=won R1 lost R2, 2=lost conf finals, 3=lost Cup Finals, 4=won Cup
# 2020 had 24-team bubble format — qualifying round losers get 0
PLAYOFF_RESULTS = {
    2010: {
        "CHI": 4, "PHI": 3,
        "SJ": 2, "MTL": 2,
        "BOS": 1, "PIT": 1, "LA": 1, "DET": 1,
        "WSH": 0, "NJ": 0, "BUF": 0, "OTT": 0, "COL": 0, "NSH": 0, "VAN": 0, "ARI": 0,
    },
    2011: {
        "BOS": 4, "VAN": 3,
        "TB": 2, "SJ": 2,
        "WSH": 1, "PHI": 1, "DET": 1, "NSH": 1,
        "NYR": 0, "BUF": 0, "PIT": 0, "MTL": 0, "CHI": 0, "LA": 0, "ARI": 0, "ANA": 0,
    },
    2012: {
        "LA": 4, "NJ": 3,
        "ARI": 2, "NYR": 2,
        "STL": 1, "NSH": 1, "PHI": 1, "WSH": 1,
        "VAN": 0, "SJ": 0, "CHI": 0, "DET": 0, "PIT": 0, "FLA": 0, "BOS": 0, "OTT": 0,
    },
    2013: {
        "CHI": 4, "BOS": 3,
        "LA": 2, "PIT": 2,
        "DET": 1, "SJ": 1, "NYR": 1, "OTT": 1,
        "MIN": 0, "ANA": 0, "VAN": 0, "STL": 0, "TOR": 0, "WSH": 0, "MTL": 0, "NYI": 0,
    },
    2014: {
        "LA": 4, "NYR": 3,
        "MTL": 2, "CHI": 2,
        "BOS": 1, "PIT": 1, "ANA": 1, "MIN": 1,
        "PHI": 0, "CBJ": 0, "TB": 0, "DET": 0, "SJ": 0, "DAL": 0, "STL": 0, "COL": 0,
    },
    2015: {
        "CHI": 4, "TB": 3,
        "ANA": 2, "NYR": 2,
        "CGY": 1, "MIN": 1, "MTL": 1, "WSH": 1,
        "WPG": 0, "VAN": 0, "NSH": 0, "STL": 0, "PIT": 0, "DET": 0, "OTT": 0, "NYI": 0,
    },
    2016: {
        "PIT": 4, "SJ": 3,
        "TB": 2, "STL": 2,
        "NYI": 1, "WSH": 1, "DAL": 1, "NSH": 1,
        "NYR": 0, "DET": 0, "PHI": 0, "FLA": 0, "CHI": 0, "MIN": 0, "LA": 0, "ANA": 0,
    },
    2017: {
        "PIT": 4, "NSH": 3,
        "OTT": 2, "ANA": 2,
        "NYR": 1, "WSH": 1, "STL": 1, "EDM": 1,
        "CBJ": 0, "MTL": 0, "BOS": 0, "TOR": 0, "CHI": 0, "MIN": 0, "CGY": 0, "SJ": 0,
    },
    2018: {
        "WSH": 4, "VGK": 3,
        "TB": 2, "WPG": 2,
        "BOS": 1, "PIT": 1, "NSH": 1, "SJ": 1,
        "NJ": 0, "TOR": 0, "CBJ": 0, "PHI": 0, "COL": 0, "MIN": 0, "LA": 0, "ANA": 0,
    },
    2019: {
        "STL": 4, "BOS": 3,
        "CAR": 2, "SJ": 2,
        "CBJ": 1, "NYI": 1, "COL": 1, "DAL": 1,
        "TB": 0, "PIT": 0, "WSH": 0, "TOR": 0, "NSH": 0, "WPG": 0, "CGY": 0, "VGK": 0,
    },
    # 2020: 24-team bubble. Qualifying round losers get 0.
    2020: {
        "TB": 4, "DAL": 3,
        "NYI": 2, "VGK": 2,
        "BOS": 1, "PHI": 1, "COL": 1, "VAN": 1,
        "CBJ": 0, "MTL": 0, "CAR": 0, "WSH": 0, "CHI": 0, "ARI": 0, "CGY": 0, "STL": 0,
        "PIT": 0, "NYR": 0, "FLA": 0, "TOR": 0, "EDM": 0, "NSH": 0, "MIN": 0, "WPG": 0,
    },
    2021: {
        "TB": 4, "MTL": 3,
        "NYI": 2, "VGK": 2,
        "BOS": 1, "CAR": 1, "COL": 1, "WPG": 1,
        "WSH": 0, "PIT": 0, "EDM": 0, "TOR": 0, "FLA": 0, "NSH": 0, "MIN": 0, "STL": 0,
    },
    2022: {
        "COL": 4, "TB": 3,
        "NYR": 2, "EDM": 2,
        "CAR": 1, "FLA": 1, "STL": 1, "CGY": 1,
        "PIT": 0, "WSH": 0, "BOS": 0, "TOR": 0, "NSH": 0, "MIN": 0, "DAL": 0, "LA": 0,
    },
    2023: {
        "VGK": 4, "FLA": 3,
        "CAR": 2, "DAL": 2,
        "TOR": 1, "NJ": 1, "EDM": 1, "SEA": 1,
        "BOS": 0, "TB": 0, "NYI": 0, "NYR": 0, "WPG": 0, "LA": 0, "MIN": 0, "COL": 0,
    },
    2024: {
        "FLA": 4, "EDM": 3,
        "NYR": 2, "DAL": 2,
        "BOS": 1, "CAR": 1, "COL": 1, "VAN": 1,
        "TOR": 0, "TB": 0, "WSH": 0, "NYI": 0, "VGK": 0, "WPG": 0, "NSH": 0, "LA": 0,
    },
    # 2025 (2024-25) season: playoffs not yet concluded — no bracket data
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
    2010: 30, 2011: 30, 2012: 30, 2013: 30,
    2014: 30, 2015: 30, 2016: 30, 2017: 30,
    2018: 31, 2019: 31, 2020: 31, 2021: 31,
    2022: 32, 2023: 32, 2024: 32, 2025: 32,
}

REQUEST_DELAY = 3  # seconds between requests (be respectful)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _match_team_abbrev(team_name, team_map):
    """
    Look up a team name in a name→abbreviation map.
    Tries exact match first, then case-insensitive exact match fallback.
    Returns abbreviation or None.
    """
    abbrev = team_map.get(team_name)
    if abbrev:
        return abbrev
    # Case-insensitive exact match only (no substring — avoids
    # "New York Rangers" matching "New York Islanders")
    lower = team_name.strip().lower()
    for name, ab in team_map.items():
        if name.lower() == lower:
            return ab
    return None


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
        api_abbrev = (t.get("teamAbbrev") or {}).get("default", "")
        abbrev = NHL_ABBREV_MAP.get(api_abbrev, api_abbrev)
        if not abbrev:
            continue

        teams[abbrev] = {
            "team": abbrev,
            "name": (t.get("teamName") or {}).get("default", ""),
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
# NHL Stats REST API — Special Teams (PP%/PK%)
# ---------------------------------------------------------------------------

def fetch_nhl_special_teams(year):
    """
    Fetch PP% and PK% from the NHL Stats REST API.
    The standings endpoint returns None for these fields, but the
    stats/rest/en/team/summary endpoint has them.

    Returns dict of {team_abbrev: {"ppPct": float, "pkPct": float}}.
    """
    season_id = f"{year - 1}{year}"
    url = "https://api.nhle.com/stats/rest/en/team/summary"
    params = {"cayenneExp": f"seasonId={season_id} and gameTypeId=2"}

    print(f"  Fetching NHL Stats API special teams for {year} (season {season_id})...")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"  ERROR: NHL Stats API request failed for {year}: {e}")
        return {}

    teams = {}
    for t in data.get("data", []):
        team_name = t.get("teamFullName", "")
        abbrev = _match_team_abbrev(team_name, NST_TEAM_MAP)
        if not abbrev:
            print(f"  WARNING: Unknown team in stats API: {team_name}")
            continue

        pp_pct = t.get("powerPlayPct", 0) or 0
        pk_pct = t.get("penaltyKillPct", 0) or 0

        teams[abbrev] = {
            "ppPct": round(pp_pct * 100, 1),
            "pkPct": round(pk_pct * 100, 1),
        }

    print(f"  -> Got {len(teams)} teams with PP%/PK% from NHL Stats API")
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

        abbrev = _match_team_abbrev(team_name, NST_TEAM_MAP)
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

def merge_season_data(year, standings, advanced, special_teams=None):
    """Merge standings + advanced stats + special teams + playoff results."""
    cup_info = CUP_RESULTS.get(year, {})
    playoff_results = PLAYOFF_RESULTS.get(year, {})
    season_label = cup_info.get("season_label", f"{year - 1}-{str(year)[2:]}")
    if special_teams is None:
        special_teams = {}

    playoff_team_count = len(playoff_results)

    merged = {
        "_metadata": {
            "season": season_label,
            "year": year,
            "sources": {
                "standings": "NHL API (api-web.nhle.com)",
                "advanced": "Natural Stat Trick (naturalstattrick.com)",
                "specialTeams": "NHL Stats REST API (api.nhle.com/stats/rest)",
            },
            "fetchedAt": datetime.utcnow().isoformat() + "Z",
            "cupWinner": cup_info.get("winner", ""),
            "cupFinalist": cup_info.get("finalist", ""),
            "playoffTeams": playoff_team_count,
        },
        "teams": {},
    }

    # Start with standings (the authoritative source for W/L/PTS/GF/GA)
    for abbrev, st in standings.items():
        team_data = dict(st)  # copy

        # Merge special teams from Stats REST API (overrides 0s from standings)
        st_data = special_teams.get(abbrev, {})
        if st_data:
            team_data["ppPct"] = st_data["ppPct"]
            team_data["pkPct"] = st_data["pkPct"]

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

        # Playoff results
        team_data["wonCup"] = (abbrev == cup_info.get("winner"))
        team_data["cupFinalist"] = (abbrev == cup_info.get("finalist"))
        team_data["madePlayoffs"] = abbrev in playoff_results
        team_data["playoffRoundsWon"] = playoff_results.get(abbrev, 0)

        merged["teams"][abbrev] = team_data

    # Check for teams in advanced but not in standings
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

    if len(teams) != expected:
        issues.append(f"Team count: {len(teams)} (expected {expected})")

    playoff_count = sum(1 for t in teams.values() if t.get("madePlayoffs"))
    expected_playoff = 24 if year == 2020 else 16
    if playoff_count != expected_playoff:
        issues.append(f"Playoff teams: {playoff_count} (expected {expected_playoff})")

    for abbrev, t in teams.items():
        pts = t.get("pts", 0)
        w = t.get("w", 0)
        gp = t.get("gp", 0)

        if gp < 40 and year != 2020 and year != 2021:
            issues.append(f"{abbrev}: Only {gp} games played (expected ~82)")
        if pts > 0 and pts < 30 and gp > 60:
            issues.append(f"{abbrev}: Only {pts} points in {gp} games (suspicious)")
        if w > gp:
            issues.append(f"{abbrev}: More wins ({w}) than games ({gp})")

        # Special teams ranges (8-35 PP%, 65-95 PK% — ANA 2021 had 8.9% PP)
        ppPct = t.get("ppPct", 0)
        pkPct = t.get("pkPct", 0)
        if ppPct > 0 and (ppPct < 8 or ppPct > 35):
            issues.append(f"{abbrev}: PP% = {ppPct} out of expected range (8-35)")
        if pkPct > 0 and (pkPct < 65 or pkPct > 95):
            issues.append(f"{abbrev}: PK% = {pkPct} out of expected range (65-95)")

        # Advanced stats ranges
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

    # 2. Fetch special teams (PP%/PK%) from NHL Stats REST API
    special_teams = fetch_nhl_special_teams(year)
    time.sleep(REQUEST_DELAY)

    # 3. Fetch advanced stats from NST (unless standings-only)
    advanced = {}
    if not standings_only:
        advanced = fetch_nst_advanced(year)
        time.sleep(REQUEST_DELAY)

    # 4. Merge
    merged = merge_season_data(year, standings, advanced, special_teams)

    # 5. Validate
    validate_season(year, merged)

    # 6. Save
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
            "sources": ["NHL API", "NHL Stats REST API", "Natural Stat Trick"],
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
