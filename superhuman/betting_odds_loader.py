"""
Betting Odds Loader - Load and analyze Vegas betting odds
==========================================================
Loads historical Vegas odds for benchmarking model performance
against the betting market.
"""

import csv
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sklearn.metrics import brier_score_loss, log_loss

from .config import normalize_team_abbrev as _normalize_team, HISTORICAL_DIR, parse_bool

logger = logging.getLogger(__name__)


@dataclass
class TeamOdds:
    """Vegas odds for a single team in a season."""
    team: str
    season: int
    cup_odds_american: int  # American odds format (+500, -200, etc.)
    cup_implied_prob: float  # Implied probability from odds
    playoff_odds_american: int
    playoff_implied_prob: float
    actual_made_playoffs: bool
    actual_won_cup: bool


def american_to_probability(odds: int) -> float:
    """
    Convert American odds to implied probability.

    American odds:
    - Positive (+150): underdog, probability = 100 / (odds + 100)
    - Negative (-150): favorite, probability = |odds| / (|odds| + 100)
    """
    if odds == 0:
        return 0.0
    elif odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def get_available_vegas_seasons(
    start_season: int = 2010,
    end_season: int = 2100,
) -> List[int]:
    """Return sorted seasons with normalized vegas odds files present."""
    seasons: List[int] = []
    for path in sorted(HISTORICAL_DIR.glob("vegas_odds_*.csv")):
        try:
            season = int(path.stem.split("_")[-1])
        except ValueError:
            continue
        if start_season <= season <= end_season:
            seasons.append(season)
    return seasons


def _first_non_empty(row: dict, keys: List[str], default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def _parse_american_odds(raw: str) -> int:
    normalized = raw.strip().replace("−", "-").replace("—", "-").replace("+", "")
    odds = int(normalized)
    return odds if odds < 0 else int(f"+{odds}")


def load_vegas_odds(season: int) -> Dict[str, TeamOdds]:
    """
    Load Vegas odds for a single season.

    Args:
        season: Season year (e.g., 2024)

    Returns:
        Dictionary mapping team abbreviation to TeamOdds
    """
    csv_path = HISTORICAL_DIR / f"vegas_odds_{season}.csv"

    if not csv_path.exists():
        logger.debug(f"Vegas odds file not found: {csv_path}")
        return {}

    teams = {}
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                team_raw = _first_non_empty(row, ["team", "team_abbrev", "team_code", "abbrev"])
                cup_odds = _parse_american_odds(_first_non_empty(row, ["cup_odds_american", "cup_odds", "cup"]))
                playoff_odds = _parse_american_odds(
                    _first_non_empty(row, ["playoff_odds_american", "playoff_odds", "playoffs_odds", "playoff"])
                )
                cup_prob_raw = _first_non_empty(row, ["cup_implied_prob", "cup_prob"])
                playoff_prob_raw = _first_non_empty(row, ["playoff_implied_prob", "playoff_prob"])
                made_playoffs_raw = _first_non_empty(row, ["actual_made_playoffs", "made_playoffs"])
                won_cup_raw = _first_non_empty(row, ["actual_won_cup", "won_cup"])
                season_raw = _first_non_empty(row, ["season"], str(season))

                odds = TeamOdds(
                    team=_normalize_team(team_raw),
                    season=int(season_raw),
                    cup_odds_american=cup_odds,
                    cup_implied_prob=float(cup_prob_raw),
                    playoff_odds_american=playoff_odds,
                    playoff_implied_prob=float(playoff_prob_raw),
                    actual_made_playoffs=parse_bool(made_playoffs_raw),
                    actual_won_cup=parse_bool(won_cup_raw),
                )
                teams[odds.team] = odds
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse odds for {row.get('team', 'unknown')}: {e}")
                continue

    logger.debug(f"Loaded Vegas odds for {len(teams)} teams in season {season}")
    return teams


def load_all_vegas_odds(
    start_season: int = 2010,
    end_season: int = 2024
) -> Dict[str, TeamOdds]:
    """
    Load Vegas odds for all seasons.

    Returns:
        Dictionary mapping "{team}_{season}" to TeamOdds
    """
    all_odds = {}

    seasons = get_available_vegas_seasons(start_season=start_season, end_season=end_season)
    for season in seasons:
        season_odds = load_vegas_odds(season)
        for team, odds in season_odds.items():
            key = f"{team}_{season}"
            all_odds[key] = odds

    if seasons:
        logger.info(f"Loaded Vegas odds for {len(all_odds)} team-seasons across {len(seasons)} seasons")
    else:
        logger.info("Loaded Vegas odds for 0 team-seasons (no vegas_odds_YYYY.csv files found)")
    return all_odds


def calculate_vegas_brier_score(
    odds_data: Dict[str, TeamOdds],
    target: str = 'playoff'
) -> Tuple[float, int]:
    """
    Calculate Brier score for Vegas predictions.

    Args:
        odds_data: Dictionary of TeamOdds
        target: 'playoff' or 'cup'

    Returns:
        Tuple of (brier_score, n_samples)
    """
    predictions = []
    actuals = []

    for odds in odds_data.values():
        if target == 'playoff':
            predictions.append(odds.playoff_implied_prob)
            actuals.append(1 if odds.actual_made_playoffs else 0)
        else:  # cup
            predictions.append(odds.cup_implied_prob)
            actuals.append(1 if odds.actual_won_cup else 0)

    if not predictions:
        return float('nan'), 0

    brier = brier_score_loss(actuals, predictions)
    return brier, len(predictions)


def calculate_vegas_accuracy(
    odds_data: Dict[str, TeamOdds],
    target: str = 'playoff'
) -> Tuple[float, int, int]:
    """
    Calculate accuracy of Vegas predictions.

    For playoffs: threshold at 0.5 implied probability
    For cup: check if team with highest odds won

    Returns:
        Tuple of (accuracy, correct, total)
    """
    if target == 'playoff':
        correct = 0
        total = len(odds_data)

        for odds in odds_data.values():
            predicted = odds.playoff_implied_prob >= 0.5
            actual = odds.actual_made_playoffs
            if predicted == actual:
                correct += 1

        return correct / total if total > 0 else 0.0, correct, total

    else:  # cup
        # Group by season and check if top pick won
        by_season = {}
        for odds in odds_data.values():
            if odds.season not in by_season:
                by_season[odds.season] = []
            by_season[odds.season].append(odds)

        correct = 0
        total = len(by_season)

        for season, teams in by_season.items():
            # Find Vegas favorite (highest cup probability)
            favorite = max(teams, key=lambda x: x.cup_implied_prob)
            if favorite.actual_won_cup:
                correct += 1

        return correct / total if total > 0 else 0.0, correct, total


def get_team_vegas_odds(team: str, season: int) -> Optional[TeamOdds]:
    """
    Get Vegas odds for a specific team and season.
    """
    season_odds = load_vegas_odds(season)
    return season_odds.get(team)


def benchmark_model_vs_vegas(
    model_predictions: List[Tuple[str, int, float, float]],  # (team, season, playoff_prob, cup_prob)
    odds_data: Dict[str, TeamOdds]
) -> Dict[str, float]:
    """
    Compare model predictions against Vegas odds.

    Args:
        model_predictions: List of (team, season, playoff_prob, cup_prob)
        odds_data: Dictionary of TeamOdds

    Returns:
        Dictionary with comparison metrics
    """
    model_playoff_preds = []
    vegas_playoff_preds = []
    playoff_actuals = []

    model_cup_preds = []
    vegas_cup_preds = []
    cup_actuals = []

    for team, season, playoff_prob, cup_prob in model_predictions:
        key = f"{team}_{season}"
        if key not in odds_data:
            continue

        odds = odds_data[key]

        model_playoff_preds.append(playoff_prob)
        vegas_playoff_preds.append(odds.playoff_implied_prob)
        playoff_actuals.append(1 if odds.actual_made_playoffs else 0)

        model_cup_preds.append(cup_prob)
        vegas_cup_preds.append(odds.cup_implied_prob)
        cup_actuals.append(1 if odds.actual_won_cup else 0)

    if not model_playoff_preds:
        return {'error': 'No matching predictions found'}

    # Calculate Brier scores
    model_brier_playoff = brier_score_loss(playoff_actuals, model_playoff_preds)
    vegas_brier_playoff = brier_score_loss(playoff_actuals, vegas_playoff_preds)

    model_brier_cup = brier_score_loss(cup_actuals, model_cup_preds)
    vegas_brier_cup = brier_score_loss(cup_actuals, vegas_cup_preds)

    # Calculate accuracy (threshold 0.5 for playoffs)
    model_correct = sum(1 for p, a in zip(model_playoff_preds, playoff_actuals)
                       if (p >= 0.5) == bool(a))
    vegas_correct = sum(1 for p, a in zip(vegas_playoff_preds, playoff_actuals)
                       if (p >= 0.5) == bool(a))

    n_samples = len(model_playoff_preds)

    return {
        'n_samples': n_samples,

        # Playoff comparison
        'model_brier_playoff': model_brier_playoff,
        'vegas_brier_playoff': vegas_brier_playoff,
        'brier_improvement_playoff': (vegas_brier_playoff - model_brier_playoff) / vegas_brier_playoff * 100 if vegas_brier_playoff > 0 else 0.0,

        'model_accuracy_playoff': model_correct / n_samples,
        'vegas_accuracy_playoff': vegas_correct / n_samples,

        # Cup comparison
        'model_brier_cup': model_brier_cup,
        'vegas_brier_cup': vegas_brier_cup,
        'brier_improvement_cup': (vegas_brier_cup - model_brier_cup) / vegas_brier_cup * 100 if vegas_brier_cup > 0 else 0.0,

        # Edge calculation
        'beats_vegas_playoff': model_brier_playoff < vegas_brier_playoff,
        'beats_vegas_cup': model_brier_cup < vegas_brier_cup,
    }


# Cache for loaded odds
_odds_cache: Optional[Dict[str, TeamOdds]] = None


def get_cached_odds() -> Dict[str, TeamOdds]:
    """Get cached odds data, loading if necessary."""
    global _odds_cache
    if _odds_cache is None:
        _odds_cache = load_all_vegas_odds()
    return _odds_cache


def clear_cache():
    """Clear the odds cache."""
    global _odds_cache
    _odds_cache = None
