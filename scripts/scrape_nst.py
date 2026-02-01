#!/usr/bin/env python3
"""
Scrape Natural Stat Trick for advanced analytics (HDCF%, CF%, PDO, etc.)
Outputs: data/nst_stats.json

Note: Please support Natural Stat Trick via Patreon if using regularly.
Rate limiting is implemented to be respectful of their servers.
"""

import json
import time
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

from config import NST_TEAM_MAP as TEAM_NAME_MAP, NST_API, SEASON_ID
from utils import fetch_html, safe_float

# Natural Stat Trick URLs (NOTE: www. prefix is required!)
NST_BASE_URL = NST_API["base_url"]

def fetch_and_parse_nst():
    """Fetch all NST data with proper column parsing."""
    print("Fetching Natural Stat Trick data...")

    params = {
        "fromseason": SEASON_ID,
        "thruseason": SEASON_ID,
        "stype": "2",
        "sit": "5v5",
        "score": "all",
        "rate": "n",
        "team": "all",
        "loc": "B",
        "gpf": "410"
    }

    html = fetch_html(NST_BASE_URL, params=params)
    soup = BeautifulSoup(html, 'lxml')

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

        # Get team name — NST has a blank first column (row number),
        # so the team name is at the column mapped to "TEAM" header
        team_idx = col_map.get("TEAM", col_map.get("Team", 1))
        team_name = cells[team_idx].get_text(strip=True) if team_idx < len(cells) else ""
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

        # Get xGF/xGA — NST provides these at 5v5
        xgf_val = get_val("XGF", 0) or get_val("xGF", 0)
        xga_val = get_val("XGA", 0) or get_val("xGA", 0)

        # Get goals for/against at 5v5 (for GSAx calculation)
        gf_5v5 = get_val("GF", 0)
        ga_5v5 = get_val("GA", 0)

        # Calculate GSAx = xGA - actual GA (positive = saved more than expected)
        gsax = round(xga_val - ga_5v5, 2) if xga_val > 0 and ga_5v5 > 0 else 0.0

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
            "xgf": xgf_val,
            "xga": xga_val,
            "xgfPct": get_val("XGF%", 50) or get_val("xGF%", 50),
            "gsax": gsax,
            "scf": get_val("SCF", 0),
            "sca": get_val("SCA", 0),
            "scfPct": get_val("SCF%", 50),
            "shPct": get_val("SH%", 8),
            "svPct": _scale_sv_pct(get_val("SV%", 0)),
            "pdo": get_val("PDO", 100),
        }

    print(f"Parsed {len(teams)} teams from NST")
    return teams

def _scale_sv_pct(raw):
    """Convert SV% to percentage scale (e.g., 91.5), handling both ratio and pct formats."""
    if raw == 0:
        return 0
    if raw < 1:  # Ratio format like 0.915
        return round(raw * 100, 2)
    return round(raw, 2)  # Already percentage like 91.5

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
