"""
Real Data Loader - Load actual NHL statistics
==============================================
Replaces synthetic data with real historical NHL data.

This loader:
1. Reads from CSV files in data/historical/
2. Merges standings with advanced stats
3. Creates TeamSeason objects with complete data
4. Falls back to API if files not available
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import asdict

from .data_models import TeamSeason
from .nhl_api import NHLDataClient, TeamStanding, TeamAdvancedStats
from .config import ALL_TEAMS, CONFERENCES

logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data"
HISTORICAL_DIR = DATA_DIR / "historical"


def load_real_historical_data(
    start_season: int = 2010,
    end_season: int = 2025
) -> List[TeamSeason]:
    """
    Load real historical NHL data from CSV files.

    Args:
        start_season: First season to load (e.g., 2010)
        end_season: Last season to load (e.g., 2025)

    Returns:
        List of TeamSeason objects with real NHL data
    """
    all_teams = []

    for season in range(start_season, end_season + 1):
        season_teams = _load_season_data(season)
        if season_teams:
            all_teams.extend(season_teams)
            logger.info(f"Loaded {len(season_teams)} teams for season {season}")
        else:
            logger.warning(f"No data available for season {season}")

    logger.info(f"Total loaded: {len(all_teams)} team-seasons")
    return all_teams


def _load_season_data(season: int) -> List[TeamSeason]:
    """Load data for a single season."""
    # Load standings
    standings = _load_standings_csv(season)
    if not standings:
        return []

    # Load advanced stats
    advanced = _load_advanced_csv(season)
    advanced_by_team = {a['team']: a for a in advanced} if advanced else {}

    # Merge into TeamSeason objects
    teams = []
    for s in standings:
        adv = advanced_by_team.get(s['team'], {})
        team = _merge_to_team_season(s, adv, season)
        if team:
            teams.append(team)

    return teams


def _load_standings_csv(season: int) -> List[Dict]:
    """Load standings from CSV file."""
    csv_path = HISTORICAL_DIR / f"standings_{season}.csv"

    if not csv_path.exists():
        logger.debug(f"Standings file not found: {csv_path}")
        return []

    rows = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def _load_advanced_csv(season: int) -> List[Dict]:
    """Load advanced stats from CSV file."""
    csv_path = HISTORICAL_DIR / f"advanced_{season}.csv"

    if not csv_path.exists():
        logger.debug(f"Advanced stats file not found: {csv_path}")
        return []

    rows = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only load 'all' situation stats
            if row.get('situation', 'all') == 'all':
                rows.append(row)

    return rows


def _merge_to_team_season(
    standings: Dict,
    advanced: Dict,
    season: int
) -> Optional[TeamSeason]:
    """Merge standings and advanced stats into TeamSeason."""
    try:
        team_abbr = standings['team']

        # Parse standings data
        games_played = int(standings.get('games_played', 82))
        wins = int(standings['wins'])
        losses = int(standings['losses'])
        ot_losses = int(standings.get('ot_losses', 0))
        points = int(standings['points'])
        goals_for = int(standings['goals_for'])
        goals_against = int(standings['goals_against'])

        # Parse home/away splits (for road_performance)
        home_wins = int(standings.get('home_wins', 0))
        home_losses = int(standings.get('home_losses', 0))
        away_wins = int(standings.get('away_wins', 0))
        away_losses = int(standings.get('away_losses', 0))

        # Parse advanced stats with defaults
        cf_pct = float(advanced.get('cf_pct', 50.0))
        ff_pct = float(advanced.get('ff_pct', 50.0))
        xgf = float(advanced.get('xgf', goals_for * 0.9))
        xga = float(advanced.get('xga', goals_against * 0.9))
        xgf_pct = float(advanced.get('xgf_pct', 50.0))
        hdcf_pct = float(advanced.get('hdcf_pct', 50.0))
        shooting_pct = float(advanced.get('shooting_pct', 10.0))
        save_pct = float(advanced.get('save_pct', 0.910))
        pdo = float(advanced.get('pdo', 100.0))
        gsax = float(advanced.get('gsax', 0.0))
        pp_pct = float(advanced.get('pp_pct', 20.0))
        pk_pct = float(advanced.get('pk_pct', 80.0))

        # Parse outcomes
        made_playoffs = standings.get('made_playoffs', '0')
        made_playoffs = made_playoffs in ('1', 'True', 'true', True, 1)

        won_cup = standings.get('won_cup', '0')
        won_cup = won_cup in ('1', 'True', 'true', True, 1)

        # Calculate derived metrics
        goal_differential = goals_for - goals_against

        # Create TeamSeason
        return TeamSeason(
            team=team_abbr,
            season=season,
            games_played=games_played,
            wins=wins,
            losses=losses,
            ot_losses=ot_losses,
            points=points,
            goals_for=goals_for,
            goals_against=goals_against,
            # goal_differential is a @property, calculated from goals_for - goals_against

            # Possession metrics
            cf_pct=cf_pct,
            ff_pct=ff_pct,
            sf_pct=(cf_pct + ff_pct) / 2,  # Approximate

            # Expected goals
            xgf=xgf,
            xga=xga,
            xgf_pct=xgf_pct,
            expected_goals_diff=xgf - xga,

            # High danger
            hdcf=int(advanced.get('hdcf', 0)) or int(xgf * 0.4),
            hdca=int(advanced.get('hdca', 0)) or int(xga * 0.4),
            hdcf_pct=hdcf_pct,

            # Goaltending
            save_pct=save_pct if save_pct < 1 else save_pct / 100,
            gsax=gsax,

            # Shooting
            shooting_pct=shooting_pct,
            pdo=pdo,

            # Special teams
            pp_pct=pp_pct,
            pk_pct=pk_pct,

            # Home/away for road_performance calculation
            home_wins=home_wins,
            home_losses=home_losses,
            home_ot_losses=int(standings.get('home_ot_losses', 0)),
            away_wins=away_wins,
            away_losses=away_losses,
            away_ot_losses=int(standings.get('away_ot_losses', 0)),

            # Outcomes
            made_playoffs=made_playoffs,
            won_cup=won_cup,

            # These will be calculated later or from other sources
            recent_form=0.0,  # Needs game-by-game data
            star_ppg=0.0,     # Needs player data
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse team data for {standings.get('team', 'unknown')}: {e}")
        return None


def load_real_training_data() -> List[TeamSeason]:
    """
    Load real training data from available historical seasons.

    Returns training data from CSV files, falling back to API or
    synthetic data if needed.
    """
    # Try to load real data
    real_data = load_real_historical_data(start_season=2015, end_season=2024)

    if len(real_data) >= 100:
        logger.info(f"Using {len(real_data)} real historical team-seasons for training")
        return real_data

    # Fall back to synthetic if insufficient real data
    logger.warning("Insufficient real data, falling back to synthetic generation")
    from .data_loader import synthesize_training_data
    return synthesize_training_data()


def get_available_seasons() -> List[int]:
    """Get list of seasons with available data."""
    available = []

    for season in range(2005, 2030):
        standings_path = HISTORICAL_DIR / f"standings_{season}.csv"
        if standings_path.exists():
            available.append(season)

    return available


def validate_data_quality(teams: List[TeamSeason]) -> Dict:
    """
    Validate data quality and return report.

    Checks for:
    - Missing values
    - Zero-variance features
    - Outliers
    - Data completeness
    """
    import numpy as np

    report = {
        'total_samples': len(teams),
        'seasons': sorted(set(t.season for t in teams)),
        'teams_per_season': {},
        'missing_values': {},
        'zero_variance': [],
        'outliers': [],
    }

    # Count teams per season
    for team in teams:
        if team.season not in report['teams_per_season']:
            report['teams_per_season'][team.season] = 0
        report['teams_per_season'][team.season] += 1

    # Check numeric fields
    numeric_fields = [
        'points', 'goal_differential', 'cf_pct', 'ff_pct', 'xgf', 'xga',
        'xgf_pct', 'hdcf_pct', 'save_pct', 'shooting_pct', 'pdo',
        'pp_pct', 'pk_pct', 'gsax'
    ]

    for field in numeric_fields:
        values = [getattr(t, field, None) for t in teams]
        values = [v for v in values if v is not None]

        if not values:
            report['missing_values'][field] = len(teams)
            continue

        values = np.array(values)
        std = np.std(values)

        if std == 0:
            report['zero_variance'].append(field)

        # Check for outliers (|z| > 4)
        z_scores = (values - np.mean(values)) / std if std > 0 else np.zeros_like(values)
        n_outliers = np.sum(np.abs(z_scores) > 4)
        if n_outliers > 0:
            report['outliers'].append({
                'field': field,
                'count': int(n_outliers),
                'min': float(values.min()),
                'max': float(values.max())
            })

    return report


# Convenience function to match old API
def load_historical_data() -> List[TeamSeason]:
    """Load historical data - tries real data first, falls back to synthetic."""
    return load_real_training_data()
