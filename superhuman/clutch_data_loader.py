"""
Clutch Data Loader - Load close game and overtime performance data
===================================================================
Loads clutch performance metrics for predicting playoff success.
Clutch performance is critical in playoffs where games are closer.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

from .config import normalize_team_abbrev as _normalize_team

logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data"
HISTORICAL_DIR = DATA_DIR / "historical"


@dataclass
class TeamClutchStats:
    """Clutch performance statistics for a team."""
    team: str
    season: int

    # One-goal games
    one_goal_wins: int
    one_goal_losses: int

    # Overtime performance
    ot_wins: int
    ot_losses: int
    so_wins: int
    so_losses: int

    # Comeback ability
    comeback_wins: int  # Won after trailing
    blown_leads: int  # Lost after leading
    trailing_after_2_wins: int  # Won after trailing after 2 periods

    @property
    def one_goal_games(self) -> int:
        """Total one-goal games played."""
        return self.one_goal_wins + self.one_goal_losses

    @property
    def one_goal_win_pct(self) -> float:
        """Win percentage in one-goal games."""
        if self.one_goal_games == 0:
            return 0.5
        return self.one_goal_wins / self.one_goal_games

    @property
    def ot_games(self) -> int:
        """Total overtime games."""
        return self.ot_wins + self.ot_losses + self.so_wins + self.so_losses

    @property
    def ot_win_pct(self) -> float:
        """Win percentage in OT/SO games."""
        if self.ot_games == 0:
            return 0.5
        return (self.ot_wins + self.so_wins) / self.ot_games

    @property
    def comeback_ratio(self) -> float:
        """Ratio of comeback wins to blown leads."""
        total = self.comeback_wins + self.blown_leads
        if total == 0:
            return 1.0
        return self.comeback_wins / total

    @property
    def clutch_score(self) -> float:
        """
        Composite clutch performance score.

        Components:
        - One-goal game win rate (35%)
        - OT/SO win rate (35%)
        - Comeback ratio (30%)

        Returns value normalized to roughly -1 to +1 range.
        """
        # One-goal component: center at 0.5, scale
        one_goal_component = (self.one_goal_win_pct - 0.5) * 2

        # OT component: center at 0.5, scale
        ot_component = (self.ot_win_pct - 0.5) * 2

        # Comeback component: center at 0.5, scale
        comeback_component = (self.comeback_ratio - 0.5) * 2

        # Weighted combination
        return (one_goal_component * 0.35 +
                ot_component * 0.35 +
                comeback_component * 0.30)


def load_clutch_data(season: int) -> Dict[str, TeamClutchStats]:
    """
    Load clutch performance data for a single season.

    Args:
        season: Season year (e.g., 2024)

    Returns:
        Dictionary mapping team abbreviation to TeamClutchStats
    """
    csv_path = HISTORICAL_DIR / f"clutch_{season}.csv"

    if not csv_path.exists():
        logger.debug(f"Clutch data file not found: {csv_path}")
        return {}

    teams = {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                stats = TeamClutchStats(
                    team=_normalize_team(row['team']),
                    season=int(row.get('season', season)),
                    one_goal_wins=int(row.get('one_goal_wins', 0)),
                    one_goal_losses=int(row.get('one_goal_losses', 0)),
                    ot_wins=int(row.get('ot_wins', 0)),
                    ot_losses=int(row.get('ot_losses', 0)),
                    so_wins=int(row.get('so_wins', 0)),
                    so_losses=int(row.get('so_losses', 0)),
                    comeback_wins=int(row.get('comeback_wins', 0)),
                    blown_leads=int(row.get('blown_leads', 0)),
                    trailing_after_2_wins=int(row.get('trailing_after_2_wins', 0))
                )
                teams[stats.team] = stats
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse clutch data for {row.get('team', 'unknown')}: {e}")
                continue

    logger.debug(f"Loaded clutch data for {len(teams)} teams in season {season}")
    return teams


# Cache for clutch data
_clutch_cache: Dict[int, Dict[str, TeamClutchStats]] = {}


def get_team_clutch_stats(team: str, season: int) -> Optional[TeamClutchStats]:
    """
    Get clutch performance stats for a specific team and season.

    Uses caching to avoid reloading files.
    """
    global _clutch_cache

    if season not in _clutch_cache:
        _clutch_cache[season] = load_clutch_data(season)

    return _clutch_cache.get(season, {}).get(team)


def calculate_clutch_feature(team: str, season: int) -> float:
    """
    Calculate the clutch_performance feature value for a team.

    Returns:
        Float value typically in range -1 to +1
    """
    stats = get_team_clutch_stats(team, season)

    if stats is None:
        return 0.0

    return stats.clutch_score


def clear_cache():
    """Clear the clutch data cache."""
    global _clutch_cache
    _clutch_cache = {}
