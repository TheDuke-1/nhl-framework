"""
Playoff Experience Loader - Load historical playoff data
=========================================================
Provides playoff experience features for teams based on
their recent playoff history.

Features:
- Playoff games played in last 3 years
- Series wins in last 3 years
- Deep run history (conf finals, cup finals)
- Recent Cup wins
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Data path
DATA_DIR = Path(__file__).parent.parent / "data" / "historical"

# Cache for loaded data
_playoff_cache: Dict[int, Dict[str, 'TeamPlayoffHistory']] = {}


@dataclass
class TeamPlayoffHistory:
    """Playoff history for a team in a given season."""
    team: str
    season: int

    # 3-year lookback metrics
    playoff_games_3yr: int
    playoff_series_3yr: int
    playoff_rounds_3yr: int
    playoff_appearances_3yr: int

    # 5-year deep run history
    conf_finals_5yr: int
    cup_finals_5yr: int
    cups_won_5yr: int

    # Current season results (for validation)
    current_rounds_won: int
    current_games_won: int
    current_games_lost: int

    @property
    def experience_score(self) -> float:
        """
        Composite playoff experience score.

        Weights:
        - Recent playoff games: 30%
        - Deep runs (conf finals+): 40%
        - Cup wins: 30%

        Returns value typically in range -1 to +2.
        """
        # Normalize components
        # Average playoff team plays ~10-15 games over 3 years
        games_norm = (self.playoff_games_3yr - 15) / 20

        # Conference finals appearances (0-3 expected over 5 years for good team)
        deep_norm = (self.conf_finals_5yr + self.cup_finals_5yr * 0.5) / 3

        # Cup wins (0-1 expected for dynasty, 0 for most)
        cup_norm = self.cups_won_5yr * 1.5

        return 0.30 * games_norm + 0.40 * deep_norm + 0.30 * cup_norm

    @property
    def is_experienced(self) -> bool:
        """Team has meaningful playoff experience."""
        return self.playoff_appearances_3yr >= 2

    @property
    def is_dynasty_candidate(self) -> bool:
        """Team has recent Cup success."""
        return self.cups_won_5yr >= 1 or self.cup_finals_5yr >= 2


def load_playoff_history(season: int) -> Dict[str, TeamPlayoffHistory]:
    """
    Load playoff history for all teams in a season.

    Args:
        season: The season year (e.g., 2024)

    Returns:
        Dictionary mapping team abbreviation to TeamPlayoffHistory
    """
    if season in _playoff_cache:
        return _playoff_cache[season]

    filepath = DATA_DIR / f"playoff_history_{season}.csv"

    if not filepath.exists():
        logger.warning(f"Playoff history file not found: {filepath}")
        return {}

    teams = {}
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                history = TeamPlayoffHistory(
                    team=row['team'],
                    season=int(row['season']),
                    playoff_games_3yr=int(row['playoff_games_3yr']),
                    playoff_series_3yr=int(row['playoff_series_3yr']),
                    playoff_rounds_3yr=int(row['playoff_rounds_3yr']),
                    playoff_appearances_3yr=int(row['playoff_appearances_3yr']),
                    conf_finals_5yr=int(row['conf_finals_5yr']),
                    cup_finals_5yr=int(row['cup_finals_5yr']),
                    cups_won_5yr=int(row['cups_won_5yr']),
                    current_rounds_won=int(row['current_rounds_won']),
                    current_games_won=int(row['current_games_won']),
                    current_games_lost=int(row['current_games_lost'])
                )
                teams[history.team] = history

        _playoff_cache[season] = teams
        logger.debug(f"Loaded playoff history for {len(teams)} teams in {season}")

    except Exception as e:
        logger.error(f"Error loading playoff history for {season}: {e}")
        return {}

    return teams


def get_team_playoff_history(team: str, season: int) -> Optional[TeamPlayoffHistory]:
    """
    Get playoff history for a specific team and season.

    Args:
        team: Team abbreviation (e.g., 'TBL')
        season: Season year

    Returns:
        TeamPlayoffHistory or None if not found
    """
    season_data = load_playoff_history(season)
    return season_data.get(team)


def calculate_playoff_experience_feature(team: str, season: int) -> float:
    """
    Calculate playoff experience feature for a team.

    This is the main entry point for feature engineering.

    Args:
        team: Team abbreviation
        season: Season year

    Returns:
        Experience score (typically -1 to +2)
    """
    history = get_team_playoff_history(team, season)

    if history is None:
        return 0.0

    return history.experience_score


def calculate_dynasty_feature(team: str, season: int) -> float:
    """
    Calculate dynasty/recent success feature.

    Measures how much recent championship-level success a team has.

    Returns:
        Dynasty score (0 to 2+)
    """
    history = get_team_playoff_history(team, season)

    if history is None:
        return 0.0

    # Weight recent cups heavily, cup finals moderately
    return history.cups_won_5yr * 1.0 + history.cup_finals_5yr * 0.3


def get_all_playoff_features(team: str, season: int) -> Dict[str, float]:
    """
    Get all playoff-related features for a team.

    Returns dictionary with all feature values.
    """
    history = get_team_playoff_history(team, season)

    if history is None:
        return {
            'playoff_experience': 0.0,
            'dynasty_score': 0.0,
            'deep_run_history': 0.0,
            'playoff_games_norm': 0.0
        }

    return {
        'playoff_experience': history.experience_score,
        'dynasty_score': calculate_dynasty_feature(team, season),
        'deep_run_history': (history.conf_finals_5yr + history.cup_finals_5yr) / 4,
        'playoff_games_norm': history.playoff_games_3yr / 30  # Normalize to ~0-1
    }


# Preload common seasons
def preload_seasons(start: int = 2010, end: int = 2024) -> None:
    """Preload playoff history for multiple seasons."""
    for season in range(start, end + 1):
        load_playoff_history(season)
    logger.info(f"Preloaded playoff history for seasons {start}-{end}")
