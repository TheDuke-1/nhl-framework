"""
NHL API Client - Real Data Infrastructure
==========================================
Fetches real NHL statistics from multiple sources with fallbacks.

Data Sources (in priority order):
1. NHL Official API (api-web.nhle.com)
2. Money Puck (CSV exports)
3. Natural Stat Trick (scraped)
4. Hockey-Reference (scraped)
5. Local CSV cache (offline mode)

Usage:
    client = NHLDataClient()
    standings = client.get_standings(season=2024)
    team_stats = client.get_team_stats(team='COL', season=2024)
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import csv

logger = logging.getLogger(__name__)

# Base paths
DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = DATA_DIR / "cache"
HISTORICAL_DIR = DATA_DIR / "historical"


@dataclass
class TeamStanding:
    """Single team's standings data."""
    team: str
    team_name: str
    season: int
    games_played: int
    wins: int
    losses: int
    ot_losses: int
    points: int
    points_pct: float
    goals_for: int
    goals_against: int
    goal_differential: int

    # Record splits
    home_wins: int = 0
    home_losses: int = 0
    home_ot_losses: int = 0
    away_wins: int = 0
    away_losses: int = 0
    away_ot_losses: int = 0

    # Streaks
    streak_code: str = ""  # e.g., "W3", "L2", "OT1"
    last_10_wins: int = 0
    last_10_losses: int = 0
    last_10_ot: int = 0

    # Playoff status
    playoff_spot: str = ""  # "x", "y", "z", "e", or ""
    wildcard_rank: int = 0
    division_rank: int = 0
    conference_rank: int = 0
    league_rank: int = 0


@dataclass
class TeamAdvancedStats:
    """Advanced analytics for a team."""
    team: str
    season: int
    situation: str = "all"  # "all", "5v5", "pp", "pk"

    # Corsi/Fenwick
    cf: int = 0  # Corsi For
    ca: int = 0  # Corsi Against
    cf_pct: float = 50.0
    ff: int = 0  # Fenwick For
    fa: int = 0  # Fenwick Against
    ff_pct: float = 50.0

    # Expected Goals
    xgf: float = 0.0
    xga: float = 0.0
    xgf_pct: float = 50.0

    # Actual Goals
    gf: int = 0
    ga: int = 0

    # High Danger
    hdcf: int = 0
    hdca: int = 0
    hdcf_pct: float = 50.0
    hdgf: int = 0
    hdga: int = 0

    # Shooting/Goaltending
    shots_for: int = 0
    shots_against: int = 0
    shooting_pct: float = 0.0
    save_pct: float = 0.0
    pdo: float = 100.0

    # GSAX (Goals Saved Above Expected)
    gsax: float = 0.0

    # Special Teams
    pp_pct: float = 0.0
    pk_pct: float = 0.0
    pp_opportunities: int = 0
    pk_opportunities: int = 0


class NHLDataClient:
    """
    Client for fetching NHL data from multiple sources.

    Implements fallback chain:
    1. Try NHL API
    2. Try Money Puck CSVs
    3. Fall back to local cache
    """

    NHL_API_BASE = "https://api-web.nhle.com/v1"
    MONEYPUCK_BASE = "https://moneypuck.com/moneypuck/playerData/seasonSummary"

    TEAM_ABBREVS = {
        'ANA': 'Anaheim Ducks', 'ARI': 'Arizona Coyotes', 'BOS': 'Boston Bruins',
        'BUF': 'Buffalo Sabres', 'CGY': 'Calgary Flames', 'CAR': 'Carolina Hurricanes',
        'CHI': 'Chicago Blackhawks', 'COL': 'Colorado Avalanche', 'CBJ': 'Columbus Blue Jackets',
        'DAL': 'Dallas Stars', 'DET': 'Detroit Red Wings', 'EDM': 'Edmonton Oilers',
        'FLA': 'Florida Panthers', 'LA': 'Los Angeles Kings', 'MIN': 'Minnesota Wild',
        'MTL': 'Montreal Canadiens', 'NSH': 'Nashville Predators', 'NJ': 'New Jersey Devils',
        'NYI': 'New York Islanders', 'NYR': 'New York Rangers', 'OTT': 'Ottawa Senators',
        'PHI': 'Philadelphia Flyers', 'PIT': 'Pittsburgh Penguins', 'SJ': 'San Jose Sharks',
        'SEA': 'Seattle Kraken', 'STL': 'St. Louis Blues', 'TB': 'Tampa Bay Lightning',
        'TOR': 'Toronto Maple Leafs', 'UTA': 'Utah Hockey Club', 'VAN': 'Vancouver Canucks',
        'VGK': 'Vegas Golden Knights', 'WSH': 'Washington Capitals', 'WPG': 'Winnipeg Jets',
    }

    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create data directories if they don't exist."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)

    def _fetch_url(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch URL with error handling."""
        try:
            req = Request(url, headers={'User-Agent': 'NHLPredictor/1.0'})
            with urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8')
        except (URLError, HTTPError) as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        return CACHE_DIR / f"{key}.json"

    def _load_cache(self, key: str) -> Optional[Any]:
        """Load data from cache."""
        if not self.cache_enabled:
            return None
        path = self._get_cache_path(key)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def _save_cache(self, key: str, data: Any):
        """Save data to cache."""
        if self.cache_enabled:
            path = self._get_cache_path(key)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    def get_standings(self, season: int = None) -> List[TeamStanding]:
        """
        Get current or historical standings.

        Args:
            season: NHL season year (e.g., 2024 for 2023-24 season)
                   If None, gets current season

        Returns:
            List of TeamStanding objects
        """
        if season is None:
            season = self._current_season()

        cache_key = f"standings_{season}"

        # Try cache first
        cached = self._load_cache(cache_key)
        if cached:
            return [TeamStanding(**t) for t in cached]

        # Try NHL API
        standings = self._fetch_standings_nhl_api(season)
        if standings:
            self._save_cache(cache_key, [asdict(s) for s in standings])
            return standings

        # Try local historical file
        standings = self._load_historical_standings(season)
        if standings:
            return standings

        logger.warning(f"Could not fetch standings for {season}")
        return []

    def _fetch_standings_nhl_api(self, season: int) -> Optional[List[TeamStanding]]:
        """Fetch standings from NHL API."""
        # NHL API uses date-based standings
        # For historical, use end of regular season
        if season < self._current_season():
            date_str = f"{season}-04-15"  # Approximate end of regular season
        else:
            date_str = "now"

        url = f"{self.NHL_API_BASE}/standings/{date_str}"
        data = self._fetch_url(url)

        if not data:
            return None

        try:
            parsed = json.loads(data)
            return self._parse_nhl_standings(parsed, season)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse NHL standings: {e}")
            return None

    def _parse_nhl_standings(self, data: dict, season: int) -> List[TeamStanding]:
        """Parse NHL API standings response."""
        standings = []

        for team_data in data.get('standings', []):
            try:
                team = TeamStanding(
                    team=team_data.get('teamAbbrev', {}).get('default', ''),
                    team_name=team_data.get('teamName', {}).get('default', ''),
                    season=season,
                    games_played=team_data.get('gamesPlayed', 0),
                    wins=team_data.get('wins', 0),
                    losses=team_data.get('losses', 0),
                    ot_losses=team_data.get('otLosses', 0),
                    points=team_data.get('points', 0),
                    points_pct=team_data.get('pointPctg', 0.0),
                    goals_for=team_data.get('goalFor', 0),
                    goals_against=team_data.get('goalAgainst', 0),
                    goal_differential=team_data.get('goalDifferential', 0),
                    home_wins=team_data.get('homeWins', 0),
                    home_losses=team_data.get('homeLosses', 0),
                    home_ot_losses=team_data.get('homeOtLosses', 0),
                    away_wins=team_data.get('roadWins', 0),
                    away_losses=team_data.get('roadLosses', 0),
                    away_ot_losses=team_data.get('roadOtLosses', 0),
                    streak_code=team_data.get('streakCode', ''),
                    last_10_wins=team_data.get('l10Wins', 0),
                    last_10_losses=team_data.get('l10Losses', 0),
                    last_10_ot=team_data.get('l10OtLosses', 0),
                    division_rank=team_data.get('divisionSequence', 0),
                    conference_rank=team_data.get('conferenceSequence', 0),
                    league_rank=team_data.get('leagueSequence', 0),
                )
                standings.append(team)
            except Exception as e:
                logger.warning(f"Failed to parse team data: {e}")
                continue

        return standings

    def _load_historical_standings(self, season: int) -> Optional[List[TeamStanding]]:
        """Load standings from local historical CSV."""
        csv_path = HISTORICAL_DIR / f"standings_{season}.csv"

        if not csv_path.exists():
            return None

        standings = []
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    standings.append(TeamStanding(
                        team=row['team'],
                        team_name=row.get('team_name', self.TEAM_ABBREVS.get(row['team'], '')),
                        season=int(row.get('season', season)),
                        games_played=int(row.get('games_played', 82)),
                        wins=int(row['wins']),
                        losses=int(row['losses']),
                        ot_losses=int(row.get('ot_losses', 0)),
                        points=int(row['points']),
                        points_pct=float(row.get('points_pct', int(row['points']) / 164)),
                        goals_for=int(row['goals_for']),
                        goals_against=int(row['goals_against']),
                        goal_differential=int(row.get('goal_differential',
                            int(row['goals_for']) - int(row['goals_against']))),
                        home_wins=int(row.get('home_wins', 0)),
                        home_losses=int(row.get('home_losses', 0)),
                        home_ot_losses=int(row.get('home_ot_losses', 0)),
                        away_wins=int(row.get('away_wins', 0)),
                        away_losses=int(row.get('away_losses', 0)),
                        away_ot_losses=int(row.get('away_ot_losses', 0)),
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse row: {e}")
                    continue

        return standings if standings else None

    def get_advanced_stats(self, season: int = None, situation: str = "all") -> List[TeamAdvancedStats]:
        """
        Get advanced analytics for all teams.

        Args:
            season: NHL season year
            situation: "all", "5v5", "pp", "pk"

        Returns:
            List of TeamAdvancedStats objects
        """
        if season is None:
            season = self._current_season()

        cache_key = f"advanced_{season}_{situation}"

        # Try cache
        cached = self._load_cache(cache_key)
        if cached:
            return [TeamAdvancedStats(**t) for t in cached]

        # Try Money Puck
        stats = self._fetch_moneypuck_stats(season, situation)
        if stats:
            self._save_cache(cache_key, [asdict(s) for s in stats])
            return stats

        # Try local file
        stats = self._load_historical_advanced(season, situation)
        if stats:
            return stats

        logger.warning(f"Could not fetch advanced stats for {season}")
        return []

    def _fetch_moneypuck_stats(self, season: int, situation: str) -> Optional[List[TeamAdvancedStats]]:
        """Fetch advanced stats from Money Puck."""
        url = f"{self.MONEYPUCK_BASE}/{season}/regular/teams.csv"
        data = self._fetch_url(url)

        if not data:
            return None

        try:
            return self._parse_moneypuck_csv(data, season, situation)
        except Exception as e:
            logger.warning(f"Failed to parse Money Puck data: {e}")
            return None

    def _parse_moneypuck_csv(self, csv_data: str, season: int, situation: str) -> List[TeamAdvancedStats]:
        """Parse Money Puck CSV data."""
        import io
        stats = []

        reader = csv.DictReader(io.StringIO(csv_data))
        for row in reader:
            if situation != "all" and row.get('situation', 'all') != situation:
                continue

            try:
                stats.append(TeamAdvancedStats(
                    team=row.get('team', ''),
                    season=season,
                    situation=row.get('situation', 'all'),
                    cf=int(float(row.get('corsiFor', 0))),
                    ca=int(float(row.get('corsiAgainst', 0))),
                    cf_pct=float(row.get('corsiForPctg', 50)),
                    ff=int(float(row.get('fenwickFor', 0))),
                    fa=int(float(row.get('fenwickAgainst', 0))),
                    ff_pct=float(row.get('fenwickForPctg', 50)),
                    xgf=float(row.get('xGoalsFor', 0)),
                    xga=float(row.get('xGoalsAgainst', 0)),
                    xgf_pct=float(row.get('xGoalsForPctg', 50)),
                    gf=int(float(row.get('goalsFor', 0))),
                    ga=int(float(row.get('goalsAgainst', 0))),
                    shots_for=int(float(row.get('shotsOnGoalFor', 0))),
                    shots_against=int(float(row.get('shotsOnGoalAgainst', 0))),
                    shooting_pct=float(row.get('shootingPctg', 0)) * 100,
                    save_pct=float(row.get('savePctg', 0)),
                    pdo=float(row.get('pdo', 100)),
                ))
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse Money Puck row: {e}")
                continue

        return stats

    def _load_historical_advanced(self, season: int, situation: str) -> Optional[List[TeamAdvancedStats]]:
        """Load advanced stats from local CSV."""
        csv_path = HISTORICAL_DIR / f"advanced_{season}.csv"

        if not csv_path.exists():
            return None

        stats = []
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if situation != "all" and row.get('situation', 'all') != situation:
                    continue
                try:
                    stats.append(TeamAdvancedStats(
                        team=row['team'],
                        season=season,
                        situation=row.get('situation', 'all'),
                        cf_pct=float(row.get('cf_pct', 50)),
                        ff_pct=float(row.get('ff_pct', 50)),
                        xgf=float(row.get('xgf', 0)),
                        xga=float(row.get('xga', 0)),
                        xgf_pct=float(row.get('xgf_pct', 50)),
                        hdcf_pct=float(row.get('hdcf_pct', 50)),
                        shooting_pct=float(row.get('shooting_pct', 10)),
                        save_pct=float(row.get('save_pct', 0.91)),
                        pdo=float(row.get('pdo', 100)),
                        gsax=float(row.get('gsax', 0)),
                        pp_pct=float(row.get('pp_pct', 20)),
                        pk_pct=float(row.get('pk_pct', 80)),
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse advanced row: {e}")
                    continue

        return stats if stats else None

    def get_playoff_results(self, season: int) -> Dict[str, Any]:
        """Get playoff results for a completed season."""
        cache_key = f"playoffs_{season}"

        cached = self._load_cache(cache_key)
        if cached:
            return cached

        # Try local file
        csv_path = HISTORICAL_DIR / f"playoffs_{season}.csv"
        if csv_path.exists():
            results = {'season': season, 'rounds': [], 'champion': None}
            with open(csv_path, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results['rounds'].append(row)
                    if row.get('round') == 'Final' and int(row.get('winner_wins', 0)) == 4:
                        results['champion'] = row.get('winner')
            return results

        return {'season': season, 'rounds': [], 'champion': None}

    def _current_season(self) -> int:
        """Get current NHL season year."""
        today = date.today()
        # NHL season runs Oct-Jun, so if before October, use previous year
        if today.month < 10:
            return today.year
        return today.year + 1


def download_historical_data(start_season: int = 2010, end_season: int = 2025):
    """
    Download and cache historical data for multiple seasons.

    Run this once to populate the historical data directory.
    """
    client = NHLDataClient(cache_enabled=True)

    for season in range(start_season, end_season + 1):
        print(f"Fetching season {season}...")

        # Get standings
        standings = client.get_standings(season)
        if standings:
            print(f"  Standings: {len(standings)} teams")

        # Get advanced stats
        advanced = client.get_advanced_stats(season)
        if advanced:
            print(f"  Advanced stats: {len(advanced)} records")

        # Get playoff results (for completed seasons)
        if season < client._current_season():
            playoffs = client.get_playoff_results(season)
            if playoffs.get('champion'):
                print(f"  Champion: {playoffs['champion']}")

    print("Done!")


if __name__ == "__main__":
    # Test the client
    client = NHLDataClient()
    print("Testing NHL Data Client...")

    standings = client.get_standings(2024)
    print(f"Standings: {len(standings)} teams")

    if standings:
        print(f"Sample: {standings[0]}")
