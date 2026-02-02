"""
Superhuman NHL Prediction System - Configuration
================================================
Central configuration for the prediction system.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SUPERHUMAN_DIR = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORICAL_DIR = DATA_DIR / "historical"

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

# Historical team name mappings (teams that moved/renamed)
HISTORICAL_TEAM_MAP = {
    "ARI": "UTA",  # Arizona -> Utah (2024)
    "PHX": "UTA",  # Phoenix -> Arizona -> Utah
    "ATL": "WPG",  # Atlanta -> Winnipeg (2011)
    "HFD": "CAR",  # Hartford -> Carolina
    "QUE": "COL",  # Quebec -> Colorado
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


@dataclass
class FeatureWeights:
    """Placeholder for optimized weights - will be set by regression."""
    goal_differential: float = 0.0
    territorial_dominance: float = 0.0
    shot_quality_premium: float = 0.0
    goaltending: float = 0.0
    special_teams: float = 0.0
    road_performance: float = 0.0
    recent_form: float = 0.0
    depth: float = 0.0
    star_power: float = 0.0
    clutch: float = 0.0


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


def normalize_team_abbrev(abbrev: str) -> str:
    """Normalize historical team abbreviations."""
    return HISTORICAL_TEAM_MAP.get(abbrev, abbrev)
