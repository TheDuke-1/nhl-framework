"""
Recent Form Data Loader - Load game-by-game performance data
=============================================================
Loads recent game results for calculating momentum/form features.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data"
HISTORICAL_DIR = DATA_DIR / "historical"


@dataclass
class TeamRecentForm:
    """Recent form statistics for a team."""
    team: str
    season: int

    # Last 10 games performance
    last_10_wins: int
    last_10_losses: int
    last_10_ot_losses: int
    last_10_gf: int  # Goals for
    last_10_ga: int  # Goals against

    # Streak info
    streak_type: str  # 'W' for win streak, 'L' for loss streak
    streak_length: int

    @property
    def last_10_points(self) -> int:
        """Points earned in last 10 games (2 for W, 1 for OTL, 0 for L)."""
        return (self.last_10_wins * 2) + self.last_10_ot_losses

    @property
    def last_10_win_pct(self) -> float:
        """Win percentage in last 10 games."""
        total = self.last_10_wins + self.last_10_losses + self.last_10_ot_losses
        return self.last_10_wins / total if total > 0 else 0.0

    @property
    def last_10_gd(self) -> int:
        """Goal differential in last 10 games."""
        return self.last_10_gf - self.last_10_ga

    @property
    def momentum_score(self) -> float:
        """
        Calculate momentum score based on recent performance.

        Combines:
        - Win percentage (weighted 40%)
        - Goal differential per game (weighted 30%)
        - Current streak (weighted 30%)

        Returns value in roughly -2 to +2 range.
        """
        # Win percentage component (center at 0.5)
        win_pct_component = (self.last_10_win_pct - 0.5) * 2

        # GD per game component (center at 0)
        gd_per_game = self.last_10_gd / 10
        gd_component = gd_per_game / 1.5  # Scale to roughly -1 to +1

        # Streak component
        if self.streak_type == 'W':
            streak_component = min(self.streak_length, 5) * 0.15
        else:
            streak_component = -min(self.streak_length, 5) * 0.15

        # Combine components
        return (win_pct_component * 0.4) + (gd_component * 0.3) + (streak_component * 0.3)


def load_recent_form_data(season: int) -> Dict[str, TeamRecentForm]:
    """
    Load recent form data for a single season.

    Args:
        season: Season year (e.g., 2024)

    Returns:
        Dictionary mapping team abbreviation to TeamRecentForm
    """
    csv_path = HISTORICAL_DIR / f"recent_form_{season}.csv"

    if not csv_path.exists():
        logger.debug(f"Recent form file not found: {csv_path}")
        return {}

    teams = {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                form = TeamRecentForm(
                    team=row['team'],
                    season=int(row.get('season', season)),
                    last_10_wins=int(row.get('last_10_wins', 0)),
                    last_10_losses=int(row.get('last_10_losses', 0)),
                    last_10_ot_losses=int(row.get('last_10_ot_losses', 0)),
                    last_10_gf=int(row.get('last_10_gf', 0)),
                    last_10_ga=int(row.get('last_10_ga', 0)),
                    streak_type=row.get('streak_type', 'W'),
                    streak_length=int(row.get('streak_length', 0))
                )
                teams[form.team] = form
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse recent form for {row.get('team', 'unknown')}: {e}")
                continue

    logger.debug(f"Loaded recent form for {len(teams)} teams in season {season}")
    return teams


# Cache for recent form data
_recent_form_cache: Dict[int, Dict[str, TeamRecentForm]] = {}


def get_team_recent_form(team: str, season: int) -> Optional[TeamRecentForm]:
    """
    Get recent form data for a specific team and season.

    Uses caching to avoid reloading files.
    """
    global _recent_form_cache

    if season not in _recent_form_cache:
        _recent_form_cache[season] = load_recent_form_data(season)

    return _recent_form_cache.get(season, {}).get(team)


def calculate_recent_form_feature(team: str, season: int) -> float:
    """
    Calculate the recent_form feature value for a team.

    Returns:
        Float value typically in range -1 to +1
    """
    form = get_team_recent_form(team, season)

    if form is None:
        return 0.0

    return form.momentum_score


def clear_cache():
    """Clear the recent form cache."""
    global _recent_form_cache
    _recent_form_cache = {}
