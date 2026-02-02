"""
Real Data Loader - Load verified historical NHL data from JSON files
====================================================================
Reads from data/historical/verified/season_YYYY.json files produced
by scripts/fetch_historical.py. Each file contains standings, advanced
stats (NST), special teams (PP%/PK%), and playoff results.
"""

import json
import logging
from typing import List, Optional

from .data_models import TeamSeason
from .config import HISTORICAL_DIR, normalize_team_abbrev as _normalize_team

logger = logging.getLogger(__name__)


def load_real_historical_data(
    start_season: int = 2010,
    end_season: int = 2025
) -> List[TeamSeason]:
    """
    Load real historical NHL data from verified JSON files.

    Args:
        start_season: First season to load (e.g., 2010 for 2009-10)
        end_season: Last season to load (e.g., 2025 for 2024-25)

    Returns:
        List of TeamSeason objects with real NHL data
    """
    all_teams = []

    for season in range(start_season, end_season + 1):
        season_teams = _load_verified_json(season)
        if season_teams:
            all_teams.extend(season_teams)
            logger.info(f"Loaded {len(season_teams)} teams for season {season}")
        else:
            logger.warning(f"No verified data available for season {season}")

    logger.info(f"Total loaded: {len(all_teams)} team-seasons")
    return all_teams


def _load_verified_json(season: int) -> List[TeamSeason]:
    """Load and parse a single verified season JSON file into TeamSeason objects."""
    json_path = HISTORICAL_DIR / f"season_{season}.json"

    if not json_path.exists():
        logger.debug(f"Verified file not found: {json_path}")
        return []

    with open(json_path) as f:
        data = json.load(f)

    teams_data = data.get("teams", {})
    if not teams_data:
        logger.warning(f"No teams in {json_path}")
        return []

    teams = []
    for abbrev, t in teams_data.items():
        team = _json_to_team_season(abbrev, t, season)
        if team:
            teams.append(team)

    return teams


def _json_to_team_season(abbrev: str, t: dict, season: int) -> Optional[TeamSeason]:
    """Convert a single team's JSON record into a TeamSeason object."""
    try:
        team_abbr = _normalize_team(abbrev)

        gp = t.get("gp", 0)
        wins = t.get("w", 0)
        losses = t.get("l", 0)
        ot_losses = t.get("otl", 0)
        points = t.get("pts", 0)
        goals_for = t.get("gf", 0)
        goals_against = t.get("ga", 0)

        # Home/away splits
        home_wins = t.get("homeW", 0)
        home_losses = t.get("homeL", 0)
        home_ot_losses = t.get("homeOTL", 0)
        road_wins = t.get("roadW", 0)
        road_losses = t.get("roadL", 0)
        road_ot_losses = t.get("roadOTL", 0)

        # Special teams — stored as percentages (e.g., 22.4 for 22.4%)
        # Default to league average if missing so the model doesn't see 0
        pp_pct = t.get("ppPct") or 0
        pk_pct = t.get("pkPct") or 0
        if pp_pct == 0:
            logger.warning(f"{abbrev} {season}: PP% missing, imputing league avg 20.0")
            pp_pct = 20.0
        if pk_pct == 0:
            logger.warning(f"{abbrev} {season}: PK% missing, imputing league avg 80.0")
            pk_pct = 80.0

        # Advanced stats from NST (5v5) — default to 50.0 (league average)
        cf_pct = t.get("cfPct") or 50.0
        hdcf_pct = t.get("hdcfPct") or 50.0

        # NST PDO comes as decimal (0.95-1.05 range) or 100-scale (95-105).
        # TeamSeason expects PDO on 100-scale (95-105 range).
        pdo_raw = t.get("pdo") or 1.0
        if pdo_raw < 2.0:
            # Decimal format (e.g., 1.005) — convert to 100-scale
            pdo = pdo_raw * 100
        elif 80 <= pdo_raw <= 120:
            # Already on 100-scale (e.g., 100.5)
            pdo = pdo_raw
        else:
            logger.warning(f"{abbrev} {season}: PDO value {pdo_raw} outside expected range, defaulting to 100.0")
            pdo = 100.0

        # NST SH% is already a percentage (e.g., 8.41)
        shooting_pct = t.get("shPct") or 10.0

        # NST SV% comes as percentage-like (e.g., 91.45 for 91.45%) or
        # decimal (e.g., 0.9145). TeamSeason expects decimal (e.g., 0.9145).
        sv_raw = t.get("svPct") or 91.0
        if sv_raw > 1.0:
            # Percentage format (e.g., 91.45) — convert to decimal
            save_pct = sv_raw / 100.0
        elif 0.8 <= sv_raw <= 1.0:
            # Already decimal (e.g., 0.9145)
            save_pct = sv_raw
        else:
            logger.warning(f"{abbrev} {season}: SV% value {sv_raw} outside expected range, defaulting to 0.910")
            save_pct = 0.910

        # Raw Corsi/HD counts (for feature engineering)
        hdcf = t.get("hdcf") or 0
        hdca = t.get("hdca") or 0

        # xG/GSAx not available from NST team table or standings API.
        # Model's feature_engineering handles 0 defaults for these.
        # TODO: integrate MoneyPuck xG data for historical seasons
        if t.get("hasAdvanced") and not t.get("xgf"):
            logger.warning(f"{abbrev} {season}: xG/GSAx unavailable, defaulting to 0.0")
        xgf = 0.0
        xga = 0.0
        gsax = 0.0

        # Playoff outcomes
        made_playoffs = t.get("madePlayoffs", False)
        won_cup = t.get("wonCup", False)
        playoff_rounds_won = t.get("playoffRoundsWon", 0)

        # Sanity: Cup winner must have 4 rounds
        if won_cup:
            playoff_rounds_won = 4

        return TeamSeason(
            team=team_abbr,
            season=season,
            games_played=gp,
            wins=wins,
            losses=losses,
            ot_losses=ot_losses,
            points=points,
            goals_for=goals_for,
            goals_against=goals_against,

            cf_pct=cf_pct,
            ff_pct=cf_pct,  # Approximation: FF% not in NST team table, using CF% (correlated but excludes blocked shots)
            sf_pct=cf_pct,  # Approximation: SF% not in NST team table, using CF%

            xgf=xgf,
            xga=xga,
            xgf_pct=50.0,
            expected_goals_diff=0.0,

            hdcf=hdcf,
            hdca=hdca,
            hdcf_pct=hdcf_pct,

            save_pct=save_pct,
            gsax=gsax,

            shooting_pct=shooting_pct,
            pdo=pdo,

            pp_pct=pp_pct,
            pk_pct=pk_pct,

            home_wins=home_wins,
            home_losses=home_losses,
            home_ot_losses=home_ot_losses,
            away_wins=road_wins,
            away_losses=road_losses,
            away_ot_losses=road_ot_losses,

            made_playoffs=made_playoffs,
            won_cup=won_cup,
            playoff_rounds_won=playoff_rounds_won,

            recent_form=0.0,
            star_ppg=0.0,
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse team data for {abbrev}: {e}")
        return None


def load_real_training_data() -> List[TeamSeason]:
    """
    Load real training data from verified historical JSON files.
    Falls back to synthetic data if insufficient real data is found.
    """
    real_data = load_real_historical_data(start_season=2010, end_season=2024)

    if len(real_data) >= 100:
        logger.info(f"Using {len(real_data)} real historical team-seasons for training")
        return real_data

    logger.warning("Insufficient real data, falling back to synthetic generation")
    from .data_loader import synthesize_training_data
    return synthesize_training_data()


def get_available_seasons() -> List[int]:
    """Get list of seasons with available verified data."""
    available = []
    for path in sorted(HISTORICAL_DIR.glob("season_*.json")):
        try:
            year = int(path.stem.split("_")[1])
            available.append(year)
        except (ValueError, IndexError):
            continue
    return available
