"""
Player Data Loader - Load individual player statistics
=======================================================
Loads player-level data for calculating:
- star_power: Quality of top players (PPG of stars)
- roster_depth: Number of quality scorers (20+ goal scorers, etc.)
"""

import csv
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from .config import normalize_team_abbrev as _normalize_team, HISTORICAL_DIR, parse_bool

logger = logging.getLogger(__name__)


@dataclass
class PlayerStats:
    """Individual player statistics for a season."""
    team: str
    season: int
    player_name: str
    position: str
    games_played: int
    goals: int
    assists: int
    points: int
    ppg: float  # Points per game
    toi_per_game: float  # Time on ice per game
    is_star: bool  # Is this player considered a star?


@dataclass
class TeamPlayerStats:
    """Aggregated player statistics for a team."""
    team: str
    season: int

    # Star metrics
    num_stars: int  # Number of star players
    star_avg_ppg: float  # Average PPG of star players
    top_scorer_ppg: float  # PPG of top scorer
    top_3_avg_ppg: float  # Average PPG of top 3 scorers

    # Depth metrics
    players_20_goals: int  # Players with 20+ goals
    players_30_goals: int  # Players with 30+ goals
    players_50_points: int  # Players with 50+ points
    players_70_points: int  # Players with 70+ points

    # Positional balance
    top_forward_ppg: float
    top_defenseman_ppg: float

    # Total team scoring
    total_goals: int
    total_points: int
    avg_team_ppg: float  # Average PPG across all players


def load_player_data(season: int) -> List[PlayerStats]:
    """
    Load player data for a single season from CSV.

    Args:
        season: Season year (e.g., 2024)

    Returns:
        List of PlayerStats for all players in that season
    """
    csv_path = HISTORICAL_DIR / f"players_{season}.csv"

    if not csv_path.exists():
        logger.debug(f"Player data file not found: {csv_path}")
        return []

    players = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # Detect CSV format: old (2010-2014) uses 'player'/'games',
        # new (2015+) uses 'player_name'/'games_played'/'ppg' etc.
        is_old_format = 'player' in fieldnames and 'player_name' not in fieldnames

        for row in reader:
            try:
                # Get player name from whichever column exists
                name = row.get('player_name') or row.get('player', '')
                if name in ('N/A', '', 'Unknown'):
                    continue

                games = int(row.get('games_played') or row.get('games', 0))
                goals = int(row.get('goals', 0))
                assists = int(row.get('assists', 0))
                points = int(row.get('points', 0))

                # Old format lacks ppg/toi/position/is_star — derive what we can
                if is_old_format:
                    ppg = points / games if games > 0 else 0.0
                    toi = 0.0
                    position = 'F'
                    is_star = ppg >= 0.9 and games >= 50
                else:
                    ppg = float(row.get('ppg', 0.0))
                    toi = float(row.get('toi_per_game', 0.0))
                    position = row.get('position', 'F')
                    is_star = parse_bool(row.get('is_star', '0'))

                player = PlayerStats(
                    team=_normalize_team(row['team']),
                    season=int(row.get('season', season)),
                    player_name=name,
                    position=position,
                    games_played=games,
                    goals=goals,
                    assists=assists,
                    points=points,
                    ppg=ppg,
                    toi_per_game=toi,
                    is_star=is_star
                )
                players.append(player)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse player: {row.get('player_name', row.get('player', 'unknown'))} - {e}")
                continue

    logger.debug(f"Loaded {len(players)} players for season {season}")
    return players


def aggregate_team_player_stats(players: List[PlayerStats], team: str, season: int) -> Optional[TeamPlayerStats]:
    """
    Aggregate player stats for a single team.

    Args:
        players: List of all player stats for the season
        team: Team abbreviation
        season: Season year

    Returns:
        TeamPlayerStats with aggregated metrics, or None if no players
    """
    team_players = [p for p in players if p.team == team]

    if not team_players:
        return None

    # Sort by points for depth calculations
    sorted_by_points = sorted(team_players, key=lambda p: p.points, reverse=True)
    sorted_by_ppg = sorted(team_players, key=lambda p: p.ppg, reverse=True)

    # Star metrics
    stars = [p for p in team_players if p.is_star]
    num_stars = len(stars)
    star_avg_ppg = sum(p.ppg for p in stars) / len(stars) if stars else 0.0

    # Top scorer metrics
    top_scorer_ppg = sorted_by_ppg[0].ppg if sorted_by_ppg else 0.0
    top_3_ppg = [p.ppg for p in sorted_by_ppg[:3]]
    top_3_avg_ppg = sum(top_3_ppg) / len(top_3_ppg) if top_3_ppg else 0.0

    # Depth metrics
    players_20_goals = len([p for p in team_players if p.goals >= 20])
    players_30_goals = len([p for p in team_players if p.goals >= 30])
    players_50_points = len([p for p in team_players if p.points >= 50])
    players_70_points = len([p for p in team_players if p.points >= 70])

    # Positional balance
    forwards = [p for p in team_players if p.position in ('C', 'LW', 'RW', 'F')]
    defensemen = [p for p in team_players if p.position == 'D']

    top_forward_ppg = max((p.ppg for p in forwards), default=0.0)
    top_defenseman_ppg = max((p.ppg for p in defensemen), default=0.0)

    # Team totals
    total_goals = sum(p.goals for p in team_players)
    total_points = sum(p.points for p in team_players)
    total_games = sum(p.games_played for p in team_players)
    avg_team_ppg = total_points / total_games if total_games > 0 else 0.0

    return TeamPlayerStats(
        team=team,
        season=season,
        num_stars=num_stars,
        star_avg_ppg=star_avg_ppg,
        top_scorer_ppg=top_scorer_ppg,
        top_3_avg_ppg=top_3_avg_ppg,
        players_20_goals=players_20_goals,
        players_30_goals=players_30_goals,
        players_50_points=players_50_points,
        players_70_points=players_70_points,
        top_forward_ppg=top_forward_ppg,
        top_defenseman_ppg=top_defenseman_ppg,
        total_goals=total_goals,
        total_points=total_points,
        avg_team_ppg=avg_team_ppg
    )


def load_all_team_player_stats(
    start_season: int = 2010,
    end_season: int = 2024
) -> Dict[str, TeamPlayerStats]:
    """
    Load and aggregate player stats for all teams across seasons.

    Args:
        start_season: First season to load
        end_season: Last season to load

    Returns:
        Dictionary mapping (team, season) tuple string to TeamPlayerStats
    """
    all_stats = {}

    for season in range(start_season, end_season + 1):
        players = load_player_data(season)

        if not players:
            continue

        # Get unique teams for this season
        teams = set(p.team for p in players)

        for team in teams:
            team_stats = aggregate_team_player_stats(players, team, season)
            if team_stats:
                key = f"{team}_{season}"
                all_stats[key] = team_stats

    logger.info(f"Loaded player stats for {len(all_stats)} team-seasons")
    return all_stats


def calculate_star_power_from_players(team_stats: TeamPlayerStats) -> float:
    """
    Calculate star_power feature from player data.

    Factors:
    - Star player average PPG (weighted 50%)
    - Top scorer PPG (weighted 30%)
    - Top 3 average PPG (weighted 20%)

    Returns value normalized to roughly -1 to +1 range.
    """
    if team_stats is None:
        return 0.0

    # Base PPG for an average star is around 0.9-1.0
    baseline_ppg = 0.95

    # Calculate components
    star_component = (team_stats.star_avg_ppg - baseline_ppg) * 0.5 if team_stats.num_stars > 0 else 0.0
    top_scorer_component = (team_stats.top_scorer_ppg - baseline_ppg) * 0.3
    top_3_component = (team_stats.top_3_avg_ppg - (baseline_ppg * 0.8)) * 0.2

    # Combine and scale to roughly -1 to +1
    raw_score = star_component + top_scorer_component + top_3_component
    return raw_score * 3  # Scale factor


def calculate_roster_depth_from_players(team_stats: TeamPlayerStats) -> float:
    """
    Calculate roster_depth feature from player data.

    Factors:
    - Number of 20+ goal scorers (primary)
    - Number of 50+ point players (secondary)
    - Positional balance (bonus)

    Returns value normalized to roughly -1 to +1 range.
    """
    if team_stats is None:
        return 0.0

    # Average team has ~3 20-goal scorers, ~4 50-point players
    goals_component = (team_stats.players_20_goals - 3) * 0.4
    points_component = (team_stats.players_50_points - 4) * 0.3

    # Bonus for having productive defenseman
    defense_bonus = 0.2 if team_stats.top_defenseman_ppg > 0.7 else 0.0

    # 30-goal scorers are elite
    elite_bonus = team_stats.players_30_goals * 0.15

    return goals_component + points_component + defense_bonus + elite_bonus


# Cache for loaded player stats
_player_stats_cache: Optional[Dict[str, TeamPlayerStats]] = None


def get_team_player_stats(team: str, season: int) -> Optional[TeamPlayerStats]:
    """
    Get player stats for a specific team and season.

    Uses caching to avoid reloading files.
    """
    global _player_stats_cache

    if _player_stats_cache is None:
        _player_stats_cache = load_all_team_player_stats()

    key = f"{team}_{season}"
    return _player_stats_cache.get(key)


def clear_cache():
    """Clear the player stats cache."""
    global _player_stats_cache
    _player_stats_cache = None
