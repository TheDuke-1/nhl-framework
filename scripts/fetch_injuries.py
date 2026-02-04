#!/usr/bin/env python3
"""
Fetch NHL injury data from public sources.

Primary: Hockey-Reference injury report (structured HTML table)
Fallback: Empty data (graceful degradation)

Output: data/injuries.json
"""

import json
import logging
import sys
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Add scripts dir to path for config import
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    DATA_DIR, ALL_TEAMS, USER_AGENT, REQUEST_TIMEOUT, get_current_timestamp
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": USER_AGENT}

# Hockey-Reference team abbreviation mapping to our standard abbreviations
HREF_TEAM_MAP = {
    "ANA": "ANA", "BOS": "BOS", "BUF": "BUF", "CAR": "CAR",
    "CBJ": "CBJ", "CGY": "CGY", "CHI": "CHI", "COL": "COL",
    "DAL": "DAL", "DET": "DET", "EDM": "EDM", "FLA": "FLA",
    "LAK": "LA", "MIN": "MIN", "MTL": "MTL", "NJD": "NJ",
    "NSH": "NSH", "NYI": "NYI", "NYR": "NYR", "OTT": "OTT",
    "PHI": "PHI", "PIT": "PIT", "SEA": "SEA", "SJS": "SJ",
    "STL": "STL", "TBL": "TB", "TOR": "TOR", "UTA": "UTA",
    "VAN": "VAN", "VGK": "VGK", "WPG": "WPG", "WSH": "WSH",
}

# Full team name to abbreviation (for Hockey-Reference)
TEAM_NAME_MAP = {
    "Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF",
    "Carolina Hurricanes": "CAR", "Columbus Blue Jackets": "CBJ",
    "Calgary Flames": "CGY", "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL", "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA", "Los Angeles Kings": "LA",
    "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL",
    "New Jersey Devils": "NJ", "Nashville Predators": "NSH",
    "New York Islanders": "NYI", "New York Rangers": "NYR",
    "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI",
    "Pittsburgh Penguins": "PIT", "Seattle Kraken": "SEA",
    "San Jose Sharks": "SJ", "St. Louis Blues": "STL",
    "Tampa Bay Lightning": "TB", "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA", "Utah Mammoth": "UTA",
    "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
    "Winnipeg Jets": "WPG", "Washington Capitals": "WSH",
}


def fetch_hockey_reference_injuries():
    """
    Scrape Hockey-Reference injury report.

    Hockey-Reference has a structured HTML table with columns:
    Player, Team, Date, Injury Type, Injury Note
    """
    url = "https://www.hockey-reference.com/friv/injuries.cgi"
    injuries_by_team = {team: [] for team in ALL_TEAMS}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")

        # Find the injuries table
        table = soup.find("table", {"id": "injuries"})
        if table is None:
            # Try finding any table with injury data
            table = soup.find("table")

        if table is None:
            logger.warning("No injury table found on Hockey-Reference")
            return injuries_by_team

        tbody = table.find("tbody")
        if tbody is None:
            tbody = table

        rows = tbody.find_all("tr")
        parsed_count = 0

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue

            # Extract player name (first cell, may be a link)
            player_cell = cells[0]
            player_name = player_cell.get_text(strip=True)

            # Extract team (second cell, may be a link)
            team_cell = cells[1]
            team_text = team_cell.get_text(strip=True)

            # Try to get team abbrev from link href
            team_link = team_cell.find("a")
            team_abbrev = None
            if team_link and team_link.get("href"):
                # href like "/teams/TOR/2026.html"
                href = team_link["href"]
                match = re.search(r'/teams/([A-Z]+)/', href)
                if match:
                    href_abbrev = match.group(1)
                    team_abbrev = HREF_TEAM_MAP.get(href_abbrev, href_abbrev)

            # Fallback: match by full team name
            if team_abbrev is None:
                team_abbrev = TEAM_NAME_MAP.get(team_text, None)

            if team_abbrev is None or team_abbrev not in injuries_by_team:
                continue

            # Extract injury type and note
            injury_type = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            injury_note = cells[4].get_text(strip=True) if len(cells) > 4 else ""

            # Determine status from note
            status = classify_injury_status(injury_note, injury_type)

            injuries_by_team[team_abbrev].append({
                "player": player_name,
                "position": "",  # Hockey-Reference doesn't always include position
                "status": status,
                "injury": injury_type,
                "note": injury_note,
            })
            parsed_count += 1

        logger.info(f"Parsed {parsed_count} injuries from Hockey-Reference")

    except Exception as e:
        logger.warning(f"Failed to scrape Hockey-Reference: {e}")

    return injuries_by_team


def classify_injury_status(note, injury_type):
    """Classify injury into a standard status from the note text."""
    note_lower = (note + " " + injury_type).lower()

    if "long-term" in note_lower or "ltir" in note_lower:
        return "LTIR"
    elif "injured reserve" in note_lower or " ir " in note_lower:
        return "IR"
    elif "day-to-day" in note_lower or "dtd" in note_lower:
        return "DTD"
    elif "out" in note_lower:
        return "Out"
    elif "questionable" in note_lower:
        return "DTD"
    else:
        return "Out"


def estimate_war(position, status):
    """
    Estimate WAR impact of an injured player.

    Without detailed player stats, we use conservative positional estimates
    adjusted by injury severity. This is intentionally rough — the dashboard
    shows it as "estimated" and uses it for relative team comparison, not
    as an exact value.
    """
    position = position.upper() if position else ""
    status = status.upper() if status else ""

    # Conservative positional WAR estimates (per 82 games)
    if "G" in position:
        base_war = 3.0
    elif "D" in position:
        base_war = 1.5
    elif "C" in position:
        base_war = 2.0
    else:
        base_war = 1.5  # Wings / unknown

    # Severity multiplier
    if "LTIR" in status:
        return base_war
    elif "IR" in status:
        return base_war * 0.8
    elif "DTD" in status:
        return base_war * 0.3
    elif "OUT" in status:
        return base_war * 0.6
    else:
        return base_war * 0.4


def main():
    """Fetch injuries and save to data/injuries.json."""
    DATA_DIR.mkdir(exist_ok=True)

    logger.info("Fetching injury data from Hockey-Reference...")
    injuries = fetch_hockey_reference_injuries()

    # Compute per-team WAR impact
    team_summary = {}
    total_injuries = 0

    for team_abbrev in ALL_TEAMS:
        team_injuries = injuries.get(team_abbrev, [])
        total_war_lost = 0.0

        for inj in team_injuries:
            war = estimate_war(inj.get("position", ""), inj.get("status", ""))
            inj["estimatedWar"] = round(war, 1)
            total_war_lost += war

        team_summary[team_abbrev] = {
            "injuries": team_injuries,
            "totalWarLost": round(total_war_lost, 1),
            "injuredCount": len(team_injuries),
        }
        total_injuries += len(team_injuries)

    # Build output
    output = {
        "_metadata": {
            "fetchedAt": get_current_timestamp(),
            "source": "Hockey-Reference",
            "teamCount": len(team_summary),
            "totalInjuries": total_injuries,
        },
        "teams": team_summary,
    }

    output_path = DATA_DIR / "injuries.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Saved injury data: {total_injuries} injuries across {len(team_summary)} teams")

    # Print summary
    teams_with_injuries = [(t, d) for t, d in team_summary.items() if d["injuredCount"] > 0]
    teams_with_injuries.sort(key=lambda x: -x[1]["totalWarLost"])

    if teams_with_injuries:
        print(f"\nTeams with injuries ({len(teams_with_injuries)}):")
        for team, data in teams_with_injuries[:10]:
            players = ", ".join(i["player"] for i in data["injuries"][:3])
            more = f" +{len(data['injuries'])-3} more" if len(data["injuries"]) > 3 else ""
            print(f"  {team}: {data['injuredCount']} injured, ~{data['totalWarLost']:.1f} WAR lost ({players}{more})")
    else:
        print("\nNo injury data found (scraping may have failed)")

    return output


if __name__ == "__main__":
    main()
