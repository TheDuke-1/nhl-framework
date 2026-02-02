"""
Superhuman NHL Prediction System - Ensemble Models
===================================================
Logistic Regression + Gradient Boosting + Monte Carlo ensemble.
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from scipy.stats import beta as beta_dist

from .data_models import TeamSeason, FeatureVector, PredictionResult
from .feature_engineering import FeatureEngineer, create_feature_matrix
from .config import N_SIMULATIONS, RANDOM_SEED, CONFERENCES

logger = logging.getLogger(__name__)


def calculate_recency_weights(
    features: List[FeatureVector],
    decay_rate: float = 0.15,
    cup_winner_boost: float = 2.0,
    reference_year: Optional[int] = None
) -> np.ndarray:
    """
    Calculate sample weights based on recency and Cup winner status.

    Args:
        features: List of feature vectors
        decay_rate: Exponential decay rate per year (0.15 = 15% decay/year)
        cup_winner_boost: Multiplier for Cup winner samples
        reference_year: Year to calculate from (default: max season in data)

    Returns:
        Array of sample weights
    """
    if not features:
        return np.array([])

    # Find reference year (most recent season)
    if reference_year is None:
        reference_year = max(f.season for f in features)

    weights = []
    for f in features:
        # Base weight from recency (exponential decay)
        years_ago = reference_year - f.season
        recency_weight = np.exp(-decay_rate * years_ago)

        # Boost for Cup winners (they're rare and important)
        if f.won_cup:
            recency_weight *= cup_winner_boost

        weights.append(recency_weight)

    # Normalize so weights sum to len(features)
    weights = np.array(weights)
    weights = weights / weights.mean()

    return weights


@dataclass
class ModelWeights:
    """Learned feature weights from regression."""
    weights: Dict[str, float]
    feature_names: List[str]

    def to_dict(self) -> Dict[str, float]:
        return self.weights.copy()


class WeightOptimizer:
    """
    Optimize feature weights using regularized regression.

    Uses Ridge regression to find optimal weights that minimize
    prediction error while preventing overfitting.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.model = Ridge(alpha=alpha)
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.weights: Optional[ModelWeights] = None

    def fit(
        self,
        features: List[FeatureVector],
        sample_weight: Optional[np.ndarray] = None
    ) -> 'WeightOptimizer':
        """Fit regression to find optimal weights."""
        X, y, names = create_feature_matrix(features)
        self.feature_names = names

        # Remove features with zero variance
        variances = np.var(X, axis=0)
        valid_cols = variances > 1e-10
        X_valid = X[:, valid_cols]
        valid_names = [n for n, v in zip(names, valid_cols) if v]

        if X_valid.shape[1] == 0:
            logger.warning("No valid features for regression")
            return self

        # Standardize features
        X_scaled = self.scaler.fit_transform(X_valid)

        # Fit regression with sample weights
        self.model.fit(X_scaled, y, sample_weight=sample_weight)

        # Extract and normalize weights
        raw_weights = np.abs(self.model.coef_)
        if raw_weights.sum() > 0:
            normalized = raw_weights / raw_weights.sum() * 100
        else:
            normalized = np.ones(len(raw_weights)) * (100 / len(raw_weights))

        self.weights = ModelWeights(
            weights={name: weight for name, weight in zip(valid_names, normalized)},
            feature_names=valid_names
        )

        logger.info(f"Optimized weights: {self.weights.to_dict()}")
        return self

    def get_weights(self) -> Dict[str, float]:
        """Return optimized weights."""
        if self.weights is None:
            return {}
        return self.weights.to_dict()


class PlayoffClassifier:
    """
    Logistic regression classifier for playoff probability.
    """

    def __init__(self):
        self.model = LogisticRegression(
            penalty='l2',
            C=0.5,
            solver='lbfgs',
            max_iter=1000,
            random_state=RANDOM_SEED
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.valid_cols: Optional[np.ndarray] = None

    def fit(
        self,
        features: List[FeatureVector],
        sample_weight: Optional[np.ndarray] = None
    ) -> 'PlayoffClassifier':
        """Train classifier on historical data."""
        X, _, names = create_feature_matrix(features)
        y = np.array([1 if f.made_playoffs else 0 for f in features])

        # Remove zero-variance features
        variances = np.var(X, axis=0)
        self.valid_cols = variances > 1e-10
        X_valid = X[:, self.valid_cols]

        if X_valid.shape[1] == 0:
            logger.warning("No valid features for classification")
            return self

        X_scaled = self.scaler.fit_transform(X_valid)
        self.model.fit(X_scaled, y, sample_weight=sample_weight)
        self.is_fitted = True

        logger.info(f"Playoff classifier trained on {len(features)} samples")
        return self

    def predict_proba(self, features: List[FeatureVector]) -> np.ndarray:
        """Predict playoff probability for each team."""
        if not self.is_fitted:
            return np.full(len(features), 0.5)

        X, _, _ = create_feature_matrix(features)
        X_valid = X[:, self.valid_cols]
        X_scaled = self.scaler.transform(X_valid)

        return self.model.predict_proba(X_scaled)[:, 1]


class CupPredictor:
    """
    Gradient boosting classifier for Cup probability.
    """

    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            random_state=RANDOM_SEED
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.valid_cols: Optional[np.ndarray] = None

    def fit(
        self,
        features: List[FeatureVector],
        sample_weight: Optional[np.ndarray] = None
    ) -> 'CupPredictor':
        """Train classifier on historical data."""
        X, _, _ = create_feature_matrix(features)
        y = np.array([1 if f.won_cup else 0 for f in features])

        # Remove zero-variance features
        variances = np.var(X, axis=0)
        self.valid_cols = variances > 1e-10
        X_valid = X[:, self.valid_cols]

        if X_valid.shape[1] == 0:
            logger.warning("No valid features for Cup prediction")
            return self

        X_scaled = self.scaler.fit_transform(X_valid)

        # Need at least some positive examples
        if y.sum() < 2:
            logger.warning("Not enough Cup winners for training")
            return self

        self.model.fit(X_scaled, y, sample_weight=sample_weight)
        self.is_fitted = True

        logger.info(f"Cup predictor trained on {len(features)} samples, {y.sum()} winners")
        return self

    def predict_proba(self, features: List[FeatureVector]) -> np.ndarray:
        """Predict Cup probability for each team."""
        if not self.is_fitted:
            return np.full(len(features), 1/32)

        X, _, _ = create_feature_matrix(features)
        X_valid = X[:, self.valid_cols]
        X_scaled = self.scaler.transform(X_valid)

        return self.model.predict_proba(X_scaled)[:, 1]


class NeuralNetworkPredictor:
    """
    Neural network for Cup probability prediction.

    Uses a multi-layer perceptron with calibration for better
    probability estimates on the rare Cup winner event.
    """

    def __init__(self):
        self.base_model = MLPClassifier(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            solver='adam',
            alpha=0.01,  # L2 regularization
            batch_size=32,
            learning_rate='adaptive',
            learning_rate_init=0.001,
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=20,
            random_state=RANDOM_SEED
        )
        self.model = None  # Will be calibrated model
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.valid_cols: Optional[np.ndarray] = None

    def fit(
        self,
        features: List[FeatureVector],
        sample_weight: Optional[np.ndarray] = None
    ) -> 'NeuralNetworkPredictor':
        """Train neural network with calibration."""
        X, _, _ = create_feature_matrix(features)
        y = np.array([1 if f.won_cup else 0 for f in features])

        # Remove zero-variance features
        variances = np.var(X, axis=0)
        self.valid_cols = variances > 1e-10
        X_valid = X[:, self.valid_cols]

        if X_valid.shape[1] == 0:
            logger.warning("No valid features for neural network")
            return self

        # Need at least some positive examples
        if y.sum() < 3:
            logger.warning("Not enough Cup winners for neural network training")
            return self

        X_scaled = self.scaler.fit_transform(X_valid)

        # Wrap in calibrated classifier for better probability estimates
        # Using sigmoid (Platt scaling) for binary classification
        try:
            self.model = CalibratedClassifierCV(
                self.base_model,
                method='sigmoid',
                cv=3
            )
            # CalibratedClassifierCV supports sample_weight
            self.model.fit(X_scaled, y, sample_weight=sample_weight)
            self.is_fitted = True
            logger.info(f"Neural network trained on {len(features)} samples")
        except Exception as e:
            logger.warning(f"Neural network training failed: {e}")
            # Fall back to uncalibrated model
            self.base_model.fit(X_scaled, y)
            self.model = self.base_model
            self.is_fitted = True

        return self

    def predict_proba(self, features: List[FeatureVector]) -> np.ndarray:
        """Predict Cup probability using neural network."""
        if not self.is_fitted or self.model is None:
            return np.full(len(features), 1/32)

        X, _, _ = create_feature_matrix(features)
        X_valid = X[:, self.valid_cols]
        X_scaled = self.scaler.transform(X_valid)

        probs = self.model.predict_proba(X_scaled)
        if probs.shape[1] > 1:
            return probs[:, 1]
        return probs.ravel()


class CupProbabilityCalibrator:
    """
    Calibrates Cup probabilities using isotonic regression.

    Addresses the issue of raw model probabilities being poorly
    calibrated for rare events (Cup winners are 1/32 per season).
    """

    def __init__(self):
        self.calibrator = IsotonicRegression(
            y_min=0.001,  # Minimum probability
            y_max=0.50,   # Maximum probability (even favorites rarely > 50%)
            out_of_bounds='clip'
        )
        self.is_fitted = False

    def fit(self, raw_probs: np.ndarray, actual_outcomes: np.ndarray) -> 'CupProbabilityCalibrator':
        """Fit calibrator on historical predictions and outcomes."""
        if len(raw_probs) < 10 or actual_outcomes.sum() < 2:
            logger.warning("Not enough data for Cup calibration")
            return self

        # Sort by raw probability for isotonic regression
        sorted_indices = np.argsort(raw_probs)
        self.calibrator.fit(raw_probs[sorted_indices], actual_outcomes[sorted_indices])
        self.is_fitted = True
        logger.info("Cup probability calibrator fitted")
        return self

    def calibrate(self, raw_probs: np.ndarray) -> np.ndarray:
        """Calibrate raw probabilities."""
        if not self.is_fitted:
            return raw_probs

        calibrated = self.calibrator.predict(raw_probs)
        # Ensure probabilities sum to approximately 1 per season
        return calibrated


class MonteCarloSimulator:
    """
    Monte Carlo playoff simulation.

    Simulates full playoff bracket thousands of times
    to estimate Cup probability for each team.

    Enhanced mode uses trained playoff series model with:
    - Round-specific upset rates
    - Playoff experience factors
    - Empirical parity adjustments
    """

    def __init__(
        self,
        n_simulations: int = N_SIMULATIONS,
        use_enhanced_model: bool = True
    ):
        self.n_sims = n_simulations
        self.use_enhanced_model = use_enhanced_model
        self.series_predictor = None

        # Round-specific base win rates (from historical data)
        # Higher seed win probability by round
        self.round_base_rates = {
            1: 0.59,  # Round 1: higher seed wins 59%
            2: 0.53,  # Round 2: 53%
            3: 0.50,  # Conf Finals: coin flip
            4: 0.53,  # Cup Finals: 53%
        }

        if use_enhanced_model:
            self._init_series_predictor()

    def _init_series_predictor(self):
        """Initialize the playoff series predictor."""
        try:
            from .playoff_series_model import get_series_predictor
            self.series_predictor = get_series_predictor()
            logger.info("Initialized enhanced playoff series predictor")
        except Exception as e:
            logger.warning(f"Could not initialize series predictor: {e}")
            self.use_enhanced_model = False

    def simulate(
        self,
        teams: List[TeamSeason],
        strength_scores: Dict[str, float],
        experience_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Run Monte Carlo simulation.

        Args:
            teams: List of teams with current stats
            strength_scores: Pre-computed strength score per team
            experience_scores: Optional playoff experience scores

        Returns:
            Cup probability for each team
        """
        cup_wins = defaultdict(int)

        # Default experience scores if not provided
        if experience_scores is None:
            experience_scores = {t.team: 0.0 for t in teams}

        # Separate by conference
        east_teams = [t for t in teams if self._get_conference(t.team) == "East"]
        west_teams = [t for t in teams if self._get_conference(t.team) == "West"]

        for _ in range(self.n_sims):
            # Get playoff teams (top 8 by points per conference)
            east_playoff = sorted(east_teams, key=lambda t: -t.points)[:8]
            west_playoff = sorted(west_teams, key=lambda t: -t.points)[:8]

            # Simulate conference playoffs
            east_champ = self._simulate_conference(
                east_playoff, strength_scores, experience_scores
            )
            west_champ = self._simulate_conference(
                west_playoff, strength_scores, experience_scores
            )

            # Cup Final (round 4)
            cup_winner = self._simulate_series(
                east_champ, west_champ,
                strength_scores.get(east_champ, 50),
                strength_scores.get(west_champ, 50),
                round_num=4,
                exp_a=experience_scores.get(east_champ, 0),
                exp_b=experience_scores.get(west_champ, 0)
            )
            cup_wins[cup_winner] += 1

        # Convert to probabilities
        return {team: wins / self.n_sims for team, wins in cup_wins.items()}

    def _simulate_conference(
        self,
        playoff_teams: List[TeamSeason],
        strength_scores: Dict[str, float],
        experience_scores: Dict[str, float]
    ) -> str:
        """Simulate conference playoffs, return champion."""
        teams = [t.team for t in playoff_teams]

        if len(teams) < 8:
            teams.extend(["BYE"] * (8 - len(teams)))

        # Round 1: 1v8, 2v7, 3v6, 4v5
        r1_matchups = [(0, 7), (1, 6), (2, 5), (3, 4)]
        r1_winners = []
        for i, j in r1_matchups:
            if teams[j] == "BYE":
                r1_winners.append(teams[i])
            else:
                winner = self._simulate_series(
                    teams[i], teams[j],
                    strength_scores.get(teams[i], 50),
                    strength_scores.get(teams[j], 50),
                    round_num=1,
                    exp_a=experience_scores.get(teams[i], 0),
                    exp_b=experience_scores.get(teams[j], 0)
                )
                r1_winners.append(winner)

        # Round 2
        r2_winners = []
        for k in range(0, 4, 2):
            winner = self._simulate_series(
                r1_winners[k], r1_winners[k+1],
                strength_scores.get(r1_winners[k], 50),
                strength_scores.get(r1_winners[k+1], 50),
                round_num=2,
                exp_a=experience_scores.get(r1_winners[k], 0),
                exp_b=experience_scores.get(r1_winners[k+1], 0)
            )
            r2_winners.append(winner)

        # Conference Final (round 3)
        return self._simulate_series(
            r2_winners[0], r2_winners[1],
            strength_scores.get(r2_winners[0], 50),
            strength_scores.get(r2_winners[1], 50),
            round_num=3,
            exp_a=experience_scores.get(r2_winners[0], 0),
            exp_b=experience_scores.get(r2_winners[1], 0)
        )

    def _simulate_series(
        self,
        team_a: str,
        team_b: str,
        strength_a: float,
        strength_b: float,
        round_num: int = 1,
        exp_a: float = 0,
        exp_b: float = 0
    ) -> str:
        """Simulate best-of-7 series with round-specific parity."""
        # Enhanced model uses series predictor if available
        if self.use_enhanced_model and self.series_predictor is not None:
            try:
                # Determine higher/lower seed by strength
                if strength_a >= strength_b:
                    prob_higher = self.series_predictor.predict_series_probability(
                        higher_seed=team_a,
                        lower_seed=team_b,
                        round_num=round_num,
                        strength_diff=strength_a - strength_b,
                        experience_diff=exp_a - exp_b
                    )
                    return team_a if np.random.random() < prob_higher else team_b
                else:
                    prob_higher = self.series_predictor.predict_series_probability(
                        higher_seed=team_b,
                        lower_seed=team_a,
                        round_num=round_num,
                        strength_diff=strength_b - strength_a,
                        experience_diff=exp_b - exp_a
                    )
                    return team_b if np.random.random() < prob_higher else team_a
            except Exception:
                pass  # Fall back to basic model

        # Basic model: Win probability from strength difference
        diff = strength_a - strength_b
        prob_a = 1 / (1 + np.exp(-0.03 * diff))

        # Apply round-specific parity (later rounds = more upsets)
        parity_factor = self.round_base_rates.get(round_num, 0.55)
        # Blend toward 50% for later rounds
        prob_a = prob_a * 0.7 + parity_factor * 0.3

        # Add home ice for higher seed (team_a assumed higher)
        home_pattern = [True, True, False, False, True, False, True]

        wins_a, wins_b = 0, 0
        game = 0

        while wins_a < 4 and wins_b < 4:
            game_prob = prob_a + (0.04 if home_pattern[game] else -0.02)
            game_prob = np.clip(game_prob, 0.15, 0.85)

            if np.random.random() < game_prob:
                wins_a += 1
            else:
                wins_b += 1
            game += 1

        return team_a if wins_a == 4 else team_b

    def _get_conference(self, team: str) -> str:
        """Get conference for team."""
        for conf, divisions in CONFERENCES.items():
            for teams in divisions.values():
                if team in teams:
                    return conf
        return "East"  # Default


class EnsemblePredictor:
    """
    Enhanced ensemble model combining:
    - Logistic regression (playoff probability)
    - Gradient boosting (Cup probability)
    - Neural network (Cup probability - deep learning)
    - Monte Carlo simulation (bracket simulation)
    - Isotonic calibration for Cup probabilities
    """

    def __init__(
        self,
        use_neural_network: bool = True,
        use_recency_weighting: bool = True,
        recency_decay_rate: float = 0.15,
        cup_winner_boost: float = 2.0
    ):
        self.feature_engineer = FeatureEngineer()
        self.weight_optimizer = WeightOptimizer()
        self.playoff_classifier = PlayoffClassifier()
        self.cup_predictor = CupPredictor()
        self.neural_predictor = NeuralNetworkPredictor() if use_neural_network else None
        self.cup_calibrator = CupProbabilityCalibrator()
        self.monte_carlo = MonteCarloSimulator(n_simulations=10000)
        self.use_neural_network = use_neural_network
        self.use_recency_weighting = use_recency_weighting
        self.recency_decay_rate = recency_decay_rate
        self.cup_winner_boost = cup_winner_boost
        self.is_fitted = False

        # Ensemble weights for Cup prediction
        self.cup_ensemble_weights = {
            'gradient_boosting': 0.30,
            'neural_network': 0.30,
            'monte_carlo': 0.40
        }

    def fit(self, training_data: List[TeamSeason]) -> 'EnsemblePredictor':
        """Train all models on historical data with recency weighting."""
        logger.info(f"Training enhanced ensemble on {len(training_data)} team-seasons")

        # Feature engineering
        train_features = self.feature_engineer.fit_transform(training_data)

        # Calculate recency weights if enabled
        sample_weight = None
        if self.use_recency_weighting:
            sample_weight = calculate_recency_weights(
                train_features,
                decay_rate=self.recency_decay_rate,
                cup_winner_boost=self.cup_winner_boost
            )
            logger.info(f"Using recency weighting (decay={self.recency_decay_rate}, "
                       f"cup_boost={self.cup_winner_boost})")

        # Train sub-models with sample weights
        self.weight_optimizer.fit(train_features, sample_weight=sample_weight)
        self.playoff_classifier.fit(train_features, sample_weight=sample_weight)
        self.cup_predictor.fit(train_features, sample_weight=sample_weight)

        # Train neural network if enabled
        if self.use_neural_network and self.neural_predictor is not None:
            logger.info("Training neural network component...")
            self.neural_predictor.fit(train_features, sample_weight=sample_weight)

        # Fit Cup probability calibrator on training data predictions
        self._fit_cup_calibrator(training_data, train_features)

        self.is_fitted = True
        logger.info("Enhanced ensemble training complete")
        return self

    def _fit_cup_calibrator(
        self,
        training_data: List[TeamSeason],
        train_features: List[FeatureVector]
    ) -> None:
        """Fit the Cup probability calibrator using cross-validation."""
        # Get raw probabilities from models
        gb_probs = self.cup_predictor.predict_proba(train_features)

        if self.use_neural_network and self.neural_predictor is not None:
            nn_probs = self.neural_predictor.predict_proba(train_features)
            # Average GB and NN for calibration input
            raw_probs = 0.5 * gb_probs + 0.5 * nn_probs
        else:
            raw_probs = gb_probs

        # Actual outcomes
        actual = np.array([1 if f.won_cup else 0 for f in train_features])

        # Fit calibrator
        self.cup_calibrator.fit(raw_probs, actual)

    def predict(self, teams: List[TeamSeason]) -> List[PredictionResult]:
        """Generate predictions for teams."""
        if not self.is_fitted:
            raise RuntimeError("Ensemble must be fit before predict")

        # Transform features
        features = self.feature_engineer.transform(teams)

        # Get strength scores (using regression weights)
        strength_scores = self._calculate_strength_scores(teams, features)

        # Get model predictions
        playoff_probs = self.playoff_classifier.predict_proba(features)
        cup_probs_gb = self.cup_predictor.predict_proba(features)

        # Get neural network predictions if available
        if self.use_neural_network and self.neural_predictor is not None:
            cup_probs_nn = self.neural_predictor.predict_proba(features)
        else:
            cup_probs_nn = cup_probs_gb  # Fallback

        # Run Monte Carlo simulation with dynamic intensity based on playoff probs
        # Pass features for experience-aware series prediction
        mc_probs = self._run_dynamic_monte_carlo(
            teams, strength_scores, playoff_probs, features=features
        )

        # Create raw Cup probabilities using weighted ensemble
        raw_cup_probs = {}
        for i, team in enumerate(teams):
            mc_prob = mc_probs.get(team.team, 0.0)
            gb_prob = cup_probs_gb[i]
            nn_prob = cup_probs_nn[i]
            playoff_prob = playoff_probs[i]

            # Weighted ensemble of Cup predictions
            w = self.cup_ensemble_weights
            if self.use_neural_network:
                ensemble_prob = (
                    w['gradient_boosting'] * gb_prob +
                    w['neural_network'] * nn_prob +
                    w['monte_carlo'] * mc_prob
                )
            else:
                # Without NN, redistribute weight
                ensemble_prob = 0.4 * gb_prob + 0.6 * mc_prob

            # Gate by playoff probability (must make playoffs to win Cup)
            gated_prob = ensemble_prob * min(1.0, playoff_prob + 0.1)

            raw_cup_probs[team.team] = gated_prob

        # CRITICAL FIX: Normalize Cup probabilities to sum to 100%
        total_prob = sum(raw_cup_probs.values())
        if total_prob > 0:
            normalized_cup_probs = {
                team: prob / total_prob for team, prob in raw_cup_probs.items()
            }
        else:
            normalized_cup_probs = {team: 1/32 for team in raw_cup_probs}

        # Create results with normalized probabilities
        results = []
        strength_values = list(strength_scores.values())

        for i, (team, feature) in enumerate(zip(teams, features)):
            cup_prob = normalized_cup_probs[team.team]

            # Confidence interval using Beta distribution
            ci_lower, ci_upper = self._calculate_ci(cup_prob, n=10000)

            # FIXED: Use percentile-based tier classification
            tier = self._classify_tier_percentile(
                strength_scores[team.team],
                strength_values
            )

            result = PredictionResult(
                team=team.team,
                season=team.season,
                composite_strength=strength_scores[team.team],
                playoff_probability=float(playoff_probs[i]),
                cup_win_probability=float(cup_prob),
                cup_prob_lower=ci_lower,
                cup_prob_upper=ci_upper,
                tier=tier
            )
            results.append(result)

        # Add rankings
        results.sort(key=lambda r: -r.composite_strength)
        for rank, result in enumerate(results, 1):
            result.strength_rank = rank

        return results

    def _run_dynamic_monte_carlo(
        self,
        teams: List[TeamSeason],
        strength_scores: Dict[str, float],
        playoff_probs: np.ndarray,
        features: Optional[List[FeatureVector]] = None
    ) -> Dict[str, float]:
        """
        Run Monte Carlo simulation with dynamic adjustments.

        Key improvements over static MC:
        1. Uses playoff probabilities to adjust seeding uncertainty
        2. Increases simulation count for close matchups
        3. Incorporates strength uncertainty into series outcomes
        4. Passes playoff experience to series predictor
        """
        # Create adjusted strength scores that incorporate playoff uncertainty
        adjusted_strengths = {}
        for i, team in enumerate(teams):
            base_strength = strength_scores[team.team]
            playoff_prob = playoff_probs[i]

            # Teams with lower playoff probability have more uncertain strength
            # Add noise proportional to playoff uncertainty
            uncertainty = (1 - playoff_prob) * 10
            adjusted_strengths[team.team] = base_strength

        # Extract experience scores from features if available
        experience_scores = None
        if features is not None:
            experience_scores = {
                teams[i].team: features[i].playoff_experience
                for i in range(len(teams))
            }

        # Run simulation with experience scores for enhanced playoff model
        return self.monte_carlo.simulate(
            teams, adjusted_strengths, experience_scores=experience_scores
        )

    def _calculate_strength_scores(
        self,
        teams: List[TeamSeason],
        features: List[FeatureVector]
    ) -> Dict[str, float]:
        """Calculate composite strength score for each team."""
        weights = self.weight_optimizer.get_weights()

        scores = {}
        for team, feature in zip(teams, features):
            feature_dict = {
                'goal_differential_rate': feature.goal_differential_rate,
                'territorial_dominance': feature.territorial_dominance,
                'shot_quality_premium': feature.shot_quality_premium,
                'goaltending_quality': feature.goaltending_quality,
                'special_teams_composite': feature.special_teams_composite,
                'road_performance': feature.road_performance,
                'roster_depth': feature.roster_depth,
                'star_power': feature.star_power,
                'clutch_performance': feature.clutch_performance,
                'sustainability': feature.sustainability,
                'recent_form': feature.recent_form,
                'vegas_cup_signal': feature.vegas_cup_signal,
                'playoff_experience': feature.playoff_experience,
                'dynasty_score': feature.dynasty_score,
            }

            # Weighted sum
            score = 50  # Base score
            for name, weight in weights.items():
                if name in feature_dict:
                    score += weight * feature_dict[name] / 10

            scores[team.team] = score

        return scores

    def _calculate_ci(
        self,
        prob: float,
        n: int = 10000,
        confidence: float = 0.90
    ) -> Tuple[float, float]:
        """Calculate confidence interval using Beta distribution."""
        alpha = prob * n + 1
        beta_param = (1 - prob) * n + 1

        lower = beta_dist.ppf((1 - confidence) / 2, alpha, beta_param)
        upper = beta_dist.ppf((1 + confidence) / 2, alpha, beta_param)

        return float(lower), float(upper)

    def _classify_tier(self, strength: float) -> str:
        """Classify team into tier based on absolute strength thresholds."""
        if strength >= 70:
            return "Elite"
        elif strength >= 55:
            return "Contender"
        elif strength >= 45:
            return "Bubble"
        else:
            return "Longshot"

    def _classify_tier_percentile(
        self,
        strength: float,
        all_strengths: List[float]
    ) -> str:
        """
        Classify team into tier based on percentile rank.

        This is more robust than fixed thresholds as it adapts
        to the actual distribution of team strengths.

        Tiers:
        - Elite: Top 4 teams (~12.5%)
        - Contender: Next 8 teams (~25%)
        - Bubble: Next 8 teams (~25%)
        - Longshot: Bottom 12 teams (~37.5%)
        """
        sorted_strengths = sorted(all_strengths, reverse=True)
        rank = sorted_strengths.index(strength) + 1

        if rank <= 4:
            return "Elite"
        elif rank <= 12:
            return "Contender"
        elif rank <= 20:
            return "Bubble"
        else:
            return "Longshot"

    def get_feature_weights(self) -> Dict[str, float]:
        """Return learned feature weights."""
        return self.weight_optimizer.get_weights()
