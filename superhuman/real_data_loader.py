"""
Real Data Loader - Load actual NHL statistics
==============================================
Replaces synthetic data with real historical NHL data.

This loader:
1. Reads from CSV files in data/historical/
2. Merges standings with advanced stats
3. Loads playoff history for playoff_rounds_won
4. Normalizes team abbreviations across all sources
5. Creates TeamSeason objects with complete data
6. Falls back to API if files not available
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from .data_models import TeamSeason
from .config import DATA_DIR, HISTORICAL_DIR, normalize_team_abbrev as _normalize_team, parse_bool

logger = logging.getLogger(__name__)


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
    """Load data for a single season from all available sources."""
    # Load standings (required)
    standings = _load_standings_csv(season)
    if not standings:
        return []

    # Load advanced stats
    advanced = _load_advanced_csv(season)
    advanced_by_team = {_normalize_team(a['team']): a for a in advanced} if advanced else {}

    # Load playoff history for playoff_rounds_won
    playoff_history = _load_playoff_history_csv(season)

    # Merge into TeamSeason objects
    teams = []
    for s in standings:
        team_abbr = _normalize_team(s['team'])
        adv = advanced_by_team.get(team_abbr, {})
        playoff = playoff_history.get(team_abbr, {})
        team = _merge_to_team_season(s, adv, playoff, season)
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


def _load_playoff_history_csv(season: int) -> Dict[str, Dict]:
    """
    Load playoff history for a season.

    Returns dict mapping team abbreviation to playoff history fields.
    Key field: current_rounds_won (used for playoff_rounds_won in training).
    """
    csv_path = HISTORICAL_DIR / f"playoff_history_{season}.csv"

    if not csv_path.exists():
        logger.debug(f"Playoff history file not found: {csv_path}")
        return {}

    teams = {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                team = _normalize_team(row['team'])
                teams[team] = {
                    'current_rounds_won': int(row.get('current_rounds_won', 0)),
                    'current_games_won': int(row.get('current_games_won', 0)),
                    'current_games_lost': int(row.get('current_games_lost', 0)),
                }
            except (KeyError, ValueError) as e:
                logger.debug(f"Failed to parse playoff history for {row.get('team', '?')}: {e}")

    return teams


def _merge_to_team_season(
    standings: Dict,
    advanced: Dict,
    playoff: Dict,
    season: int
) -> Optional[TeamSeason]:
    """Merge standings, advanced stats, and playoff history into TeamSeason."""
    try:
        team_abbr = _normalize_team(standings['team'])

        # Parse standings data
        games_played = int(standings.get('games_played', 82))
        wins = int(standings['wins'])
        losses = int(standings['losses'])
        ot_losses = int(standings.get('ot_losses', 0))
        points = int(standings['points'])
        goals_for = int(standings['goals_for'])
        goals_against = int(standings['goals_against'])

        # Parse home/away splits — new format (2015+) has these, old (2010-2014) doesn't
        home_wins = int(standings.get('home_wins', 0))
        home_losses = int(standings.get('home_losses', 0))
        home_ot_losses = int(standings.get('home_ot_losses', 0))
        away_wins = int(standings.get('away_wins', 0))
        away_losses = int(standings.get('away_losses', 0))
        away_ot_losses = int(standings.get('away_ot_losses', 0))

        # For old format without home/away splits, estimate from totals
        if home_wins == 0 and away_wins == 0 and wins > 0:
            home_wins = int(wins * 0.55)  # ~55% of wins at home is NHL average
            away_wins = wins - home_wins
            home_losses = int(losses * 0.45)
            away_losses = losses - home_losses
            home_ot_losses = int(ot_losses * 0.5)
            away_ot_losses = ot_losses - home_ot_losses

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

        # Parse outcomes from standings
        made_playoffs = parse_bool(standings.get('made_playoffs', '0'))
        won_cup = parse_bool(standings.get('won_cup', '0'))

        # Get playoff_rounds_won from playoff history CSV
        # This is the training target — how far the team went
        playoff_rounds_won = playoff.get('current_rounds_won', 0)

        # Sanity: if won_cup is True, rounds_won must be 4
        if won_cup:
            playoff_rounds_won = 4

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

            # Possession metrics
            cf_pct=cf_pct,
            ff_pct=ff_pct,
            sf_pct=(cf_pct + ff_pct) / 2,

            # Expected goals
            xgf=xgf,
            xga=xga,
            xgf_pct=xgf_pct,
            expected_goals_diff=xgf - xga,

            # High danger
            hdcf=int(advanced['hdcf']) if 'hdcf' in advanced else int(xgf * 0.4),
            hdca=int(advanced['hdca']) if 'hdca' in advanced else int(xga * 0.4),
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
            home_ot_losses=home_ot_losses,
            away_wins=away_wins,
            away_losses=away_losses,
            away_ot_losses=away_ot_losses,

            # Outcomes
            made_playoffs=made_playoffs,
            won_cup=won_cup,
            playoff_rounds_won=playoff_rounds_won,

            # These get populated from auxiliary loaders via feature_engineering
            recent_form=0.0,
            star_ppg=0.0,
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse team data for {standings.get('team', 'unknown')}: {e}")
        return None


def load_real_training_data() -> List[TeamSeason]:
    """
    Load real training data from available historical seasons.

    Returns training data from CSV files, falling back to synthetic
    data if needed.
    """
    real_data = load_real_historical_data(start_season=2010, end_season=2024)

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


