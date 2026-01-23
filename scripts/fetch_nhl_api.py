#!/usr/bin/env python3
"""
Fetch NHL standings and team stats from the official NHL API.
Outputs: data/nhl_standings.json
"""

import json
import requests
from pathlib import Path
from datetime import datetime

# NHL API endpoints
STANDINGS_URL = "https://api-web.nhle.com/v1/standings/now"
SCHEDULE_URL = "https://api-web.nhle.com/v1/schedule/now"

# Team abbreviation mapping (NHL API uses different codes)
TEAM_ABBREV_MAP = {
    "ANA": "ANA", "BOS": "BOS", "BUF": "BUF", "CAR": "CAR",
    "CBJ": "CBJ", "CGY": "CGY", "CHI": "CHI", "COL": "COL",
    "DAL": "DAL", "DET": "DET", "EDM": "EDM", "FLA": "FLA",
    "LAK": "LA", "MIN": "MIN", "MTL": "MTL", "NJD": "NJ",
    "NSH": "NSH", "NYI": "NYI", "NYR": "NYR", "OTT": "OTT",
    "PHI": "PHI", "PIT": "PIT", "SEA": "SEA", "SJS": "SJ",
    "STL": "STL", "TBL": "TB", "TOR": "TOR", "UTA": "UTA",
    "VAN": "VAN", "VGK": "VGK", "WPG": "WPG", "WSH": "WSH"
}

def fetch_standings():
    """Fetch current NHL standings."""
    print("Fetching NHL standings...")
    response = requests.get(STANDINGS_URL, timeout=30)
    response.raise_for_status()
    return response.json()

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
            "ppPct": round(team_data.get("powerPlayPctg", 0) * 100, 1) if team_data.get("powerPlayPctg") else 0,
            "pkPct": round(team_data.get("penaltyKillPctg", 0) * 100, 1) if team_data.get("penaltyKillPctg") else 0,
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

    # Add metadata
    output = {
        "_metadata": {
            "source": "NHL API",
            "endpoint": STANDINGS_URL,
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
