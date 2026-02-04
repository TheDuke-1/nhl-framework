#!/usr/bin/env python3
"""
Merge data from all sources (NHL API, MoneyPuck, Natural Stat Trick) into teams.json.
This is the final step that creates the data file the HTML dashboard loads.

Outputs: data/teams.json
"""

import json
from pathlib import Path
from datetime import datetime

from config import TEAM_NAMES, TEAM_INFO, ALL_TEAMS
from utils import load_json_file

# Build NHL_TEAMS dict from config's TEAM_NAMES and TEAM_INFO
NHL_TEAMS = {}
for abbrev in ALL_TEAMS:
    info = TEAM_INFO.get(abbrev, {"conf": "Unknown", "div": "Unknown"})
    NHL_TEAMS[abbrev] = {
        "name": TEAM_NAMES.get(abbrev, abbrev),
        "conf": info["conf"],
        "div": info["div"],
    }

# Default values for missing data
DEFAULTS = {
    "gp": 0, "w": 0, "l": 0, "otl": 0, "pts": 0,
    "gf": 0, "ga": 0, "ppPct": 20.0, "pkPct": 80.0,
    "cf": 0, "cfPct": 50.0, "xgf": 0, "xga": 0,
    "hdcf": 0, "hdcfPct": 50.0, "pdo": 1.000, "gsax": 0.0,
    "scf": 0, "scfPct": 50.0, "xgfPct": 50.0,
    "recentForm": 50.0, "weight": 200,
}

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
            "home": nhl.get("home", ""),
            "away": nhl.get("away", ""),
            "divRank": nhl.get("divRank", 0),
            "confRank": nhl.get("confRank", 0),
            "leagueRank": nhl.get("leagueRank", 0),
        })

        # Recent form from L10 record (points percentage in last 10 games)
        if nhl.get("recentPts"):
            team["recentForm"] = round(nhl.get("recentPts", 50.0), 1)

    # Merge Natural Stat Trick data (primary source for advanced stats)
    # NST provides: CF%, HDCF%, PDO, xGF, xGA, SCF%, SH%, SV%
    if abbrev in nst_data:
        nst = nst_data[abbrev]
        team.update({
            "cf": nst.get("cf", team["cf"]),
            "cfPct": nst.get("cfPct", team["cfPct"]),
            "hdcf": nst.get("hdcf", team["hdcf"]),
            "hdcfPct": nst.get("hdcfPct", team["hdcfPct"]),
            "pdo": nst.get("pdo", team["pdo"]),
            "scf": nst.get("scf", 0),
            "scfPct": nst.get("scfPct", 50.0),
            "xgf": nst.get("xgf", team["xgf"]),
            "xga": nst.get("xga", team["xga"]),
            "xgfPct": nst.get("xgfPct", 50.0),
            "gsax": nst.get("gsax", team["gsax"]),
        })

    # Merge MoneyPuck data as secondary/cross-reference (if available)
    if abbrev in mp_data:
        mp = mp_data[abbrev]
        # Only use MoneyPuck if NST didn't provide xG data
        if team["xgf"] == DEFAULTS["xgf"]:
            team.update({
                "xgf": mp.get("xgf", team["xgf"]),
                "xga": mp.get("xga", team["xga"]),
                "gsax": mp.get("gsax", team["gsax"]),
            })
        # Store MoneyPuck values for cross-reference
        team["mp_xgf"] = mp.get("xgf", 0)
        team["mp_gsax"] = mp.get("gsax", 0)

    # Calculate derived metrics

    # xG Differential
    team["xgd"] = round(team["xgf"] - team["xga"], 2)

    # xGF% (if not already set)
    xgf = team["xgf"]
    xga = team["xga"]
    if "xgfPct" not in team or team["xgfPct"] == 50.0:
        if xgf + xga > 0:
            team["xgfPct"] = round(xgf / (xgf + xga) * 100, 1)

    # Goal Differential
    team["gd"] = team["gf"] - team["ga"]

    # Points percentage
    if team["gp"] > 0:
        team["ptsPct"] = round(team["pts"] / (team["gp"] * 2) * 100, 1)
    else:
        team["ptsPct"] = 0

    # Weight placeholder — all real scoring now handled by superhuman ML model.
    # Old V7.2 hand-tuned weights archived to archive/v72_weights.py
    team["weight"] = 200

    return team

def main():
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Load all source files
    nhl_raw = load_json_file(data_dir / "nhl_standings.json")
    mp_raw = load_json_file(data_dir / "moneypuck_stats.json")
    nst_raw = load_json_file(data_dir / "nst_stats.json")
    odds_raw = load_json_file(data_dir / "odds.json")

    # Extract team data from each source
    nhl_data = nhl_raw.get("teams", {})
    mp_data = mp_raw.get("teams", {})
    nst_data = nst_raw.get("teams", {})
    odds_data = odds_raw.get("teams", {})

    print(f"Loaded: NHL API ({len(nhl_data)} teams), MoneyPuck ({len(mp_data)} teams), NST ({len(nst_data)} teams), Odds ({len(odds_data)} teams)")

    # Merge all teams
    teams = []
    for abbrev in NHL_TEAMS:
        team = merge_team_data(nhl_data, mp_data, nst_data, abbrev)

        # Merge odds data
        if abbrev in odds_data:
            odds = odds_data[abbrev]
            team["playoffPct"] = odds.get("playoffPct", 0)
            team["divisionPct"] = odds.get("divisionPct", 0)
            team["cupPct"] = odds.get("cupPct", 0)
            team["impliedCupOdds"] = odds.get("impliedCupOdds", 0)
            team["projPts"] = odds.get("projPts", 0)

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
                "odds": odds_raw.get("_metadata", {}).get("fetchedAt", "unknown"),
            },
            "teamCount": len(teams),
            "version": "7.3"
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
