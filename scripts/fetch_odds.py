#!/usr/bin/env python3
"""
Fetch playoff probabilities and Cup odds from public sources.
Outputs: data/odds.json

Sources:
  - Hockey-Reference playoff probability simulations
    (Playoffs%, Division%, Win Cup% for all 32 teams)

These are model-based probabilities from 1000+ season simulations,
not sportsbook odds. They update daily during the regular season.
"""

import json
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

from config import NST_TEAM_MAP as TEAM_NAME_MAP
from utils import fetch_html

HOCKEY_REF_URL = "https://www.hockey-reference.com/friv/playoff_prob.fcgi"


def fetch_hockey_ref_probabilities():
    """Scrape Hockey-Reference playoff probability page."""
    print("Fetching Hockey-Reference playoff probabilities...")

    html = fetch_html(HOCKEY_REF_URL)
    soup = BeautifulSoup(html, "lxml")
    teams = {}

    # Hockey-Reference organizes by division — find all team rows across all tables
    # Each division table has id like "standings_EAS_ATL", "standings_WES_CEN", etc.
    tables = soup.find_all("table")

    for table in tables:
        # Get column headers for this table
        thead = table.find("thead")
        if not thead:
            continue

        header_cells = thead.find_all("th")
        col_names = [h.get_text(strip=True) for h in header_cells]

        # Build column index map
        col_map = {}
        for i, name in enumerate(col_names):
            col_map[name] = i

        # Must have the key probability columns
        if "Playoffs" not in col_map and "Make Playoffs" not in col_map:
            continue

        tbody = table.find("tbody")
        if not tbody:
            continue

        for row in tbody.find_all("tr"):
            # Skip header rows mixed into tbody
            if row.get("class") and "thead" in row.get("class", []):
                continue

            cells = row.find_all(["td", "th"])
            if len(cells) < 5:
                continue

            # Team name — look for "Team" column or use first th
            team_name = ""
            team_idx = col_map.get("Team", col_map.get("Tm", -1))
            if team_idx >= 0 and team_idx < len(cells):
                # The team cell often contains a link
                link = cells[team_idx].find("a")
                if link:
                    team_name = link.get_text(strip=True)
                else:
                    team_name = cells[team_idx].get_text(strip=True)
            else:
                # Try first cell
                link = cells[0].find("a")
                if link:
                    team_name = link.get_text(strip=True)
                else:
                    team_name = cells[0].get_text(strip=True)

            abbrev = TEAM_NAME_MAP.get(team_name)
            if not abbrev:
                # Try partial match
                for name, ab in TEAM_NAME_MAP.items():
                    if name.lower() in team_name.lower() or team_name.lower() in name.lower():
                        abbrev = ab
                        break

            if not abbrev:
                continue

            def get_val(col_name, default=0.0):
                idx = col_map.get(col_name, -1)
                if idx >= 0 and idx < len(cells):
                    text = cells[idx].get_text(strip=True)
                    text = text.replace("%", "").replace(",", "")
                    try:
                        return float(text)
                    except (ValueError, TypeError):
                        return default
                return default

            # Extract probabilities
            playoff_pct = get_val("Playoffs", 0) or get_val("Make Playoffs", 0)
            division_pct = get_val("Division", 0) or get_val("Div", 0)
            cup_pct = get_val("Win Cup", 0) or get_val("Cup", 0)

            # Extract projected stats
            proj_w = get_val("W", 0)
            proj_l = get_val("L", 0)
            proj_ol = get_val("OL", 0)
            proj_pts = get_val("PTS", 0)

            # Convert Cup% to implied American odds for reference
            # Formula: if prob > 50%, odds = -(prob/(1-prob))*100
            #          if prob < 50%, odds = +((1-prob)/prob)*100
            implied_odds = 0
            if cup_pct > 0 and cup_pct < 100:
                cup_decimal = cup_pct / 100
                if cup_decimal >= 0.5:
                    implied_odds = int(-(cup_decimal / (1 - cup_decimal)) * 100)
                else:
                    implied_odds = int(((1 - cup_decimal) / cup_decimal) * 100)

            teams[abbrev] = {
                "team": abbrev,
                "playoffPct": round(playoff_pct, 1),
                "divisionPct": round(division_pct, 1),
                "cupPct": round(cup_pct, 1),
                "impliedCupOdds": implied_odds,
                "projW": round(proj_w, 1),
                "projL": round(proj_l, 1),
                "projOL": round(proj_ol, 1),
                "projPts": round(proj_pts, 1),
            }

    print("Parsed probabilities for %d teams" % len(teams))
    return teams


def main():
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    try:
        teams = fetch_hockey_ref_probabilities()

        if not teams:
            print("Error: No teams parsed from Hockey-Reference")
            return {}

        # Build output
        output = {
            "_metadata": {
                "source": "Hockey-Reference Playoff Probabilities",
                "url": HOCKEY_REF_URL,
                "type": "model-based (1000+ season simulations)",
                "fetchedAt": datetime.utcnow().isoformat() + "Z",
                "teamCount": len(teams),
                "notes": "Probabilities are simulation-based, not sportsbook odds. "
                         "impliedCupOdds converts cup probability to American odds format."
            },
            "teams": teams
        }

        # Write current odds
        output_path = data_dir / "odds.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        print("Saved odds to %s" % output_path)

        # Save historical snapshot
        hist_dir = data_dir / "historical" / "odds"
        hist_dir.mkdir(parents=True, exist_ok=True)
        snapshot_name = "odds_%s.json" % datetime.utcnow().strftime("%Y%m%d")
        snapshot_path = hist_dir / snapshot_name
        with open(snapshot_path, "w") as f:
            json.dump(output, f, indent=2)
        print("Saved snapshot to %s" % snapshot_path)

        # Print summary
        print("\nTop 10 Cup Contenders:")
        sorted_teams = sorted(teams.values(), key=lambda t: -t["cupPct"])
        for i, t in enumerate(sorted_teams[:10], 1):
            odds_str = "+%d" % t["impliedCupOdds"] if t["impliedCupOdds"] > 0 else str(t["impliedCupOdds"])
            print("  %2d. %-4s  Cup: %5.1f%%  (%s)  Playoffs: %5.1f%%  Proj: %.0f pts" % (
                i, t["team"], t["cupPct"], odds_str, t["playoffPct"], t["projPts"]))

        return teams

    except Exception as e:
        print("Error fetching odds: %s" % e)
        import traceback
        traceback.print_exc()
        return {}


if __name__ == "__main__":
    main()
