"""
Superhuman NHL Prediction System - Validation Framework
========================================================
Cross-validation, calibration, and backtesting tools.
"""

import json
import numpy as np
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, replace
from collections import defaultdict

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import brier_score_loss, log_loss, precision_score, recall_score, f1_score
from sklearn.calibration import calibration_curve

from .data_models import TeamSeason, PredictionResult
from .models import EnsemblePredictor
from .config import (
    TRAINING_SEASONS,
    TEST_SEASONS,
    RANDOM_SEED,
    HISTORICAL_DIR,
    select_conference_playoff_teams,
)

logger = logging.getLogger(__name__)


def _compute_file_signature(paths: List[Path]) -> str:
    """Compute a short fingerprint from file bytes for cache invalidation."""
    h = hashlib.sha256()
    for path in paths:
        try:
            h.update(path.read_bytes())
        except Exception:
            continue
    return h.hexdigest()[:10]


def _compute_historical_data_signature() -> str:
    """Fingerprint historical input dataset shape/timestamps for cache invalidation."""
    h = hashlib.sha256()
    candidates = sorted(HISTORICAL_DIR.glob("season_*.json"))
    advanced_dir = HISTORICAL_DIR / "advanced"
    if advanced_dir.exists():
        candidates.extend(sorted(advanced_dir.glob("season_*.json")))
        candidates.extend(sorted(advanced_dir.glob("season_*.csv")))

    for p in candidates:
        try:
            stat = p.stat()
            h.update(str(p.relative_to(HISTORICAL_DIR.parent)).encode("utf-8"))
            h.update(str(stat.st_size).encode("utf-8"))
            h.update(str(stat.st_mtime_ns).encode("utf-8"))
        except Exception:
            continue
    return h.hexdigest()[:10]


@dataclass
class ValidationResult:
    """Results from validation run."""
    brier_score_playoff: float
    brier_score_cup: float
    log_loss_playoff: float
    calibration_error: float
    accuracy_playoff: float
    n_samples: int
    n_correct_cup_picks: int
    n_cup_events: int

    def to_dict(self) -> Dict:
        return {
            'brier_score_playoff': round(self.brier_score_playoff, 4),
            'brier_score_cup': round(self.brier_score_cup, 4),
            'log_loss_playoff': round(self.log_loss_playoff, 4),
            'calibration_error': round(self.calibration_error, 4),
            'accuracy_playoff': round(self.accuracy_playoff, 4),
            'n_samples': self.n_samples,
            'n_correct_cup_picks': self.n_correct_cup_picks,
            'n_cup_events': self.n_cup_events,
        }


@dataclass
class CalibrationBin:
    """Single bin in calibration analysis."""
    predicted_prob: float
    actual_rate: float
    n_samples: int


class ValidationFramework:
    """
    Cross-validation and calibration framework.

    Implements:
    - Time-series cross-validation (train on past, test on future)
    - Brier score for probability accuracy
    - Calibration curve analysis
    - Backtest on historical seasons
    """

    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits
        self.results: List[ValidationResult] = []

    def cross_validate(
        self,
        all_data: List[TeamSeason],
        model_factory=None
    ) -> ValidationResult:
        """
        Perform time-series cross-validation.

        Uses seasons chronologically - always train on earlier
        seasons and test on later seasons.
        """
        np.random.seed(RANDOM_SEED)
        # Group by season
        by_season: Dict[int, List[TeamSeason]] = defaultdict(list)
        for team in all_data:
            by_season[team.season].append(team)

        seasons = sorted(by_season.keys())
        if len(seasons) < 3:
            logger.warning("Not enough seasons for cross-validation")
            return self._empty_result()

        # Time-series splits
        all_predictions = []
        all_actuals_playoff = []
        all_actuals_cup = []

        for split_idx in range(2, len(seasons)):
            train_seasons = seasons[:split_idx]
            test_season = seasons[split_idx]

            # Get train and test data
            train_data = []
            for s in train_seasons:
                train_data.extend(by_season[s])

            test_data = by_season[test_season]

            if len(train_data) < 32 or len(test_data) < 16:
                continue

            # Train model
            if model_factory is None:
                model = EnsemblePredictor()
            else:
                model = model_factory()
            model.fit(train_data)

            # Predict
            predictions = model.predict(test_data)

            # Collect results
            for pred in predictions:
                team_data = next(
                    (t for t in test_data if t.team == pred.team),
                    None
                )
                if team_data:
                    all_predictions.append(pred)
                    all_actuals_playoff.append(1 if team_data.made_playoffs else 0)
                    all_actuals_cup.append(1 if team_data.won_cup else 0)

            logger.info(
                f"CV split {split_idx}: train seasons {train_seasons}, "
                f"test season {test_season}"
            )

        if not all_predictions:
            return self._empty_result()

        # Calculate metrics
        result = self._calculate_metrics(
            all_predictions,
            all_actuals_playoff,
            all_actuals_cup
        )

        self.results.append(result)
        return result

    def backtest(
        self,
        historical_data: List[TeamSeason],
        test_seasons: List[int]
    ) -> ValidationResult:
        """
        Backtest on specific seasons.

        Trains on all data before test_seasons, then evaluates
        on test_seasons.
        """
        # Split data
        train_data = [t for t in historical_data if t.season not in test_seasons]
        test_data = [t for t in historical_data if t.season in test_seasons]

        if len(train_data) < 32 or len(test_data) < 16:
            logger.warning("Insufficient data for backtest")
            return self._empty_result()

        logger.info(
            f"Backtest: {len(train_data)} training samples, "
            f"{len(test_data)} test samples"
        )

        # Train model
        model = EnsemblePredictor()
        model.fit(train_data)

        # Predict
        predictions = model.predict(test_data)

        # Collect actuals
        actuals_playoff = []
        actuals_cup = []

        for pred in predictions:
            team_data = next(
                (t for t in test_data if t.team == pred.team and t.season == pred.season),
                None
            )
            if team_data:
                actuals_playoff.append(1 if team_data.made_playoffs else 0)
                actuals_cup.append(1 if team_data.won_cup else 0)

        result = self._calculate_metrics(predictions, actuals_playoff, actuals_cup)
        self.results.append(result)
        return result

    def analyze_calibration(
        self,
        predictions: List[PredictionResult],
        actuals: List[int],
        n_bins: int = 10
    ) -> List[CalibrationBin]:
        """
        Analyze probability calibration.

        For well-calibrated predictions:
        - 20% predicted -> ~20% actual rate
        - 50% predicted -> ~50% actual rate
        """
        if not predictions:
            return []

        pred_probs = np.array([p.playoff_probability for p in predictions])
        actual_array = np.array(actuals)

        # Use sklearn calibration curve
        try:
            prob_true, prob_pred = calibration_curve(
                actual_array, pred_probs,
                n_bins=n_bins, strategy='uniform'
            )

            bins = []
            for i in range(len(prob_pred)):
                bins.append(CalibrationBin(
                    predicted_prob=float(prob_pred[i]),
                    actual_rate=float(prob_true[i]),
                    n_samples=int(len(predictions) / n_bins)
                ))
            return bins
        except Exception as e:
            logger.warning(f"Calibration analysis failed: {e}")
            return []

    def _calculate_metrics(
        self,
        predictions: List[PredictionResult],
        actuals_playoff: List[int],
        actuals_cup: List[int]
    ) -> ValidationResult:
        """Calculate validation metrics."""
        pred_playoff = np.array([p.playoff_probability for p in predictions])
        pred_cup = np.array([p.cup_win_probability for p in predictions])
        actual_playoff = np.array(actuals_playoff)
        actual_cup = np.array(actuals_cup)

        # Brier scores (lower is better, 0 is perfect)
        brier_playoff = brier_score_loss(actual_playoff, pred_playoff)
        brier_cup = brier_score_loss(actual_cup, pred_cup)

        # Log loss for playoff (handle edge cases)
        pred_playoff_clipped = np.clip(pred_playoff, 1e-10, 1 - 1e-10)
        try:
            logloss_playoff = log_loss(actual_playoff, pred_playoff_clipped)
        except Exception:
            logloss_playoff = float('nan')

        # Calibration error (mean absolute difference from perfect calibration)
        try:
            prob_true, prob_pred = calibration_curve(
                actual_playoff, pred_playoff,
                n_bins=5, strategy='uniform'
            )
            calibration_error = np.mean(np.abs(prob_true - prob_pred))
        except Exception:
            calibration_error = float('nan')

        # Accuracy (threshold at 0.5)
        pred_binary = (pred_playoff >= 0.5).astype(int)
        accuracy = np.mean(pred_binary == actual_playoff)

        # Cup winner picks
        n_cup_events = int(actual_cup.sum())
        n_correct = 0
        if n_cup_events > 0:
            # For each season with a Cup winner, check if our top pick won
            # Group by season
            by_season = defaultdict(list)
            for pred, actual in zip(predictions, actuals_cup):
                by_season[pred.season].append((pred, actual))

            for season, season_data in by_season.items():
                if any(a for _, a in season_data):
                    # Find our top pick
                    top_pick = max(season_data, key=lambda x: x[0].cup_win_probability)
                    if top_pick[1] == 1:
                        n_correct += 1

        return ValidationResult(
            brier_score_playoff=float(brier_playoff),
            brier_score_cup=float(brier_cup),
            log_loss_playoff=float(logloss_playoff),
            calibration_error=float(calibration_error),
            accuracy_playoff=float(accuracy),
            n_samples=len(predictions),
            n_correct_cup_picks=n_correct,
            n_cup_events=n_cup_events
        )

    def _empty_result(self) -> ValidationResult:
        """Return empty validation result."""
        return ValidationResult(
            brier_score_playoff=float('nan'),
            brier_score_cup=float('nan'),
            log_loss_playoff=float('nan'),
            calibration_error=float('nan'),
            accuracy_playoff=0.0,
            n_samples=0,
            n_correct_cup_picks=0,
            n_cup_events=0
        )

    def print_summary(self) -> None:
        """Print validation summary."""
        if not self.results:
            print("No validation results available")
            return

        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        for i, result in enumerate(self.results):
            print(f"\nRun {i + 1}:")
            print(f"  Samples: {result.n_samples}")
            print(f"  Brier Score (Playoff): {result.brier_score_playoff:.4f}")
            print(f"  Brier Score (Cup): {result.brier_score_cup:.4f}")
            print(f"  Log Loss (Playoff): {result.log_loss_playoff:.4f}")
            print(f"  Calibration Error: {result.calibration_error:.4f}")
            print(f"  Playoff Accuracy: {result.accuracy_playoff:.1%}")
            if result.n_cup_events > 0:
                print(f"  Cup Picks: {result.n_correct_cup_picks}/{result.n_cup_events}")

        # Aggregate
        if len(self.results) > 1:
            avg_brier = np.mean([r.brier_score_playoff for r in self.results])
            avg_acc = np.mean([r.accuracy_playoff for r in self.results])
            print(f"\nAggregate:")
            print(f"  Mean Brier (Playoff): {avg_brier:.4f}")
            print(f"  Mean Accuracy: {avg_acc:.1%}")


@dataclass
class BacktestSeasonResult:
    """Result from backtesting a single held-out season."""
    season: int
    model_top_pick: str
    model_top_5: List[str]
    actual_winner: str
    winner_in_top_5: bool
    model_prob_for_winner: float
    top_pick_correct: bool
    winner_rank: int
    playoff_teams_hit: int
    playoff_precision: float
    playoff_recall: float
    playoff_f1: float


def _predict_playoff_field_nhl(predictions: List[PredictionResult]) -> set[str]:
    """
    Predict playoff field using NHL qualification rules:
    top 3 per division + 2 wildcards per conference.
    """
    team_scores = {p.team: float(p.playoff_probability) for p in predictions}
    predicted: set[str] = set()
    for conf in ("East", "West"):
        qualifiers = select_conference_playoff_teams(conf, team_scores)
        predicted.update(team for team, _ in qualifiers[:8])
    return predicted


def generate_backtest_report(
    historical_data: List[TeamSeason],
    cache_path: Optional[str] = None,
    force_refresh: bool = False,
    model_overrides: Optional[Dict] = None,
) -> Dict:
    """
    Strict walk-forward backtest across all seasons.

    For each held-out season: train only on prior seasons, predict,
    then record Cup-winner ranking and playoff-team classification quality.

    Args:
        historical_data: All historical team-season data
        cache_path: If provided, load from / save to this cache file

    Returns:
        Dict with season-by-season results and summary stats
    """
    np.random.seed(RANDOM_SEED)
    from .config import CURRENT_SEASON

    module_paths = [
        Path(__file__),
        Path(__file__).with_name("models.py"),
        Path(__file__).with_name("real_data_loader.py"),
        Path(__file__).with_name("feature_engineering.py"),
        Path(__file__).with_name("config.py"),
    ]
    code_hash = _compute_file_signature(module_paths)
    data_hash = _compute_historical_data_signature()
    model_overrides = model_overrides or {}
    override_hash = hashlib.sha256(
        json.dumps(model_overrides, sort_keys=True).encode("utf-8")
    ).hexdigest()[:10]
    MODEL_VERSION = f"backtest-v2.4-{CURRENT_SEASON}-{code_hash}-{data_hash}-{override_hash}"

    # Check cache
    if cache_path and not force_refresh:
        cache_file = Path(cache_path)
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    cached = json.load(f)
                cache_is_current = (
                    cached.get("modelVersion") == MODEL_VERSION
                    and cached.get("evaluationMode") == "strict_walk_forward"
                    and "averageWinnerRank" in cached.get("summary", {})
                )
                if cache_is_current:
                    logger.info(f"Loading valid backtest cache from {cache_file}")
                    return cached
                else:
                    logger.info("Backtest cache stale (version mismatch), regenerating")
            except Exception as e:
                logger.warning(f"Failed to read backtest cache: {e}")

    # Group data by season
    by_season: Dict[int, List[TeamSeason]] = defaultdict(list)
    for team in historical_data:
        by_season[team.season].append(team)

    seasons = sorted(by_season.keys())
    results = []
    walk_forward_splits = []
    skipped_splits = []
    strict_oof_required = bool(
        model_overrides.get("strict_verification")
        and model_overrides.get("require_oof_cup_calibration_in_strict_mode")
    )

    for held_out in seasons:
        # Strict walk-forward: no future leakage allowed.
        train_data = [t for t in historical_data if t.season < held_out]
        test_data = by_season[held_out]
        train_seasons = sorted({t.season for t in train_data})
        min_train = train_seasons[0] if train_seasons else None
        max_train = train_seasons[-1] if train_seasons else None

        if len(train_data) < 64 or len(test_data) < 16:
            skipped_splits.append(
                {
                    "heldOutSeason": held_out,
                    "reason": "insufficient_train_or_test_samples",
                    "trainSamples": len(train_data),
                    "testSamples": len(test_data),
                }
            )
            continue

        # Strict OOF Cup calibration is mathematically underpowered in very
        # early windows. Skip these windows explicitly to avoid noisy retries.
        if strict_oof_required and len(train_seasons) < 5:
            skipped_splits.append(
                {
                    "heldOutSeason": held_out,
                    "reason": "insufficient_oof_cup_history",
                    "trainSeasonCount": len(train_seasons),
                }
            )
            continue

        # Find actual winner
        actual_winner = None
        for t in test_data:
            if t.won_cup:
                actual_winner = t.team
                break

        if actual_winner is None:
            continue

        # Train and predict
        model_kwargs = {"use_neural_network": False}
        model_kwargs.update(model_overrides)
        model = EnsemblePredictor(**model_kwargs)
        try:
            model.fit(train_data)
            predictions = model.predict(test_data)
        except Exception as e:
            skipped_splits.append(
                {
                    "heldOutSeason": held_out,
                    "reason": "model_fit_or_predict_failed",
                    "error": str(e),
                }
            )
            logger.warning(f"Backtest failed for season {held_out}: {e}")
            continue

        # Sort by Cup probability
        predictions.sort(key=lambda p: -p.cup_win_probability)

        top_pick = predictions[0].team
        top_5 = [p.team for p in predictions[:5]]
        winner_pred = next((p for p in predictions if p.team == actual_winner), None)
        winner_prob = winner_pred.cup_win_probability if winner_pred else 0.0
        winner_rank = next(
            (idx + 1 for idx, p in enumerate(predictions) if p.team == actual_winner),
            len(predictions)
        )

        # Predict playoff field using NHL conference/division wildcard rules.
        predicted_playoff = _predict_playoff_field_nhl(predictions)
        actual_playoff = {t.team for t in test_data if t.made_playoffs}
        playoff_hit = len(predicted_playoff.intersection(actual_playoff))

        # Binary classification quality for playoff teams (per season).
        # Use team order from test_data for stable y_true/y_pred alignment.
        y_true = np.array([1 if t.team in actual_playoff else 0 for t in test_data])
        y_pred = np.array([1 if t.team in predicted_playoff else 0 for t in test_data])
        playoff_precision = precision_score(y_true, y_pred, zero_division=0)
        playoff_recall = recall_score(y_true, y_pred, zero_division=0)
        playoff_f1 = f1_score(y_true, y_pred, zero_division=0)

        result = BacktestSeasonResult(
            season=held_out,
            model_top_pick=top_pick,
            model_top_5=top_5,
            actual_winner=actual_winner,
            winner_in_top_5=actual_winner in top_5,
            model_prob_for_winner=winner_prob,
            top_pick_correct=(top_pick == actual_winner),
            winner_rank=winner_rank,
            playoff_teams_hit=playoff_hit,
            playoff_precision=float(playoff_precision),
            playoff_recall=float(playoff_recall),
            playoff_f1=float(playoff_f1),
        )
        results.append(result)
        walk_forward_splits.append(
            {
                "heldOutSeason": held_out,
                "minTrainSeason": min_train,
                "maxTrainSeason": max_train,
                "trainSeasonCount": len(train_seasons),
            }
        )

        logger.info(
            f"Season {held_out}: top pick={top_pick}, "
            f"winner={actual_winner}, in top 5={actual_winner in top_5}"
        )

    # Summary
    n_seasons = len(results)
    n_top_pick_correct = sum(1 for r in results if r.top_pick_correct)
    n_winner_in_top_5 = sum(1 for r in results if r.winner_in_top_5)
    avg_winner_rank = float(np.mean([r.winner_rank for r in results])) if n_seasons > 0 else 0.0
    avg_playoff_hit = float(np.mean([r.playoff_teams_hit for r in results])) if n_seasons > 0 else 0.0
    avg_playoff_precision = float(np.mean([r.playoff_precision for r in results])) if n_seasons > 0 else 0.0
    avg_playoff_recall = float(np.mean([r.playoff_recall for r in results])) if n_seasons > 0 else 0.0
    avg_playoff_f1 = float(np.mean([r.playoff_f1 for r in results])) if n_seasons > 0 else 0.0

    leakage_free = all(
        split["maxTrainSeason"] is not None and split["maxTrainSeason"] < split["heldOutSeason"]
        for split in walk_forward_splits
    )

    report = {
        "modelVersion": MODEL_VERSION,
        "evaluationMode": "strict_walk_forward",
        "walkForwardAudit": {
            "leakageFree": leakage_free,
            "evaluatedSplits": len(walk_forward_splits),
            "skippedSplits": skipped_splits,
            "splits": walk_forward_splits,
        },
        "seasons": [
            {
                "season": r.season,
                "modelTopPick": r.model_top_pick,
                "modelTop5": r.model_top_5,
                "actualWinner": r.actual_winner,
                "winnerInTop5": r.winner_in_top_5,
                "modelProbForWinner": round(r.model_prob_for_winner * 100, 2),
                "topPickCorrect": r.top_pick_correct,
                "winnerRank": r.winner_rank,
                "playoffTeamsHit": r.playoff_teams_hit,
                "playoffPrecision": round(r.playoff_precision, 3),
                "playoffRecall": round(r.playoff_recall, 3),
                "playoffF1": round(r.playoff_f1, 3),
            }
            for r in results
        ],
        "summary": {
            "totalSeasons": n_seasons,
            "topPickCorrect": n_top_pick_correct,
            "topPickAccuracy": round(n_top_pick_correct / n_seasons * 100, 1) if n_seasons > 0 else 0,
            "winnerInTop5": n_winner_in_top_5,
            "top5Accuracy": round(n_winner_in_top_5 / n_seasons * 100, 1) if n_seasons > 0 else 0,
            "averageWinnerRank": round(avg_winner_rank, 2),
            "averagePlayoffTeamsHit": round(avg_playoff_hit, 2),
            "averagePlayoffPrecision": round(avg_playoff_precision, 3),
            "averagePlayoffRecall": round(avg_playoff_recall, 3),
            "averagePlayoffF1": round(avg_playoff_f1, 3),
        }
    }

    # Save cache
    if cache_path:
        cache_file = Path(cache_path)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Saved backtest cache to {cache_file}")

    return report


def benchmark_against_baseline(
    predictions: List[PredictionResult],
    actuals: List[int]
) -> Dict[str, float]:
    """
    Compare model against naive baselines.

    Baselines:
    - Random: 50% for everyone
    - Points-based: Sort by points, top 16 = playoffs
    """
    pred_probs = np.array([p.playoff_probability for p in predictions])
    actual = np.array(actuals)

    # Model Brier score
    model_brier = brier_score_loss(actual, pred_probs)

    # Random baseline (0.5 for everyone)
    random_preds = np.full(len(actual), 0.5)
    random_brier = brier_score_loss(actual, random_preds)

    # Improvement over random
    improvement = (random_brier - model_brier) / random_brier * 100

    return {
        'model_brier': model_brier,
        'random_brier': random_brier,
        'improvement_pct': improvement
    }


def _blend_toward_mean(value: float, mean: float, alpha: float) -> float:
    """Blend a value toward a league mean based on checkpoint progress."""
    return mean + alpha * (value - mean)


def _to_checkpoint_view(season_teams: List[TeamSeason], checkpoint_games: int) -> List[TeamSeason]:
    """
    Approximate partial-season team profiles at a given games-played checkpoint.

    Since historical snapshots are season-end aggregates, this creates a
    conservative partial-information view by:
    - Scaling counting stats by progress
    - Shrinking rate-based stats toward season league means
    """
    if not season_teams:
        return []

    league_means = {
        "cf_pct": float(np.mean([t.cf_pct for t in season_teams])),
        "hdcf_pct": float(np.mean([t.hdcf_pct for t in season_teams])),
        "pp_pct": float(np.mean([t.pp_pct for t in season_teams])),
        "pk_pct": float(np.mean([t.pk_pct for t in season_teams])),
        "pdo": float(np.mean([t.pdo for t in season_teams])),
        "save_pct": float(np.mean([t.save_pct for t in season_teams])),
        "gsax": float(np.mean([t.gsax for t in season_teams])),
        "xgf_pct": float(np.mean([t.xgf_pct for t in season_teams])),
    }

    checkpoint_teams: List[TeamSeason] = []
    for ts in season_teams:
        if checkpoint_games <= 0:
            alpha = 0.0
        else:
            denom = ts.games_played if ts.games_played > 0 else 82
            alpha = min(1.0, checkpoint_games / denom)

        cp = replace(ts)
        cp.games_played = int(round((ts.games_played if ts.games_played > 0 else 82) * alpha))
        cp.wins = int(round(ts.wins * alpha))
        cp.losses = int(round(ts.losses * alpha))
        cp.ot_losses = int(round(ts.ot_losses * alpha))
        cp.points = int(round(ts.points * alpha))
        cp.goals_for = int(round(ts.goals_for * alpha))
        cp.goals_against = int(round(ts.goals_against * alpha))

        cp.home_wins = int(round(ts.home_wins * alpha))
        cp.home_losses = int(round(ts.home_losses * alpha))
        cp.home_ot_losses = int(round(ts.home_ot_losses * alpha))
        cp.away_wins = int(round(ts.away_wins * alpha))
        cp.away_losses = int(round(ts.away_losses * alpha))
        cp.away_ot_losses = int(round(ts.away_ot_losses * alpha))

        cp.cf_pct = _blend_toward_mean(ts.cf_pct, league_means["cf_pct"], alpha)
        cp.ff_pct = cp.cf_pct
        cp.sf_pct = cp.cf_pct
        cp.hdcf_pct = _blend_toward_mean(ts.hdcf_pct, league_means["hdcf_pct"], alpha)
        cp.pp_pct = _blend_toward_mean(ts.pp_pct, league_means["pp_pct"], alpha)
        cp.pk_pct = _blend_toward_mean(ts.pk_pct, league_means["pk_pct"], alpha)
        cp.pdo = _blend_toward_mean(ts.pdo, league_means["pdo"], alpha)
        cp.save_pct = _blend_toward_mean(ts.save_pct, league_means["save_pct"], alpha)
        cp.gsax = _blend_toward_mean(ts.gsax, league_means["gsax"], alpha)
        cp.xgf_pct = _blend_toward_mean(ts.xgf_pct, league_means["xgf_pct"], alpha)
        cp.xgf = ts.xgf * alpha
        cp.xga = ts.xga * alpha
        cp.expected_goals_diff = cp.xgf - cp.xga

        checkpoint_teams.append(cp)

    return checkpoint_teams


def generate_checkpoint_backtest_report(
    historical_data: List[TeamSeason],
    checkpoints: Optional[List[int]] = None,
    model_overrides: Optional[Dict] = None,
) -> Dict:
    """
    Evaluate playoff-field quality at multiple season checkpoints.

    Checkpoints are interpreted as games played (e.g., 0/20/40/60).
    """
    np.random.seed(RANDOM_SEED)
    model_overrides = model_overrides or {}
    if checkpoints is None:
        checkpoints = [0, 20, 40, 60]

    by_season: Dict[int, List[TeamSeason]] = defaultdict(list)
    for team in historical_data:
        by_season[team.season].append(team)
    seasons = sorted(by_season.keys())

    checkpoint_summaries = []

    for checkpoint in checkpoints:
        f1_scores = []
        precision_scores = []
        recall_scores = []
        hits = []
        evaluated = 0

        for held_out in seasons:
            train_seasons = [s for s in seasons if s < held_out]
            if len(train_seasons) < 2:
                continue

            train_data = []
            for season in train_seasons:
                train_data.extend(_to_checkpoint_view(by_season[season], checkpoint))
            test_data = _to_checkpoint_view(by_season[held_out], checkpoint)

            if len(train_data) < 64 or len(test_data) < 16:
                continue

            model_kwargs = {
                "use_neural_network": False,
                "use_recency_weighting": False,
                "use_cup_calibration": False,
            }
            model_kwargs.update(model_overrides)
            model = EnsemblePredictor(**model_kwargs)
            try:
                model.fit(train_data)
                predictions = model.predict(test_data)
            except Exception:
                continue

            predicted_playoff = _predict_playoff_field_nhl(predictions)
            actual_playoff = {t.team for t in by_season[held_out] if t.made_playoffs}

            y_true = np.array([1 if t.team in actual_playoff else 0 for t in by_season[held_out]])
            y_pred = np.array([1 if t.team in predicted_playoff else 0 for t in by_season[held_out]])

            f1_scores.append(float(f1_score(y_true, y_pred, zero_division=0)))
            precision_scores.append(float(precision_score(y_true, y_pred, zero_division=0)))
            recall_scores.append(float(recall_score(y_true, y_pred, zero_division=0)))
            hits.append(len(predicted_playoff.intersection(actual_playoff)))
            evaluated += 1

        checkpoint_summaries.append({
            "checkpointGames": checkpoint,
            "evaluatedSeasons": evaluated,
            "averagePlayoffTeamsHit": round(float(np.mean(hits)), 2) if hits else 0.0,
            "averagePlayoffPrecision": round(float(np.mean(precision_scores)), 3) if precision_scores else 0.0,
            "averagePlayoffRecall": round(float(np.mean(recall_scores)), 3) if recall_scores else 0.0,
            "averagePlayoffF1": round(float(np.mean(f1_scores)), 3) if f1_scores else 0.0,
        })

    return {
        "mode": "checkpoint_backtest",
        "checkpoints": checkpoint_summaries,
    }
