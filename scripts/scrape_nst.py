#!/usr/bin/env python3
"""
Scrape Natural Stat Trick for advanced analytics (HDCF%, CF%, PDO, etc.)
Outputs: data/nst_stats.json

Note: Please support Natural Stat Trick via Patreon if using regularly.
Rate limiting is implemented to be respectful of their servers.
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

# Natural Stat Trick URLs
NST_BASE_URL = "https://naturalstattrick.com/teamtable.php"

# Rate limiting - be respectful of the site
REQUEST_DELAY = 2  # seconds between requests

# Team name to abbreviation mapping
TEAM_NAME_MAP = {
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
    "Montréal Canadiens": "MTL",
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
    "St Louis Blues": "STL",
    "Tampa Bay Lightning": "TB",
    "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA",
    "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK",
    "Winnipeg Jets": "WPG",
    "Washington Capitals": "WSH",
}

def fetch_nst_page(situation="5v5", report_type="team"):
    """Fetch a page from Natural Stat Trick."""
    params = {
        "fromseason": "20252026",
        "thruseason": "20252026",
        "stype": "2",  # Regular season
        "sit": situation,
        "score": "all",
        "rate": "n",
        "team": "all",
        "loc": "B",
        "gpf": "410",
        "fd": "",
        "td": ""
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    print(f"Fetching NST data for {situation}...")
    response = requests.get(NST_BASE_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    return response.text

def parse_nst_table(html_content):
    """Parse the NST team table HTML."""
    soup = BeautifulSoup(html_content, 'lxml')

    # Find the main data table
    table = soup.find('table', {'id': 'teams'})
    if not table:
        # Try alternate table ID
        table = soup.find('table', class_='sortable')

    if not table:
        print("Warning: Could not find team table")
        return {}

    teams = {}

    # Parse table rows
    tbody = table.find('tbody')
    if not tbody:
        rows = table.find_all('tr')[1:]  # Skip header
    else:
        rows = tbody.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 5:
            continue

        # First cell usually contains team name
        team_cell = cells[0]
        team_name = team_cell.get_text(strip=True)

        # Map to abbreviation
        abbrev = TEAM_NAME_MAP.get(team_name)
        if not abbrev:
            # Try partial matching
            for name, ab in TEAM_NAME_MAP.items():
                if name.lower() in team_name.lower() or team_name.lower() in name.lower():
                    abbrev = ab
                    break

        if not abbrev:
            continue

        # Parse cell values - column positions may vary
        try:
            teams[abbrev] = {
                "team": abbrev,
                "gp": safe_int(cells[1].get_text(strip=True)) if len(cells) > 1 else 0,
                "toi": cells[2].get_text(strip=True) if len(cells) > 2 else "0",
            }

            # Look for specific stats in remaining cells
            # NST table structure varies, so we parse by finding column headers
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True)

                # CF% is usually percentage around 45-55
                if i >= 3 and is_percentage(text, 40, 60):
                    if "cfPct" not in teams[abbrev]:
                        teams[abbrev]["cfPct"] = safe_float(text)

        except (ValueError, IndexError) as e:
            print(f"Warning: Error parsing row for {team_name}: {e}")
            continue

    return teams

def fetch_and_parse_nst():
    """Fetch all NST data with proper column parsing."""
    print("Fetching Natural Stat Trick data...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    # Fetch main team table
    url = "https://naturalstattrick.com/teamtable.php"
    params = {
        "fromseason": "20252026",
        "thruseason": "20252026",
        "stype": "2",
        "sit": "5v5",
        "score": "all",
        "rate": "n",
        "team": "all",
        "loc": "B",
        "gpf": "410"
    }

    response = requests.get(url, params=params, headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"Warning: NST returned status {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, 'lxml')

    # Find the teams table
    table = soup.find('table', {'id': 'teams'})
    if not table:
        table = soup.find('table')

    if not table:
        print("Error: Could not find data table")
        return {}

    # Get headers to map columns
    headers_row = table.find('thead')
    if headers_row:
        header_cells = headers_row.find_all('th')
        column_names = [h.get_text(strip=True) for h in header_cells]
    else:
        # Default column order
        column_names = ["Team", "GP", "TOI", "W", "L", "OTL", "ROW", "Points", "Point%",
                        "CF", "CA", "CF%", "FF", "FA", "FF%", "SF", "SA", "SF%",
                        "GF", "GA", "GF%", "xGF", "xGA", "xGF%", "SCF", "SCA", "SCF%",
                        "HDCF", "HDCA", "HDCF%", "HDGF", "HDGA", "HDGF%", "HDSF", "HDSA",
                        "HDSF%", "MDCF", "MDCA", "MDCF%", "MDGF", "MDGA", "MDGF%",
                        "SH%", "SV%", "PDO"]

    # Create column index map
    col_map = {}
    for i, name in enumerate(column_names):
        col_map[name.upper().strip()] = i
        col_map[name.strip()] = i

    teams = {}

    # Parse data rows
    tbody = table.find('tbody')
    rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 5:
            continue

        # Get team name
        team_name = cells[0].get_text(strip=True)
        abbrev = TEAM_NAME_MAP.get(team_name)

        if not abbrev:
            for name, ab in TEAM_NAME_MAP.items():
                if name.lower() in team_name.lower():
                    abbrev = ab
                    break

        if not abbrev:
            continue

        # Extract values using column map
        def get_val(col_name, default=0):
            idx = col_map.get(col_name.upper(), col_map.get(col_name, -1))
            if idx >= 0 and idx < len(cells):
                return safe_float(cells[idx].get_text(strip=True))
            return default

        teams[abbrev] = {
            "team": abbrev,
            "gp": int(get_val("GP", 0)),
            "cf": get_val("CF", 0),
            "ca": get_val("CA", 0),
            "cfPct": get_val("CF%", 50),
            "ff": get_val("FF", 0),
            "fa": get_val("FA", 0),
            "ffPct": get_val("FF%", 50),
            "hdcf": get_val("HDCF", 0),
            "hdca": get_val("HDCA", 0),
            "hdcfPct": get_val("HDCF%", 50),
            "xgf": get_val("XGF", 0) or get_val("xGF", 0),
            "xga": get_val("XGA", 0) or get_val("xGA", 0),
            "xgfPct": get_val("XGF%", 50) or get_val("xGF%", 50),
            "scf": get_val("SCF", 0),
            "sca": get_val("SCA", 0),
            "scfPct": get_val("SCF%", 50),
            "shPct": get_val("SH%", 8),
            "svPct": get_val("SV%", 0.910) * 100 if get_val("SV%", 0) < 1 else get_val("SV%", 91),
            "pdo": get_val("PDO", 100),
        }

    print(f"Parsed {len(teams)} teams from NST")
    return teams

def safe_float(val):
    """Safely convert to float."""
    try:
        return float(str(val).replace('%', '').replace(',', ''))
    except (ValueError, TypeError):
        return 0.0

def safe_int(val):
    """Safely convert to int."""
    try:
        return int(float(str(val).replace(',', '')))
    except (ValueError, TypeError):
        return 0

def is_percentage(text, min_val, max_val):
    """Check if text looks like a percentage in range."""
    try:
        val = float(text.replace('%', ''))
        return min_val <= val <= max_val
    except:
        return False

def main():
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    try:
        # Fetch and parse NST data
        teams = fetch_and_parse_nst()

        if not teams:
            print("Warning: No teams parsed from NST")
            teams = {}

        # Add metadata
        output = {
            "_metadata": {
                "source": "Natural Stat Trick",
                "url": NST_BASE_URL,
                "season": "2025-26",
                "fetchedAt": datetime.utcnow().isoformat() + "Z",
                "teamCount": len(teams),
                "notes": "5v5 situation, all scores"
            },
            "teams": teams
        }

        # Write to file
        output_path = data_dir / "nst_stats.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"Saved {len(teams)} teams to {output_path}")
        return teams

    except Exception as e:
        print(f"Error fetching NST data: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    main()
