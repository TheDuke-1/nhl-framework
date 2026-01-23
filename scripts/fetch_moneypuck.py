#!/usr/bin/env python3
"""
Fetch xG and GSAx data from MoneyPuck CSV files.
Outputs: data/moneypuck_stats.json
"""

import json
import requests
import pandas as pd
from io import StringIO
from pathlib import Path
from datetime import datetime

# MoneyPuck CSV URLs (update season year as needed)
SEASON = "2025"  # 2024-25 season
TEAMS_CSV_URL = f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{SEASON}/regular/teams.csv"

# Team name to abbreviation mapping (supports both full names and abbreviations)
TEAM_NAME_MAP = {
    # Full names
    "Anaheim Ducks": "ANA",
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
    "Montreal Canadiens": "MTL",
    "New Jersey Devils": "NJ",
    "Nashville Predators": "NSH",
    "New York Islanders": "NYI",
    "New York Rangers": "NYR",
    "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI",
    "Pittsburgh Penguins": "PIT",
    "Seattle Kraken": "SEA",
    "San Jose Sharks": "SJ",
    "St. Louis Blues": "STL",
    "Tampa Bay Lightning": "TB",
    "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA",
    "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK",
    "Winnipeg Jets": "WPG",
    "Washington Capitals": "WSH",
    # Alternate names
    "Arizona Coyotes": "UTA",
    "L.A. Kings": "LA",
    # MoneyPuck abbreviations
    "ANA": "ANA", "BOS": "BOS", "BUF": "BUF", "CAR": "CAR",
    "CBJ": "CBJ", "CGY": "CGY", "CHI": "CHI", "COL": "COL",
    "DAL": "DAL", "DET": "DET", "EDM": "EDM", "FLA": "FLA",
    "LAK": "LA", "MIN": "MIN", "MTL": "MTL", "NJD": "NJ",
    "NSH": "NSH", "NYI": "NYI", "NYR": "NYR", "OTT": "OTT",
    "PHI": "PHI", "PIT": "PIT", "SEA": "SEA", "SJS": "SJ",
    "STL": "STL", "TBL": "TB", "TOR": "TOR", "UTA": "UTA",
    "VAN": "VAN", "VGK": "VGK", "WPG": "WPG", "WSH": "WSH",
    # Common variations
    "N.J": "NJ", "T.B": "TB", "L.A": "LA", "S.J": "SJ",
}

def fetch_moneypuck_csv():
    """Fetch the MoneyPuck teams CSV."""
    print(f"Fetching MoneyPuck data from {TEAMS_CSV_URL}...")
    response = requests.get(TEAMS_CSV_URL, timeout=30)
    response.raise_for_status()
    return response.text

def parse_moneypuck_data(csv_text):
    """Parse MoneyPuck CSV into our format."""
    df = pd.read_csv(StringIO(csv_text))

    teams = {}

    # Filter to 5v5 situation for most accurate metrics
    # MoneyPuck includes all situations - we want 5v5 for process metrics
    if 'situation' in df.columns:
        df_5v5 = df[df['situation'] == '5on5'].copy()
        df_all = df[df['situation'] == 'all'].copy()
    else:
        df_5v5 = df.copy()
        df_all = df.copy()

    for _, row in df_5v5.iterrows():
        team_name = row.get('team', '')
        abbrev = TEAM_NAME_MAP.get(team_name, '')

        if not abbrev:
            # Try matching by partial name
            for name, ab in TEAM_NAME_MAP.items():
                if name.lower() in team_name.lower() or team_name.lower() in name.lower():
                    abbrev = ab
                    break

        if not abbrev:
            print(f"Warning: Unknown team '{team_name}'")
            continue

        # Extract xG metrics (5v5)
        teams[abbrev] = {
            "team": abbrev,
            "xgf": round(row.get('xGoalsFor', 0), 2),
            "xga": round(row.get('xGoalsAgainst', 0), 2),
            "xgf60": round(row.get('xGoalsFor', 0) / max(row.get('icetime', 1) / 3600, 1), 2),
            "xga60": round(row.get('xGoalsAgainst', 0) / max(row.get('icetime', 1) / 3600, 1), 2),
            "gsax": round(row.get('goalsAgainst', 0) - row.get('xGoalsAgainst', 0), 2) * -1,  # Positive = better
            "cf": round(row.get('corsiFor', 0), 0),
            "ca": round(row.get('corsiAgainst', 0), 0),
            "ff": round(row.get('fenwickFor', 0), 0),
            "fa": round(row.get('fenwickAgainst', 0), 0),
            "shotsFor": round(row.get('shotsOnGoalFor', 0), 0),
            "shotsAgainst": round(row.get('shotsOnGoalAgainst', 0), 0),
        }

        # Calculate percentages
        cf = teams[abbrev]["cf"]
        ca = teams[abbrev]["ca"]
        if cf + ca > 0:
            teams[abbrev]["cfPct"] = round(cf / (cf + ca) * 100, 1)
        else:
            teams[abbrev]["cfPct"] = 50.0

        xgf = teams[abbrev]["xgf"]
        xga = teams[abbrev]["xga"]
        if xgf + xga > 0:
            teams[abbrev]["xgfPct"] = round(xgf / (xgf + xga) * 100, 1)
        else:
            teams[abbrev]["xgfPct"] = 50.0

    return teams

def main():
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    try:
        # Fetch and parse MoneyPuck data
        csv_text = fetch_moneypuck_csv()
        teams = parse_moneypuck_data(csv_text)

        # Add metadata
        output = {
            "_metadata": {
                "source": "MoneyPuck",
                "url": TEAMS_CSV_URL,
                "season": SEASON,
                "fetchedAt": datetime.utcnow().isoformat() + "Z",
                "teamCount": len(teams),
                "notes": "xG metrics at 5v5 situation"
            },
            "teams": teams
        }

        # Write to file
        output_path = data_dir / "moneypuck_stats.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"Saved {len(teams)} teams to {output_path}")
        return teams

    except Exception as e:
        print(f"Error fetching MoneyPuck data: {e}")
        # Return empty dict on error - merge script will handle missing data
        return {}

if __name__ == "__main__":
    main()
