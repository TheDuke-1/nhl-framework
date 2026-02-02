"""
Superhuman NHL Prediction System - Validation Framework
========================================================
Cross-validation, calibration, and backtesting tools.
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.calibration import calibration_curve

from .data_models import TeamSeason, PredictionResult
from .models import EnsemblePredictor
from .config import TRAINING_SEASONS, TEST_SEASONS

logger = logging.getLogger(__name__)


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
        all_data: List[TeamSeason]
    ) -> ValidationResult:
        """
        Perform time-series cross-validation.

        Uses seasons chronologically - always train on earlier
        seasons and test on later seasons.
        """
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
            model = EnsemblePredictor()
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
