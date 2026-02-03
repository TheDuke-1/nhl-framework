"""
Superhuman NHL Prediction System - Configuration
================================================
Central configuration for the prediction system.
"""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SUPERHUMAN_DIR = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORICAL_DIR = DATA_DIR / "historical" / "verified"

# Seasons to use for training/testing
TRAINING_SEASONS = list(range(2010, 2023))  # 2010-2022
TEST_SEASONS = list(range(2023, 2026))       # 2023-2025
ALL_SEASONS = TRAINING_SEASONS + TEST_SEASONS

# Current season
CURRENT_SEASON = 2026

# Model parameters
N_SIMULATIONS = 50000  # Monte Carlo simulations
RANDOM_SEED = 42

# Feature engineering
TIME_DECAY_HALF_LIFE = 20  # Games for weight to decay by 50%

# Playoff structure
PLAYOFF_TEAMS_PER_CONFERENCE = 8
GAMES_IN_SEASON = 82

# Team abbreviations
ALL_TEAMS = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL",
    "DAL", "DET", "EDM", "FLA", "LA", "MIN", "MTL", "NJ",
    "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJ",
    "STL", "TB", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH"
]

# Historical team name mappings (teams that moved/renamed).
# Maps old abbreviations to current franchise abbreviation for continuity.
# NOTE: ARI→UTA mapping merges pre-2024 Arizona data with Utah. This preserves
# franchise continuity for the model but may add noise since rosters, coaching,
# and venue changed completely. Set MERGE_RELOCATED_FRANCHISES=False to disable.
MERGE_RELOCATED_FRANCHISES = True

HISTORICAL_TEAM_MAP = {
    "ARI": "UTA",  # Arizona -> Utah (2024) — controlled by MERGE_RELOCATED_FRANCHISES
    "PHX": "UTA",  # Phoenix -> Arizona -> Utah
    "ATL": "WPG",  # Atlanta -> Winnipeg (2011)
    "HFD": "CAR",  # Hartford -> Carolina
    "QUE": "COL",  # Quebec -> Colorado
    "LAK": "LA",   # Alternate Kings abbreviation
    "NJD": "NJ",   # Alternate Devils abbreviation
    "SJS": "SJ",   # Alternate Sharks abbreviation
    "TBL": "TB",   # Alternate Lightning abbreviation
}

# Conference/Division structure (current)
CONFERENCES = {
    "East": {
        "Atlantic": ["BOS", "BUF", "DET", "FLA", "MTL", "OTT", "TB", "TOR"],
        "Metropolitan": ["CAR", "CBJ", "NJ", "NYI", "NYR", "PHI", "PIT", "WSH"]
    },
    "West": {
        "Central": ["CHI", "COL", "DAL", "MIN", "NSH", "STL", "UTA", "WPG"],
        "Pacific": ["ANA", "CGY", "EDM", "LA", "SEA", "SJ", "VAN", "VGK"]
    }
}


def parse_bool(value) -> bool:
    """Parse a boolean from CSV data (handles '1', 'True', 'true', True, 1)."""
    return value in ('1', 'True', 'true', True, 1)


def get_team_conference(team: str) -> str:
    """Get conference for a team."""
    for conf, divisions in CONFERENCES.items():
        for div, teams in divisions.items():
            if team in teams:
                return conf
    return "Unknown"


def get_team_division(team: str) -> str:
    """Get division for a team."""
    for conf, divisions in CONFERENCES.items():
        for div, teams in divisions.items():
            if team in teams:
                return div
    return "Unknown"


def select_conference_playoff_teams(conf_name, team_pts):
    """
    Select 8 playoff teams from a conference using real NHL rules.

    NHL qualification: top 3 per division + best 2 remaining as wildcards.

    Args:
        conf_name: "East" or "West"
        team_pts: dict mapping team code -> points (actual or projected)

    Returns:
        List of (team_code, points) sorted by points descending
    """
    divisions = CONFERENCES.get(conf_name, {})
    qualified = []
    wildcard_pool = []
    for div_team_codes in divisions.values():
        div_teams = sorted(
            [(code, team_pts.get(code, 0.0)) for code in div_team_codes],
            key=lambda x: -x[1]
        )
        qualified.extend(div_teams[:3])
        wildcard_pool.extend(div_teams[3:])
    wildcard_pool.sort(key=lambda x: -x[1])
    qualified.extend(wildcard_pool[:2])
    qualified.sort(key=lambda x: -x[1])
    return qualified


def normalize_team_abbrev(abbrev: str) -> str:
    """Normalize historical team abbreviations.

    When MERGE_RELOCATED_FRANCHISES is False, only normalizes alternate
    abbreviation formats (LAK→LA, etc.) without merging relocated teams.
    """
    if not MERGE_RELOCATED_FRANCHISES and abbrev in ("ARI", "PHX", "ATL"):
        # Don't merge relocated franchises — only normalize abbrev formats
        return abbrev
    return HISTORICAL_TEAM_MAP.get(abbrev, abbrev)
