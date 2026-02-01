#!/usr/bin/env python3
"""
Shared configuration for NHL Playoff Framework data pipeline.
Central location for season settings, team mappings, and API endpoints.
"""

from datetime import datetime
from pathlib import Path

# =============================================================================
# SEASON CONFIGURATION - UPDATE THIS EACH SEASON
# =============================================================================
CURRENT_SEASON = "2025-26"
SEASON_ID = "20252026"  # NHL API format
SEASON_START_YEAR = 2025
SEASON_END_YEAR = 2026

# =============================================================================
# PATHS
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# =============================================================================
# API ENDPOINTS
# =============================================================================
NHL_API = {
    "standings": "https://api-web.nhle.com/v1/standings/now",
    "schedule": "https://api-web.nhle.com/v1/schedule/now",
    "team_stats": f"https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId={SEASON_ID}",
}

NST_API = {
    "base_url": "https://www.naturalstattrick.com/teamtable.php",
    "params": {
        "fromseason": SEASON_ID,
        "thruseason": SEASON_ID,
        "stype": "2",  # Regular season
        "sit": "5v5",
        "score": "all",
        "rate": "n",
        "team": "all",
        "loc": "B",
        "gpf": "410"
    }
}

MONEYPUCK_API = {
    "teams_url": f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{SEASON_END_YEAR}/regular/teams.csv",
    "teams_page": "https://moneypuck.com/teams.htm"
}

# =============================================================================
# REQUEST SETTINGS
# =============================================================================
REQUEST_TIMEOUT = 30  # seconds
REQUEST_RETRIES = 3
REQUEST_RETRY_DELAY = 5  # seconds
REQUEST_DELAY = 2  # seconds between requests (rate limiting)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# =============================================================================
# TEAM MAPPINGS
# =============================================================================
# Standard 3-letter abbreviations used across all data sources
ALL_TEAMS = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL",
    "DAL", "DET", "EDM", "FLA", "LA", "MIN", "MTL", "NJ",
    "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJ",
    "STL", "TB", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH"
]

# NHL API uses different abbreviations
NHL_API_TEAM_MAP = {
    "ANA": "ANA", "BOS": "BOS", "BUF": "BUF", "CAR": "CAR",
    "CBJ": "CBJ", "CGY": "CGY", "CHI": "CHI", "COL": "COL",
    "DAL": "DAL", "DET": "DET", "EDM": "EDM", "FLA": "FLA",
    "LAK": "LA", "MIN": "MIN", "MTL": "MTL", "NJD": "NJ",
    "NSH": "NSH", "NYI": "NYI", "NYR": "NYR", "OTT": "OTT",
    "PHI": "PHI", "PIT": "PIT", "SEA": "SEA", "SJS": "SJ",
    "STL": "STL", "TBL": "TB", "TOR": "TOR", "UTA": "UTA",
    "VAN": "VAN", "VGK": "VGK", "WPG": "WPG", "WSH": "WSH"
}

# Natural Stat Trick team names
NST_TEAM_MAP = {
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
    "Utah Mammoth": "UTA",
    "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK",
    "Winnipeg Jets": "WPG",
    "Washington Capitals": "WSH",
}

# Team full names for display
TEAM_NAMES = {
    "ANA": "Anaheim Ducks",
    "BOS": "Boston Bruins",
    "BUF": "Buffalo Sabres",
    "CAR": "Carolina Hurricanes",
    "CBJ": "Columbus Blue Jackets",
    "CGY": "Calgary Flames",
    "CHI": "Chicago Blackhawks",
    "COL": "Colorado Avalanche",
    "DAL": "Dallas Stars",
    "DET": "Detroit Red Wings",
    "EDM": "Edmonton Oilers",
    "FLA": "Florida Panthers",
    "LA": "Los Angeles Kings",
    "MIN": "Minnesota Wild",
    "MTL": "Montreal Canadiens",
    "NJ": "New Jersey Devils",
    "NSH": "Nashville Predators",
    "NYI": "New York Islanders",
    "NYR": "New York Rangers",
    "OTT": "Ottawa Senators",
    "PHI": "Philadelphia Flyers",
    "PIT": "Pittsburgh Penguins",
    "SEA": "Seattle Kraken",
    "SJ": "San Jose Sharks",
    "STL": "St. Louis Blues",
    "TB": "Tampa Bay Lightning",
    "TOR": "Toronto Maple Leafs",
    "UTA": "Utah Mammoth",
    "VAN": "Vancouver Canucks",
    "VGK": "Vegas Golden Knights",
    "WPG": "Winnipeg Jets",
    "WSH": "Washington Capitals",
}

# Conference and Division assignments
TEAM_INFO = {
    "ANA": {"conf": "West", "div": "Pacific"},
    "BOS": {"conf": "East", "div": "Atlantic"},
    "BUF": {"conf": "East", "div": "Atlantic"},
    "CAR": {"conf": "East", "div": "Metropolitan"},
    "CBJ": {"conf": "East", "div": "Metropolitan"},
    "CGY": {"conf": "West", "div": "Pacific"},
    "CHI": {"conf": "West", "div": "Central"},
    "COL": {"conf": "West", "div": "Central"},
    "DAL": {"conf": "West", "div": "Central"},
    "DET": {"conf": "East", "div": "Atlantic"},
    "EDM": {"conf": "West", "div": "Pacific"},
    "FLA": {"conf": "East", "div": "Atlantic"},
    "LA": {"conf": "West", "div": "Pacific"},
    "MIN": {"conf": "West", "div": "Central"},
    "MTL": {"conf": "East", "div": "Atlantic"},
    "NJ": {"conf": "East", "div": "Metropolitan"},
    "NSH": {"conf": "West", "div": "Central"},
    "NYI": {"conf": "East", "div": "Metropolitan"},
    "NYR": {"conf": "East", "div": "Metropolitan"},
    "OTT": {"conf": "East", "div": "Atlantic"},
    "PHI": {"conf": "East", "div": "Metropolitan"},
    "PIT": {"conf": "East", "div": "Metropolitan"},
    "SEA": {"conf": "West", "div": "Pacific"},
    "SJ": {"conf": "West", "div": "Pacific"},
    "STL": {"conf": "West", "div": "Central"},
    "TB": {"conf": "East", "div": "Atlantic"},
    "TOR": {"conf": "East", "div": "Atlantic"},
    "UTA": {"conf": "West", "div": "Central"},
    "VAN": {"conf": "West", "div": "Pacific"},
    "VGK": {"conf": "West", "div": "Pacific"},
    "WPG": {"conf": "West", "div": "Central"},
    "WSH": {"conf": "East", "div": "Metropolitan"},
}

# =============================================================================
# DATA FRESHNESS THRESHOLDS (in hours)
# =============================================================================
FRESHNESS_THRESHOLDS = {
    "nhl_standings": 24,      # Update daily
    "moneypuck_stats": 48,    # Update every 2 days
    "nst_stats": 72,          # Update every 3 days
    "odds": 24,               # Update daily
    "teams": 24,              # Merged file should be fresh
}

# =============================================================================
# VALIDATION RANGES
# =============================================================================
VALID_RANGES = {
    "hdcfPct": (35, 65),      # HDCF% should be roughly 35-65%
    "cfPct": (40, 60),        # CF% should be roughly 40-60%
    "pdo": (95, 105),         # PDO should be roughly 95-105
    "ppPct": (10, 35),        # PP% should be roughly 10-35%
    "pkPct": (65, 95),        # PK% should be roughly 65-95%
    "gsax": (-40, 40),        # GSAx typically -30 to +30, elite goalies can exceed
    "pts": (0, 150),          # Points 0-150 in a season
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_data_file_path(filename):
    """Get the full path to a data file."""
    return DATA_DIR / filename

def ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)

def get_current_timestamp():
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"

def normalize_team_abbrev(abbrev, source="nhl"):
    """Normalize team abbreviation to standard format."""
    if source == "nhl":
        return NHL_API_TEAM_MAP.get(abbrev, abbrev)
    return abbrev

def get_team_name(abbrev):
    """Get full team name from abbreviation."""
    return TEAM_NAMES.get(abbrev, abbrev)

def get_team_info(abbrev):
    """Get team conference and division info."""
    return TEAM_INFO.get(abbrev, {"conf": "Unknown", "div": "Unknown"})


if __name__ == "__main__":
    # Print configuration summary
    print(f"NHL Playoff Framework Configuration")
    print(f"=" * 40)
    print(f"Season: {CURRENT_SEASON}")
    print(f"Season ID: {SEASON_ID}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Teams: {len(ALL_TEAMS)}")
    print(f"")
    print(f"API Endpoints:")
    for name, url in NHL_API.items():
        print(f"  - {name}: {url[:60]}...")
