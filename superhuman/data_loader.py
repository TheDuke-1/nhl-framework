"""
Superhuman NHL Prediction System - Data Loader
===============================================
Load and validate historical and current season data.

REVIEW FIXES APPLIED (Phase 1 Review):
- Synthetic data now generates independent stats (not derived from outcome)
- Added noise to prevent perfect prediction
- Separated synthetic generation into explicit function
- Added logging
- Fixed road stats generation
- Removed outcome->stat causation (was creating perfect correlation)
"""

import json
import logging
from pathlib import Path
from typing import List, Dict
import numpy as np

from .config import (
    DATA_DIR, HISTORICAL_DIR, ALL_TEAMS, TRAINING_SEASONS,
    TEST_SEASONS, RANDOM_SEED
)
from .data_models import TeamSeason

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
np.random.seed(RANDOM_SEED)

# Historical Stanley Cup winners (ground truth)
CUP_WINNERS = {
    2010: "CHI", 2011: "BOS", 2012: "LA", 2013: "CHI", 2014: "LA",
    2015: "CHI", 2016: "PIT", 2017: "PIT", 2018: "WSH", 2019: "STL",
    2020: "TB", 2021: "TB", 2022: "COL", 2023: "VGK", 2024: "FLA",
    2025: "FLA"
}

# Historical Cup finalists (runner-up)
CUP_FINALISTS = {
    2010: "PHI", 2011: "VAN", 2012: "NJ", 2013: "BOS", 2014: "NYR",
    2015: "TB", 2016: "SJ", 2017: "NSH", 2018: "VGK", 2019: "BOS",
    2020: "DAL", 2021: "MTL", 2022: "TB", 2023: "FLA", 2024: "EDM",
    2025: "EDM"
}

# Realistic stat distributions (from NHL historical averages)
STAT_DISTRIBUTIONS = {
    "goals_for": {"mean": 250, "std": 25},
    "goals_against": {"mean": 250, "std": 25},
    "cf_pct": {"mean": 50.0, "std": 3.5},
    "xgf_pct": {"mean": 50.0, "std": 3.5},
    "hdcf_pct": {"mean": 50.0, "std": 4.0},
    "gsax": {"mean": 0.0, "std": 10.0},
    "pp_pct": {"mean": 20.0, "std": 3.0},
    "pk_pct": {"mean": 80.0, "std": 3.0},
    "pdo": {"mean": 100.0, "std": 1.5},
    "top_scorer_ppg": {"mean": 0.9, "std": 0.15},
}


def load_current_season_data() -> List[TeamSeason]:
    """Load current season data from teams.json."""
    teams_file = DATA_DIR / "teams.json"

    if not teams_file.exists():
        raise FileNotFoundError(f"Teams file not found: {teams_file}")

    logger.info(f"Loading current season data from {teams_file}")

    with open(teams_file) as f:
        data = json.load(f)

    team_seasons = []
    for t in data.get("teams", []):
        # Normalize PDO (handle both 1.0x and 100.0 scales)
        pdo_raw = t.get("pdo", 100.0)
        pdo = pdo_raw * 100 if pdo_raw < 2 else pdo_raw

        ts = TeamSeason(
            team=t.get("team", ""),
            season=2026,
            games_played=t.get("gp", 0),
            wins=t.get("w", 0),
            losses=t.get("l", 0),
            ot_losses=t.get("otl", 0),
            points=t.get("pts", 0),
            goals_for=t.get("gf", 0),
            goals_against=t.get("ga", 0),
            cf_pct=t.get("cfPct", 50.0),
            xgf=t.get("xgf", 0.0),
            xga=t.get("xga", 0.0),
            xgf_pct=t.get("xgfPct", 50.0),
            hdcf_pct=t.get("hdcfPct", 50.0),
            gsax=t.get("gsax", 0.0),
            pp_pct=t.get("ppPct", 20.0),
            pk_pct=t.get("pkPct", 80.0),
            pdo=pdo,
            top_scorer_ppg=t.get("starPPG", 0.0),
            players_20_goals=t.get("depth20g", 0),
        )
        team_seasons.append(ts)

    logger.info(f"Loaded {len(team_seasons)} teams")
    return team_seasons


def load_training_data() -> List[TeamSeason]:
    """
    Load training data - tries real data first, falls back to synthetic.

    This is the recommended function to use for training.
    """
    try:
        from .real_data_loader import load_real_historical_data
        real_data = load_real_historical_data(start_season=2010, end_season=2024)
        if len(real_data) >= 32:  # At least one season
            logger.info(f"Using {len(real_data)} real historical team-seasons")
            return real_data
    except Exception as e:
        logger.warning(f"Could not load real data: {e}")

    logger.info("Falling back to synthetic training data")
    return synthesize_training_data()


def load_historical_data() -> List[TeamSeason]:
    """Load historical data from files or synthesize from known results."""
    # Try real data first
    return load_training_data()


def _load_from_file(filepath: Path) -> List[TeamSeason]:
    """Load historical data from JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    return [TeamSeason(**record) for record in data]


def synthesize_training_data() -> List[TeamSeason]:
    """
    Create synthetic historical data for model training.

    CRITICAL: Stats are generated INDEPENDENTLY of outcomes.
    This prevents the model from finding artificial perfect correlations.

    Playoff outcomes are assigned based on relative strength rankings
    (calculated from independent stats), with noise to allow upsets.
    """
    logger.info("Synthesizing training data with INDEPENDENT stat generation")
    team_seasons = []

    for season in TRAINING_SEASONS + TEST_SEASONS:
        season_teams = []

        # Step 1: Generate INDEPENDENT stats for each team
        for team in ALL_TEAMS:
            ts = _generate_independent_team_stats(team, season)
            season_teams.append(ts)

        # Step 2: Assign playoff outcomes based on relative strength
        season_teams = _assign_playoff_outcomes(season_teams, season)
        team_seasons.extend(season_teams)

    logger.info(f"Synthesized {len(team_seasons)} team-seasons")
    return team_seasons


def _generate_independent_team_stats(team: str, season: int) -> TeamSeason:
    """
    Generate team stats from INDEPENDENT random distributions.

    Each stat is drawn from its own distribution - NO stat depends on another.
    This is critical to prevent artificial multicollinearity.
    """
    # Core goal stats - INDEPENDENT draws
    gf = int(np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["goals_for"]["mean"],
                        STAT_DISTRIBUTIONS["goals_for"]["std"]),
        180, 320
    ))
    ga = int(np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["goals_against"]["mean"],
                        STAT_DISTRIBUTIONS["goals_against"]["std"]),
        180, 320
    ))

    # Possession stats - INDEPENDENT (NOT derived from goals)
    cf_pct = np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["cf_pct"]["mean"],
                        STAT_DISTRIBUTIONS["cf_pct"]["std"]),
        42, 58
    )
    xgf_pct = np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["xgf_pct"]["mean"],
                        STAT_DISTRIBUTIONS["xgf_pct"]["std"]),
        42, 58
    )
    hdcf_pct = np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["hdcf_pct"]["mean"],
                        STAT_DISTRIBUTIONS["hdcf_pct"]["std"]),
        38, 62
    )

    # Goaltending - INDEPENDENT
    gsax = np.random.normal(
        STAT_DISTRIBUTIONS["gsax"]["mean"],
        STAT_DISTRIBUTIONS["gsax"]["std"]
    )

    # Special teams - INDEPENDENT of each other
    pp_pct = np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["pp_pct"]["mean"],
                        STAT_DISTRIBUTIONS["pp_pct"]["std"]),
        14, 28
    )
    pk_pct = np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["pk_pct"]["mean"],
                        STAT_DISTRIBUTIONS["pk_pct"]["std"]),
        72, 88
    )

    # PDO (luck indicator) - INDEPENDENT
    pdo = np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["pdo"]["mean"],
                        STAT_DISTRIBUTIONS["pdo"]["std"]),
        97, 103
    )

    # Roster stats - INDEPENDENT
    top_scorer_ppg = np.clip(
        np.random.normal(STAT_DISTRIBUTIONS["top_scorer_ppg"]["mean"],
                        STAT_DISTRIBUTIONS["top_scorer_ppg"]["std"]),
        0.6, 1.4
    )
    players_20g = np.random.choice([1, 2, 3, 4, 5], p=[0.1, 0.25, 0.35, 0.2, 0.1])

    # Derived stats (these CAN be derived as they're definitional)
    gd = gf - ga
    # Points has noise - not perfectly determined by GD
    pts = 82 + int(gd * 0.7) + np.random.randint(-8, 9)
    pts = np.clip(pts, 50, 130)
    wins = int(pts / 2.4) + np.random.randint(-3, 4)
    wins = np.clip(wins, 20, 60)
    losses = np.random.randint(15, 35)
    ot_losses = 82 - wins - losses
    ot_losses = max(0, min(20, ot_losses))
    losses = 82 - wins - ot_losses

    # Road stats - INDEPENDENT proportion with variance
    road_games = 41
    road_win_rate = np.random.uniform(0.35, 0.65)
    road_wins = int(road_games * road_win_rate)
    road_losses = int(road_games * (1 - road_win_rate) * 0.7)
    road_ot_losses = road_games - road_wins - road_losses
    road_gf = int(gf * 0.48 * np.random.uniform(0.9, 1.1))
    road_ga = int(ga * 0.52 * np.random.uniform(0.9, 1.1))

    return TeamSeason(
        team=team,
        season=season,
        games_played=82,
        wins=wins,
        losses=losses,
        ot_losses=ot_losses,
        points=pts,
        goals_for=gf,
        goals_against=ga,
        cf_pct=cf_pct,
        xgf_pct=xgf_pct,
        hdcf_pct=hdcf_pct,
        gsax=gsax,
        pp_pct=pp_pct,
        pk_pct=pk_pct,
        pdo=pdo,
        away_wins=road_wins,
        away_losses=road_losses,
        away_ot_losses=road_ot_losses,
        top_scorer_ppg=top_scorer_ppg,
        players_20_goals=players_20g,
        made_playoffs=False,  # Assigned in next step
        playoff_rounds_won=0,
        won_cup=False,
    )


def _assign_playoff_outcomes(
    teams: List[TeamSeason],
    season: int
) -> List[TeamSeason]:
    """
    Assign playoff outcomes based on synthetic strength rankings.

    Uses known Cup winners as ground truth, but playoff berths are
    determined by the independently-generated stats.
    """
    cup_winner = CUP_WINNERS.get(season)
    cup_finalist = CUP_FINALISTS.get(season)

    def calculate_strength(ts: TeamSeason) -> float:
        """Simple strength composite from independent stats."""
        return (
            ts.goal_differential * 0.3 +
            (ts.hdcf_pct - 50) * 3 +
            ts.gsax * 0.5 +
            (ts.pk_pct - 80) * 2 +
            (ts.pp_pct - 20) * 1.5 +
            np.random.normal(0, 8)  # Substantial noise for realism
        )

    # Score and rank all teams
    team_scores = [(ts, calculate_strength(ts)) for ts in teams]
    team_scores.sort(key=lambda x: -x[1])

    # Top 16 make playoffs (with noise in cutoff)
    playoff_cutoff = 16 + np.random.randint(-2, 3)
    playoff_teams = set(ts.team for ts, _ in team_scores[:playoff_cutoff])

    # Force known Cup winner/finalist into playoffs (ground truth override)
    if cup_winner:
        playoff_teams.add(cup_winner)
    if cup_finalist:
        playoff_teams.add(cup_finalist)

    # Assign outcomes
    for ts in teams:
        if ts.team == cup_winner:
            ts.made_playoffs = True
            ts.playoff_rounds_won = 4
            ts.won_cup = True
        elif ts.team == cup_finalist:
            ts.made_playoffs = True
            ts.playoff_rounds_won = 3
        elif ts.team in playoff_teams:
            ts.made_playoffs = True
            ts.playoff_rounds_won = np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2])
        else:
            ts.made_playoffs = False
            ts.playoff_rounds_won = 0

    return teams


def validate_data(team_seasons: List[TeamSeason]) -> Dict:
    """Validate data quality and return diagnostic report."""
    issues = []
    warnings = []

    for ts in team_seasons:
        if ts.games_played == 0:
            issues.append(f"{ts.team} {ts.season}: No games played")
        if ts.goals_for == 0 and ts.goals_against == 0:
            warnings.append(f"{ts.team} {ts.season}: No goal data")
        if not (35 <= ts.hdcf_pct <= 65):
            warnings.append(f"{ts.team} {ts.season}: HDCF% out of range: {ts.hdcf_pct:.1f}")
        if not (95 <= ts.pdo <= 105):
            warnings.append(f"{ts.team} {ts.season}: PDO out of range: {ts.pdo:.1f}")

    cup_winners = [ts for ts in team_seasons if ts.won_cup]
    if len(cup_winners) != len(set(ts.season for ts in cup_winners)):
        issues.append("Multiple Cup winners in same season")

    return {
        "total_records": len(team_seasons),
        "seasons": len(set(ts.season for ts in team_seasons)),
        "teams": len(set(ts.team for ts in team_seasons)),
        "issues": issues,
        "warnings": warnings[:10],
        "is_valid": len(issues) == 0
    }


def get_training_data() -> List[TeamSeason]:
    """Get team seasons for training (historical)."""
    all_data = load_historical_data()
    return [ts for ts in all_data if ts.season in TRAINING_SEASONS]


def get_test_data() -> List[TeamSeason]:
    """Get team seasons for testing (recent + current)."""
    historical = load_historical_data()
    current = load_current_season_data()
    test = [ts for ts in historical if ts.season in TEST_SEASONS]
    test.extend(current)
    return test


def get_all_data() -> List[TeamSeason]:
    """Get all available team seasons."""
    return load_historical_data() + load_current_season_data()
