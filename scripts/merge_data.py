#!/usr/bin/env python3
"""
Merge data from all sources (NHL API, MoneyPuck, Natural Stat Trick) into teams.json.
This is the final step that creates the data file the HTML dashboard loads.

Outputs: data/teams.json
"""

import json
from pathlib import Path
from datetime import datetime

# All 32 NHL teams with their conferences and divisions
NHL_TEAMS = {
    "ANA": {"name": "Anaheim Ducks", "conf": "West", "div": "Pacific"},
    "BOS": {"name": "Boston Bruins", "conf": "East", "div": "Atlantic"},
    "BUF": {"name": "Buffalo Sabres", "conf": "East", "div": "Atlantic"},
    "CAR": {"name": "Carolina Hurricanes", "conf": "East", "div": "Metropolitan"},
    "CBJ": {"name": "Columbus Blue Jackets", "conf": "East", "div": "Metropolitan"},
    "CGY": {"name": "Calgary Flames", "conf": "West", "div": "Pacific"},
    "CHI": {"name": "Chicago Blackhawks", "conf": "West", "div": "Central"},
    "COL": {"name": "Colorado Avalanche", "conf": "West", "div": "Central"},
    "DAL": {"name": "Dallas Stars", "conf": "West", "div": "Central"},
    "DET": {"name": "Detroit Red Wings", "conf": "East", "div": "Atlantic"},
    "EDM": {"name": "Edmonton Oilers", "conf": "West", "div": "Pacific"},
    "FLA": {"name": "Florida Panthers", "conf": "East", "div": "Atlantic"},
    "LA": {"name": "Los Angeles Kings", "conf": "West", "div": "Pacific"},
    "MIN": {"name": "Minnesota Wild", "conf": "West", "div": "Central"},
    "MTL": {"name": "Montreal Canadiens", "conf": "East", "div": "Atlantic"},
    "NJ": {"name": "New Jersey Devils", "conf": "East", "div": "Metropolitan"},
    "NSH": {"name": "Nashville Predators", "conf": "West", "div": "Central"},
    "NYI": {"name": "New York Islanders", "conf": "East", "div": "Metropolitan"},
    "NYR": {"name": "New York Rangers", "conf": "East", "div": "Metropolitan"},
    "OTT": {"name": "Ottawa Senators", "conf": "East", "div": "Atlantic"},
    "PHI": {"name": "Philadelphia Flyers", "conf": "East", "div": "Metropolitan"},
    "PIT": {"name": "Pittsburgh Penguins", "conf": "East", "div": "Metropolitan"},
    "SEA": {"name": "Seattle Kraken", "conf": "West", "div": "Pacific"},
    "SJ": {"name": "San Jose Sharks", "conf": "West", "div": "Pacific"},
    "STL": {"name": "St. Louis Blues", "conf": "West", "div": "Central"},
    "TB": {"name": "Tampa Bay Lightning", "conf": "East", "div": "Atlantic"},
    "TOR": {"name": "Toronto Maple Leafs", "conf": "East", "div": "Atlantic"},
    "UTA": {"name": "Utah Hockey Club", "conf": "West", "div": "Central"},
    "VAN": {"name": "Vancouver Canucks", "conf": "West", "div": "Pacific"},
    "VGK": {"name": "Vegas Golden Knights", "conf": "West", "div": "Pacific"},
    "WPG": {"name": "Winnipeg Jets", "conf": "West", "div": "Central"},
    "WSH": {"name": "Washington Capitals", "conf": "East", "div": "Metropolitan"},
}

# Default values for missing data
DEFAULTS = {
    "gp": 0, "w": 0, "l": 0, "otl": 0, "pts": 0,
    "gf": 0, "ga": 0, "ppPct": 20.0, "pkPct": 80.0,
    "cf": 50, "cfPct": 50.0, "xgf": 2.5, "xga": 2.5,
    "hdcf": 50, "hdcfPct": 50.0, "pdo": 100.0, "gsax": 0.0,
    "recentXgf": 50.0, "weight": 200, "depth20g": 3,
    "hasStar": False, "starPPG": 0.0,
}

def load_json(filepath):
    """Load a JSON file, return empty dict if not found."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return {}

def merge_team_data(nhl_data, mp_data, nst_data, abbrev):
    """Merge data from all sources for a single team."""
    team_info = NHL_TEAMS.get(abbrev, {})

    # Start with defaults
    team = {
        "team": abbrev,
        "name": team_info.get("name", abbrev),
        "conf": team_info.get("conf", "East"),
        "div": team_info.get("div", ""),
    }

    # Add all defaults
    for key, val in DEFAULTS.items():
        team[key] = val

    # Merge NHL API data (standings, basic stats)
    if abbrev in nhl_data:
        nhl = nhl_data[abbrev]
        team.update({
            "gp": nhl.get("gp", team["gp"]),
            "w": nhl.get("w", team["w"]),
            "l": nhl.get("l", team["l"]),
            "otl": nhl.get("otl", team["otl"]),
            "pts": nhl.get("pts", team["pts"]),
            "gf": nhl.get("gf", team["gf"]),
            "ga": nhl.get("ga", team["ga"]),
            "ppPct": nhl.get("ppPct", team["ppPct"]),
            "pkPct": nhl.get("pkPct", team["pkPct"]),
            "streak": nhl.get("streak", ""),
            "l10": nhl.get("l10", ""),
            "divRank": nhl.get("divRank", 0),
            "confRank": nhl.get("confRank", 0),
        })

        # Calculate recent form from L10
        if nhl.get("recentPts"):
            team["recentXgf"] = nhl.get("recentPts", 50.0)

    # Merge MoneyPuck data (xG, GSAx)
    if abbrev in mp_data:
        mp = mp_data[abbrev]
        team.update({
            "xgf": mp.get("xgf", team["xgf"]),
            "xga": mp.get("xga", team["xga"]),
            "gsax": mp.get("gsax", team["gsax"]),
            "cf": mp.get("cf", team["cf"]),
        })

        # Calculate xGF% if we have both
        xgf = team["xgf"]
        xga = team["xga"]
        if xgf + xga > 0:
            team["xgfPct"] = round(xgf / (xgf + xga) * 100, 1)

    # Merge Natural Stat Trick data (HDCF%, CF%, PDO)
    if abbrev in nst_data:
        nst = nst_data[abbrev]
        team.update({
            "hdcf": nst.get("hdcf", team["hdcf"]),
            "hdcfPct": nst.get("hdcfPct", team["hdcfPct"]),
            "cfPct": nst.get("cfPct", team["cfPct"]),
            "pdo": nst.get("pdo", team["pdo"]),
            "scf": nst.get("scf", 0),
            "scfPct": nst.get("scfPct", 50.0),
        })

        # Prefer NST for CF if available
        if nst.get("cf"):
            team["cf"] = nst.get("cf")

    # Calculate derived metrics

    # xG Differential
    team["xgd"] = round(team["xgf"] - team["xga"], 2)

    # Goal Differential
    team["gd"] = team["gf"] - team["ga"]

    # Points percentage
    if team["gp"] > 0:
        team["ptsPct"] = round(team["pts"] / (team["gp"] * 2) * 100, 1)
    else:
        team["ptsPct"] = 0

    # HDCF% as the main quality metric (alias for consistency)
    team["hdcf"] = team.get("hdcfPct", 50.0)

    return team

def main():
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Load all source files
    nhl_raw = load_json(data_dir / "nhl_standings.json")
    mp_raw = load_json(data_dir / "moneypuck_stats.json")
    nst_raw = load_json(data_dir / "nst_stats.json")

    # Extract team data from each source
    nhl_data = nhl_raw.get("teams", {})
    mp_data = mp_raw.get("teams", {})
    nst_data = nst_raw.get("teams", {})

    print(f"Loaded: NHL API ({len(nhl_data)} teams), MoneyPuck ({len(mp_data)} teams), NST ({len(nst_data)} teams)")

    # Merge all teams
    teams = []
    for abbrev in NHL_TEAMS:
        team = merge_team_data(nhl_data, mp_data, nst_data, abbrev)
        teams.append(team)

    # Sort by points (descending), then by games played
    teams.sort(key=lambda t: (-t["pts"], -t["gp"]))

    # Build output
    output = {
        "_metadata": {
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "sources": {
                "nhl_api": nhl_raw.get("_metadata", {}).get("fetchedAt", "unknown"),
                "moneypuck": mp_raw.get("_metadata", {}).get("fetchedAt", "unknown"),
                "nst": nst_raw.get("_metadata", {}).get("fetchedAt", "unknown"),
            },
            "teamCount": len(teams),
            "version": "7.0"
        },
        "teams": teams
    }

    # Write main teams.json
    output_path = data_dir / "teams.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Merged data for {len(teams)} teams to {output_path}")

    # Print summary
    print("\nTop 10 by Points:")
    for i, team in enumerate(teams[:10], 1):
        print(f"  {i}. {team['team']}: {team['pts']} pts, xGD: {team['xgd']:.1f}, HDCF%: {team.get('hdcfPct', 50):.1f}")

    return teams

if __name__ == "__main__":
    main()
