#!/usr/bin/env python3
"""
Fetch NHL standings and team stats from the official NHL API.
Outputs: data/nhl_standings.json

Uses two API endpoints:
  - api-web.nhle.com/v1/standings — W/L/OTL/PTS/GF/GA, streaks, rankings
  - api.nhle.com/stats/rest — PP% and PK% (removed from standings endpoint)
"""

import json
from pathlib import Path
from datetime import datetime

from config import NHL_API_TEAM_MAP as TEAM_ABBREV_MAP, NST_TEAM_MAP as TEAM_NAME_MAP, SEASON_ID, NHL_API
from utils import fetch_json

# NHL API endpoints (built from config)
STANDINGS_URL = NHL_API["standings"]
PP_STATS_URL = f"https://api.nhle.com/stats/rest/en/team/powerplay?cayenneExp=seasonId={SEASON_ID}"
PK_STATS_URL = f"https://api.nhle.com/stats/rest/en/team/penaltykill?cayenneExp=seasonId={SEASON_ID}"

def fetch_standings():
    """Fetch current NHL standings."""
    print("Fetching NHL standings...")
    return fetch_json(STANDINGS_URL)

def fetch_pp_pk_stats():
    """Fetch PP% and PK% from the NHL stats API (separate from standings)."""
    pp_by_team = {}
    pk_by_team = {}

    # Fetch power play stats
    print("Fetching PP% from NHL stats API...")
    try:
        data = fetch_json(PP_STATS_URL)
        for row in data.get("data", []):
            name = row.get("teamFullName", "")
            abbrev = TEAM_NAME_MAP.get(name)
            if abbrev and "powerPlayPct" in row:
                raw = row["powerPlayPct"]
                pct = raw * 100 if raw < 1 else raw  # Handle both 0.225 and 22.5 formats
                if 5 <= pct <= 40:  # Sanity check: NHL PP% is always 5-40%
                    pp_by_team[abbrev] = round(pct, 1)
    except Exception as e:
        print("Warning: Could not fetch PP stats: %s" % e)

    # Fetch penalty kill stats
    print("Fetching PK% from NHL stats API...")
    try:
        data = fetch_json(PK_STATS_URL)
        for row in data.get("data", []):
            name = row.get("teamFullName", "")
            abbrev = TEAM_NAME_MAP.get(name)
            if abbrev and "penaltyKillPct" in row:
                raw = row["penaltyKillPct"]
                pct = raw * 100 if raw < 1 else raw  # Handle both 0.815 and 81.5 formats
                if 60 <= pct <= 95:  # Sanity check: NHL PK% is always 60-95%
                    pk_by_team[abbrev] = round(pct, 1)
    except Exception as e:
        print("Warning: Could not fetch PK stats: %s" % e)

    print("PP stats: %d teams, PK stats: %d teams" % (len(pp_by_team), len(pk_by_team)))
    return pp_by_team, pk_by_team

def parse_standings(data):
    """Parse standings data into our format."""
    teams = {}

    for team_data in data.get("standings", []):
        # Get team abbreviation
        api_abbrev = team_data.get("teamAbbrev", {}).get("default", "")
        abbrev = TEAM_ABBREV_MAP.get(api_abbrev, api_abbrev)

        if not abbrev:
            continue

        # Extract stats
        teams[abbrev] = {
            "team": abbrev,
            "teamName": team_data.get("teamName", {}).get("default", ""),
            "conf": "East" if team_data.get("conferenceName") == "Eastern" else "West",
            "div": team_data.get("divisionName", ""),
            "gp": team_data.get("gamesPlayed", 0),
            "w": team_data.get("wins", 0),
            "l": team_data.get("losses", 0),
            "otl": team_data.get("otLosses", 0),
            "pts": team_data.get("points", 0),
            "gf": team_data.get("goalFor", 0),
            "ga": team_data.get("goalAgainst", 0),
            "streak": team_data.get("streakCode", ""),
            "l10": f"{team_data.get('l10Wins', 0)}-{team_data.get('l10Losses', 0)}-{team_data.get('l10OtLosses', 0)}",
            "home": f"{team_data.get('homeWins', 0)}-{team_data.get('homeLosses', 0)}-{team_data.get('homeOtLosses', 0)}",
            "away": f"{team_data.get('roadWins', 0)}-{team_data.get('roadLosses', 0)}-{team_data.get('roadOtLosses', 0)}",
            # Note: powerPlayPctg and penaltyKillPctg were removed from the
            # standings endpoint. PP% and PK% now come from NST or other sources.
            "divRank": team_data.get("divisionSequence", 0),
            "confRank": team_data.get("conferenceSequence", 0),
            "leagueRank": team_data.get("leagueSequence", 0),
        }

        # Calculate recent form from L10
        l10_wins = team_data.get("l10Wins", 0)
        l10_losses = team_data.get("l10Losses", 0)
        l10_otl = team_data.get("l10OtLosses", 0)
        l10_total = l10_wins + l10_losses + l10_otl
        if l10_total > 0:
            teams[abbrev]["recentPts"] = (l10_wins * 2 + l10_otl) / (l10_total * 2) * 100
        else:
            teams[abbrev]["recentPts"] = 50.0

    return teams

def main():
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Fetch and parse standings
    raw_data = fetch_standings()
    teams = parse_standings(raw_data)

    # Fetch PP% and PK% from separate stats API
    pp_stats, pk_stats = fetch_pp_pk_stats()

    # Merge PP%/PK% into team data
    for abbrev, team in teams.items():
        if abbrev in pp_stats:
            team["ppPct"] = pp_stats[abbrev]
        if abbrev in pk_stats:
            team["pkPct"] = pk_stats[abbrev]

    # Add metadata
    output = {
        "_metadata": {
            "source": "NHL API",
            "endpoints": [STANDINGS_URL, PP_STATS_URL, PK_STATS_URL],
            "fetchedAt": datetime.utcnow().isoformat() + "Z",
            "teamCount": len(teams)
        },
        "teams": teams
    }

    # Write to file
    output_path = data_dir / "nhl_standings.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(teams)} teams to {output_path}")
    return teams

if __name__ == "__main__":
    main()
