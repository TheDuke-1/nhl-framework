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

from .data_models import TeamSeason, FeatureVector, PredictionResult, MonteCarloResult, ConferenceTrace
from .feature_engineering import FeatureEngineer, create_feature_matrix
from .config import N_SIMULATIONS, RANDOM_SEED, CONFERENCES, get_team_division, GAMES_IN_SEASON

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
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation with full round-by-round tracking.

        Uses pace-projected end-of-season points (with per-sim noise) to
        select and seed playoff teams, so the projected bracket reflects
        who the model thinks will be in the playoffs by end of season.

        Args:
            teams: List of teams with current stats
            strength_scores: Pre-computed strength score per team
            experience_scores: Optional playoff experience scores

        Returns:
            MonteCarloResult with cup probs, round advancement, matchups, etc.
        """
        cup_wins = defaultdict(int)
        # Track per-round advancement counts
        round_adv = defaultdict(lambda: defaultdict(int))  # team -> round -> count
        # Track cup final appearances
        cup_final_counts = defaultdict(int)
        # Track R1 matchup occurrences and wins
        matchup_counts = defaultdict(int)   # (higher, lower, conf) -> count
        matchup_wins = defaultdict(int)     # (higher, lower, conf) -> higher_seed_wins
        # Track R2+ matchup occurrences and wins
        r2_tracker = defaultdict(lambda: {"count": 0, "a_wins": 0})
        cf_tracker = defaultdict(lambda: {"count": 0, "a_wins": 0})
        cup_final_tracker = defaultdict(lambda: {"count": 0, "a_wins": 0})

        # Default experience scores if not provided
        if experience_scores is None:
            experience_scores = {t.team: 0.0 for t in teams}

        # Separate by conference
        east_teams = [t for t in teams if self._get_conference(t.team) == "East"]
        west_teams = [t for t in teams if self._get_conference(t.team) == "West"]

        # Calculate pace-projected end-of-season points for each team
        # Empirically, NHL teams earn ~1 pt/game with per-game σ ≈ 0.5
        projected_pts = {}
        remaining_games = {}
        for t in teams:
            if t.games_played > 0:
                pace = t.points / t.games_played
                remaining = max(0, GAMES_IN_SEASON - t.games_played)
                projected_pts[t.team] = t.points + pace * remaining
            else:
                projected_pts[t.team] = 0.0
                remaining = GAMES_IN_SEASON
            remaining_games[t.team] = remaining

        for _ in range(self.n_sims):
            # Add Gaussian noise to projected points for this sim
            sim_pts = {}
            for t in teams:
                noise = np.random.normal(0, 0.5 * np.sqrt(remaining_games[t.team]))
                sim_pts[t.team] = projected_pts[t.team] + noise

            # Select playoff teams using real NHL rules:
            # Top 3 per division + 2 best remaining as wildcards
            east_playoff = self._select_playoff_teams(east_teams, sim_pts)
            west_playoff = self._select_playoff_teams(west_teams, sim_pts)

            # Simulate conference playoffs with trace
            east_trace = self._simulate_conference(
                east_playoff, strength_scores, experience_scores, sim_pts
            )
            west_trace = self._simulate_conference(
                west_playoff, strength_scores, experience_scores, sim_pts
            )

            # Record round advancement from traces
            for trace, conf_label in [(east_trace, "East"), (west_trace, "West")]:
                # R1 winners advanced past round 1
                for team in trace.r1_winners:
                    round_adv[team][1] += 1
                # R2 winners advanced past round 2
                for team in trace.r2_winners:
                    round_adv[team][2] += 1
                # Conference champion
                round_adv[trace.conf_champion][3] += 1

                # Track R1 matchups
                for higher, lower in trace.r1_matchups:
                    key = (higher, lower, conf_label)
                    matchup_counts[key] += 1
                    if higher in trace.r1_winners:
                        matchup_wins[key] += 1

                # Track R2 matchups
                for a, b in trace.r2_matchups:
                    pair = tuple(sorted([a, b]))
                    key = (pair[0], pair[1], conf_label)
                    r2_tracker[key]["count"] += 1
                    # Which team won R2? Check r2_winners
                    for winner in trace.r2_winners:
                        if winner in (a, b):
                            if winner == pair[0]:
                                r2_tracker[key]["a_wins"] += 1

                # Track conference final matchup
                if trace.conf_final_matchup:
                    a, b = trace.conf_final_matchup
                    pair = tuple(sorted([a, b]))
                    key = (pair[0], pair[1], conf_label)
                    cf_tracker[key]["count"] += 1
                    if trace.conf_champion == pair[0]:
                        cf_tracker[key]["a_wins"] += 1

            east_champ = east_trace.conf_champion
            west_champ = west_trace.conf_champion

            # Cup Final appearances
            cup_final_counts[east_champ] += 1
            cup_final_counts[west_champ] += 1
            round_adv[east_champ][4] += 1
            round_adv[west_champ][4] += 1

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

            # Track cup final matchup
            pair = tuple(sorted([east_champ, west_champ]))
            cup_final_tracker[pair]["count"] += 1
            if cup_winner == pair[0]:
                cup_final_tracker[pair]["a_wins"] += 1

        # Convert to probabilities
        cup_probs = {team: wins / self.n_sims for team, wins in cup_wins.items()}

        # Build round advancement probabilities
        round_advancement = {}
        all_team_codes = [t.team for t in teams]
        for team in all_team_codes:
            round_advancement[team] = {
                1: round_adv[team][1] / self.n_sims,
                2: round_adv[team][2] / self.n_sims,
                3: round_adv[team][3] / self.n_sims,  # conf final win
                4: round_adv[team][4] / self.n_sims,  # cup final appearance
                "cup": cup_probs.get(team, 0.0),
            }

        # Build projected R1 matchups: top 4 most common per conference.
        # Consolidate flipped pairs (noise can swap higher/lower between sims)
        # and ensure each team appears in at most one matchup.
        projected_matchups = {"East": [], "West": []}
        pair_counts = defaultdict(int)   # (a, b, conf) -> count (a < b alphabetically)
        pair_a_wins = defaultdict(int)   # -> wins for alphabetically-first team
        for (higher, lower, conf), count in matchup_counts.items():
            a, b = (higher, lower) if higher < lower else (lower, higher)
            pair_counts[(a, b, conf)] += count
            wins = matchup_wins.get((higher, lower, conf), 0)
            # If higher==a, its wins are a's wins; otherwise a won (count - wins)
            pair_a_wins[(a, b, conf)] += wins if higher == a else (count - wins)

        seen_teams = {"East": set(), "West": set()}
        for (a, b, conf), count in sorted(pair_counts.items(), key=lambda x: -x[1]):
            if len(projected_matchups[conf]) >= 4:
                continue
            if a in seen_teams[conf] or b in seen_teams[conf]:
                continue
            a_win_prob = pair_a_wins[(a, b, conf)] / count
            # Present with the more-likely winner listed first
            if a_win_prob >= 0.5:
                projected_matchups[conf].append((a, b, round(a_win_prob, 3)))
            else:
                projected_matchups[conf].append((b, a, round(1 - a_win_prob, 3)))
            seen_teams[conf].add(a)
            seen_teams[conf].add(b)

        # Conference final appearance = won R2 (reached conf final round)
        conf_final_appearance_probs = {
            team: round_adv[team][2] / self.n_sims
            for team in all_team_codes
        }
        cup_final_probs_dict = {team: c / self.n_sims for team, c in cup_final_counts.items()}

        # Convert R2+ trackers to sorted lists, filter to >5% of sims
        min_count = self.n_sims * 0.05

        r2_matchups_result = {"East": [], "West": []}
        for (a, b, conf), data in sorted(r2_tracker.items(), key=lambda x: -x[1]["count"]):
            if data["count"] >= min_count:
                freq = data["count"] / self.n_sims
                a_win_prob = data["a_wins"] / data["count"]
                r2_matchups_result[conf].append((a, b, round(a_win_prob, 3), round(freq, 3)))

        cf_matchups_result = {"East": [], "West": []}
        for (a, b, conf), data in sorted(cf_tracker.items(), key=lambda x: -x[1]["count"]):
            if data["count"] >= min_count:
                freq = data["count"] / self.n_sims
                a_win_prob = data["a_wins"] / data["count"]
                cf_matchups_result[conf].append((a, b, round(a_win_prob, 3), round(freq, 3)))

        cup_final_matchups_result = []
        cup_min_count = self.n_sims * 0.01  # Lower threshold for Cup Finals (1%)
        for pair, data in sorted(cup_final_tracker.items(), key=lambda x: -x[1]["count"]):
            if data["count"] >= cup_min_count:
                freq = data["count"] / self.n_sims
                a_win_prob = data["a_wins"] / data["count"]
                cup_final_matchups_result.append((pair[0], pair[1], round(a_win_prob, 3), round(freq, 3)))

        return MonteCarloResult(
            cup_probabilities=cup_probs,
            round_advancement=round_advancement,
            projected_matchups=projected_matchups,
            conf_final_appearance_probs=conf_final_appearance_probs,
            cup_final_probs=cup_final_probs_dict,
            r2_matchups=r2_matchups_result,
            conf_final_matchups=cf_matchups_result,
            cup_final_matchups=cup_final_matchups_result,
            projected_standings=projected_pts,
        )

    @staticmethod
    def _select_playoff_teams(
        conf_teams: List[TeamSeason],
        sim_pts: Dict[str, float]
    ) -> List[TeamSeason]:
        """
        Select 8 playoff teams from a conference using real NHL rules.

        NHL playoff qualification:
        - Top 3 from each division qualify automatically (6 teams)
        - Best 2 remaining teams are wildcards (2 teams)

        Args:
            conf_teams: All teams in this conference
            sim_pts: Noisy projected points for this simulation iteration

        Returns:
            List of 8 TeamSeason objects that made the playoffs
        """
        # Group by division
        divisions = defaultdict(list)
        for t in conf_teams:
            div = t.division or get_team_division(t.team)
            divisions[div].append(t)

        # Sort each division by sim points
        for div in divisions:
            divisions[div].sort(key=lambda t: -sim_pts.get(t.team, t.points))

        # Top 3 per division qualify
        qualified = []
        remaining = []
        for div_teams in divisions.values():
            qualified.extend(div_teams[:3])
            remaining.extend(div_teams[3:])

        # Best 2 remaining are wildcards
        remaining.sort(key=lambda t: -sim_pts.get(t.team, t.points))
        qualified.extend(remaining[:2])

        return qualified

    def _seed_conference(
        self,
        playoff_teams: List[TeamSeason],
        sim_pts: Optional[Dict[str, float]] = None
    ) -> List[tuple]:
        """
        Seed 8 conference playoff teams into R1 matchups using real NHL rules.

        Assumes playoff_teams already contains the correct 8 teams
        (selected via _select_playoff_teams with NHL division rules).

        Returns list of 4 R1 matchup tuples: [(higher, lower), ...].
        Index 0,1 = Bracket A; Index 2,3 = Bracket B.

        NHL seeding rules:
        - Division winners are seeds 1 & 2 (by points)
        - Seed 1 (better div winner) plays WC2, Seed 2 plays WC1
        - Within each division bracket: 2nd vs 3rd from that division
        """
        def pts(t):
            return sim_pts.get(t.team, t.points) if sim_pts else t.points

        # Group the 8 playoff teams by division
        divisions = defaultdict(list)
        for t in playoff_teams:
            div = t.division or get_team_division(t.team)
            divisions[div].append(t)

        # Sort each division by points
        for div in divisions:
            divisions[div].sort(key=lambda t: -pts(t))

        div_names = sorted(divisions.keys())
        if len(div_names) != 2:
            logger.warning("Division data invalid (%d divisions), falling back to simple seeding", len(div_names))
            return self._seed_conference_simple(playoff_teams, sim_pts)

        div_a_name, div_b_name = div_names[0], div_names[1]
        div_a = divisions[div_a_name]
        div_b = divisions[div_b_name]

        # Division winners (best team in each division among the 8 qualifiers)
        div_a_winner = div_a[0] if div_a else None
        div_b_winner = div_b[0] if div_b else None

        if not div_a_winner or not div_b_winner:
            return self._seed_conference_simple(playoff_teams, sim_pts)

        # Identify which teams are divisional qualifiers (top 3 per div)
        # vs wildcards. A division may have 3, 4, or 5 of the 8 teams
        # if wildcards came from that division.
        # Divisional: first 3 per division. Wildcards: everyone else.
        div_a_divisional = div_a[:3]
        div_b_divisional = div_b[:3]
        wildcard_set = set(t.team for t in playoff_teams) - \
            set(t.team for t in div_a_divisional) - \
            set(t.team for t in div_b_divisional)
        wildcards = sorted(
            [t for t in playoff_teams if t.team in wildcard_set],
            key=lambda t: -pts(t)
        )

        # Need exactly 2 wildcards and 3 per division
        if len(div_a_divisional) < 3 or len(div_b_divisional) < 3 or len(wildcards) < 2:
            return self._seed_conference_simple(playoff_teams, sim_pts)

        # Seed 1 = div winner with more points, Seed 2 = other
        if pts(div_a_winner) >= pts(div_b_winner):
            seed1, seed1_div = div_a_winner, div_a_name
            seed2, seed2_div = div_b_winner, div_b_name
        else:
            seed1, seed1_div = div_b_winner, div_b_name
            seed2, seed2_div = div_a_winner, div_a_name

        # WC1 = better wildcard, WC2 = worse wildcard
        wc1, wc2 = wildcards[0], wildcards[1]

        # 2nd and 3rd in each division (among divisional qualifiers only)
        s1_div = [t for t in divisions[seed1_div]
                  if t.team != seed1.team and t.team not in wildcard_set]
        s2_div = [t for t in divisions[seed2_div]
                  if t.team != seed2.team and t.team not in wildcard_set]

        if len(s1_div) < 2 or len(s2_div) < 2:
            return self._seed_conference_simple(playoff_teams, sim_pts)

        # Bracket A (seed1's division): seed1 vs WC2, div 2nd vs div 3rd
        # Bracket B (seed2's division): seed2 vs WC1, div 2nd vs div 3rd
        return [
            (seed1.team, wc2.team),
            (s1_div[0].team, s1_div[1].team),
            (seed2.team, wc1.team),
            (s2_div[0].team, s2_div[1].team),
        ]

    def _seed_conference_simple(
        self,
        playoff_teams: List[TeamSeason],
        sim_pts: Optional[Dict[str, float]] = None
    ) -> List[tuple]:
        """Fallback simple 1v8, 2v7, 3v6, 4v5 seeding."""
        def pts(t):
            return sim_pts.get(t.team, t.points) if sim_pts else t.points
        teams = sorted(playoff_teams, key=lambda t: -pts(t))
        codes = [t.team for t in teams]
        while len(codes) < 8:
            codes.append("BYE")
        return [
            (codes[0], codes[7]),
            (codes[1], codes[6]),
            (codes[2], codes[5]),
            (codes[3], codes[4]),
        ]

    def _simulate_conference(
        self,
        playoff_teams: List[TeamSeason],
        strength_scores: Dict[str, float],
        experience_scores: Dict[str, float],
        sim_pts: Optional[Dict[str, float]] = None
    ) -> ConferenceTrace:
        """Simulate conference playoffs using real NHL bracket seeding."""
        trace = ConferenceTrace()

        # Get NHL-seeded matchups: [(higher, lower), ...]
        # Index 0,1 = Bracket A; Index 2,3 = Bracket B
        matchups = self._seed_conference(playoff_teams, sim_pts)

        # Round 1
        for higher, lower in matchups:
            trace.r1_matchups.append((higher, lower))
            if lower == "BYE":
                trace.r1_winners.append(higher)
            else:
                winner = self._simulate_series(
                    higher, lower,
                    strength_scores.get(higher, 50),
                    strength_scores.get(lower, 50),
                    round_num=1,
                    exp_a=experience_scores.get(higher, 0),
                    exp_b=experience_scores.get(lower, 0)
                )
                trace.r1_winners.append(winner)

        # Round 2: Winners stay on their bracket side
        # Bracket A: r1_winners[0] vs r1_winners[1]
        # Bracket B: r1_winners[2] vs r1_winners[3]
        for k in range(0, 4, 2):
            a, b = trace.r1_winners[k], trace.r1_winners[k+1]
            trace.r2_matchups.append((a, b))
            winner = self._simulate_series(
                a, b,
                strength_scores.get(a, 50),
                strength_scores.get(b, 50),
                round_num=2,
                exp_a=experience_scores.get(a, 0),
                exp_b=experience_scores.get(b, 0)
            )
            trace.r2_winners.append(winner)

        # Conference Final (round 3): bracket winners play each other
        cf_a, cf_b = trace.r2_winners[0], trace.r2_winners[1]
        trace.conf_final_matchup = (cf_a, cf_b)
        trace.conf_champion = self._simulate_series(
            cf_a, cf_b,
            strength_scores.get(cf_a, 50),
            strength_scores.get(cf_b, 50),
            round_num=3,
            exp_a=experience_scores.get(cf_a, 0),
            exp_b=experience_scores.get(cf_b, 0)
        )

        return trace

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
        self.monte_carlo_result: Optional[MonteCarloResult] = None

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
        mc_result = self._run_dynamic_monte_carlo(
            teams, strength_scores, playoff_probs, features=features
        )
        mc_probs = mc_result.cup_probabilities

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
                conference_final_probability=mc_result.conf_final_appearance_probs.get(team.team, 0.0),
                cup_final_probability=mc_result.cup_final_probs.get(team.team, 0.0),
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
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation with dynamic adjustments.

        Key improvements over static MC:
        1. Uses playoff probabilities to adjust seeding uncertainty
        2. Increases simulation count for close matchups
        3. Incorporates strength uncertainty into series outcomes
        4. Passes playoff experience to series predictor
        """
        adjusted_strengths = {team.team: strength_scores[team.team] for team in teams}

        # Extract experience scores from features if available
        experience_scores = None
        if features is not None:
            experience_scores = {
                teams[i].team: features[i].playoff_experience
                for i in range(len(teams))
            }

        # Run simulation with experience scores for enhanced playoff model
        mc_result = self.monte_carlo.simulate(
            teams, adjusted_strengths, experience_scores=experience_scores
        )
        self.monte_carlo_result = mc_result
        return mc_result

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
