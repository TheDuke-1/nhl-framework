"""
Superhuman NHL Prediction System - Feature Engineering
=======================================================
Transform raw metrics into orthogonal, predictive features.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from .data_models import TeamSeason, FeatureVector
from .config import TIME_DECAY_HALF_LIFE
from .player_data_loader import (
    get_team_player_stats,
    calculate_star_power_from_players,
    calculate_roster_depth_from_players,
    TeamPlayerStats
)
from .recent_form_loader import calculate_recent_form_feature
from .betting_odds_loader import get_team_vegas_odds
from .clutch_data_loader import calculate_clutch_feature
from .playoff_experience_loader import (
    calculate_playoff_experience_feature,
    calculate_dynasty_feature
)


class FeatureEngineer:
    """
    Transform raw team stats into model-ready features.

    Key transformations:
    1. PCA on correlated possession metrics
    2. Z-score normalization
    3. Composite feature creation
    """

    def __init__(self):
        self.possession_pca = None
        self.possession_scaler = StandardScaler()
        self.feature_scaler = StandardScaler()
        self.is_fitted = False

    def fit(self, team_seasons: List[TeamSeason]) -> 'FeatureEngineer':
        """
        Fit scalers and PCA on training data.

        Must be called before transform().
        """
        # Extract possession metrics for PCA
        possession_matrix = self._extract_possession_matrix(team_seasons)

        # Fit PCA on possession metrics
        self.possession_scaler.fit(possession_matrix)
        possession_scaled = self.possession_scaler.transform(possession_matrix)

        self.possession_pca = PCA(n_components=2)
        self.possession_pca.fit(possession_scaled)

        # Fit feature scaler on all features
        all_features = self._create_raw_features(team_seasons)
        feature_matrix = np.array([f.to_array() for f in all_features])
        self.feature_scaler.fit(feature_matrix)

        self.is_fitted = True
        return self

    def transform(self, team_seasons: List[TeamSeason]) -> List[FeatureVector]:
        """
        Transform team seasons into feature vectors.
        """
        if not self.is_fitted:
            raise RuntimeError("FeatureEngineer must be fit before transform")

        # Get PCA components for possession metrics
        possession_matrix = self._extract_possession_matrix(team_seasons)
        possession_scaled = self.possession_scaler.transform(possession_matrix)
        possession_pca = self.possession_pca.transform(possession_scaled)

        # Create feature vectors
        features = []
        for i, ts in enumerate(team_seasons):
            fv = self._create_feature_vector(
                ts,
                territorial_dominance=possession_pca[i, 0],
                shot_quality_premium=possession_pca[i, 1]
            )
            features.append(fv)

        return features

    def fit_transform(self, team_seasons: List[TeamSeason]) -> List[FeatureVector]:
        """Fit and transform in one step."""
        self.fit(team_seasons)
        return self.transform(team_seasons)

    def _extract_possession_matrix(self, team_seasons: List[TeamSeason]) -> np.ndarray:
        """Extract correlated possession metrics for PCA."""
        matrix = []
        for ts in team_seasons:
            row = [
                ts.hdcf_pct,
                ts.cf_pct,
                ts.xgf_pct,
                ts.xgd_per_game * 10,  # Scale to similar range
            ]
            matrix.append(row)
        return np.array(matrix)

    def _create_raw_features(self, team_seasons: List[TeamSeason]) -> List[FeatureVector]:
        """Create feature vectors without PCA (for fitting scaler)."""
        features = []
        for ts in team_seasons:
            fv = self._create_feature_vector(ts, 0.0, 0.0)
            features.append(fv)
        return features

    def _create_feature_vector(
        self,
        ts: TeamSeason,
        territorial_dominance: float,
        shot_quality_premium: float
    ) -> FeatureVector:
        """Create a single feature vector from team season."""

        return FeatureVector(
            team=ts.team,
            season=ts.season,

            # Core features
            goal_differential_rate=ts.gd_per_game,
            territorial_dominance=territorial_dominance,
            shot_quality_premium=shot_quality_premium,
            goaltending_quality=self._calculate_goaltending(ts),
            special_teams_composite=self._calculate_special_teams(ts),
            road_performance=self._calculate_road_performance(ts),
            recent_form=calculate_recent_form_feature(ts.team, ts.season),
            roster_depth=self._calculate_depth(ts),
            star_power=self._calculate_star_power(ts),
            clutch_performance=self._calculate_clutch(ts),
            sustainability=self._calculate_sustainability(ts),
            vegas_cup_signal=self._calculate_vegas_signal(ts),
            playoff_experience=calculate_playoff_experience_feature(ts.team, ts.season),
            dynasty_score=calculate_dynasty_feature(ts.team, ts.season),

            # Targets
            made_playoffs=ts.made_playoffs,
            playoff_success=ts.playoff_success_score,
            won_cup=ts.won_cup
        )

    def _calculate_vegas_signal(self, ts: TeamSeason) -> float:
        """
        Vegas market signal - uses pre-season Cup odds.

        Normalizes implied probability to roughly -1 to +1 range.
        - Top contenders (~15% implied): +1.5
        - Average teams (~3% implied): 0
        - Longshots (<1% implied): -1
        """
        odds = get_team_vegas_odds(ts.team, ts.season)
        if odds is None:
            return 0.0

        # Normalize: average team has ~3% Cup probability (1/32)
        # Scale so that 15% = +1.5, 3% = 0, 0.5% = -1
        implied_prob = odds.cup_implied_prob
        return (implied_prob - 0.03) * 15  # Roughly -1 to +2 range

    def _calculate_goaltending(self, ts: TeamSeason) -> float:
        """Composite goaltending score."""
        # GSAx is the primary measure
        # Normalize to roughly -3 to +3 range
        return ts.gsax / 10.0

    def _calculate_special_teams(self, ts: TeamSeason) -> float:
        """Composite special teams score."""
        # Weight PK slightly higher than PP
        pp_normalized = (ts.pp_pct - 20) / 5  # Center at 20%, scale by 5%
        pk_normalized = (ts.pk_pct - 80) / 5  # Center at 80%, scale by 5%
        return 0.4 * pp_normalized + 0.6 * pk_normalized

    def _calculate_road_performance(self, ts: TeamSeason) -> float:
        """Road performance - how well team plays away from home."""
        if ts.away_games == 0:
            return 0.0

        # Away win percentage (normalized to -1 to +1 range)
        away_win_pct = ts.away_win_pct / 100  # 0-1 scale

        # Compare to home performance (positive = better on road)
        home_win_pct = ts.home_win_pct / 100

        # Road differential: how much worse/better on the road
        # Most teams are worse on road, so 0 = average, positive = road warrior
        road_adj = away_win_pct - (home_win_pct * 0.85)  # Expect 85% of home performance

        return road_adj * 2  # Scale to roughly -1 to +1

    def _calculate_depth(self, ts: TeamSeason) -> float:
        """
        Roster depth score - uses real player data when available.

        Depth measures how many quality scorers a team has beyond
        their top stars. Deep teams have multiple 20+ goal scorers.
        """
        # Try to get real player data
        player_stats = get_team_player_stats(ts.team, ts.season)

        if player_stats is not None:
            return calculate_roster_depth_from_players(player_stats)

        # If we have player data in TeamSeason, use it
        if ts.players_20_goals > 0:
            depth_score = 0
            for i in range(min(ts.players_20_goals, 6)):
                depth_score += 1.5 - (i * 0.2)
            return depth_score / 5

        # Proxy: use goals_for relative to shooting%, suggests balanced attack
        if ts.games_played > 0:
            gf_per_game = ts.goals_for / ts.games_played
            # Higher GF with normal shooting = good depth
            # Normalize: 3.0 GF/game = average, 3.5+ = deep team
            return (gf_per_game - 2.5) / 1.5

        return 0.0

    def _calculate_star_power(self, ts: TeamSeason) -> float:
        """
        Top player quality - uses real player data when available.

        Star power measures the quality of a team's best players.
        Elite stars (1.2+ PPG) carry teams in the playoffs.
        """
        # Try to get real player data
        player_stats = get_team_player_stats(ts.team, ts.season)

        if player_stats is not None:
            return calculate_star_power_from_players(player_stats)

        # Fallback: If we have top scorer data in TeamSeason
        if hasattr(ts, 'star_ppg') and ts.star_ppg > 0:
            return (ts.star_ppg - 0.8) * 2

        if hasattr(ts, 'top_scorer_ppg') and ts.top_scorer_ppg > 0:
            return (ts.top_scorer_ppg - 0.8) * 2

        # Proxy: teams with high goal differential likely have stars
        # Elite teams (top 5 in goals) typically have star players
        if ts.games_played > 0:
            gf_per_game = ts.goals_for / ts.games_played
            gd_per_game = ts.gd_per_game
            # Combine offensive output and differential
            return (gf_per_game - 3.0) + (gd_per_game * 0.5)

        return 0.0

    def _calculate_clutch(self, ts: TeamSeason) -> float:
        """
        Clutch performance score - uses real OT/SO and one-goal game data.

        Composite of:
        - One-goal game win rate (35%)
        - OT/SO win rate (35%)
        - Comeback ratio (30%)

        Returns value typically in range -1 to +1.
        """
        return calculate_clutch_feature(ts.team, ts.season)

    def _calculate_sustainability(self, ts: TeamSeason) -> float:
        """
        Inverse sustainability indicator.
        Higher PDO = more regression risk = lower score.
        """
        # PDO of 100 is neutral, deviation is regression risk
        pdo_deviation = abs(ts.pdo - 100)
        return -pdo_deviation / 5  # Negative because high PDO = regression risk


def create_feature_matrix(
    features: List[FeatureVector],
    include_targets: bool = False
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Convert feature vectors to numpy arrays for model training.

    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Target array (playoff_success)
        feature_names: List of feature names
    """
    X = np.array([f.to_array() for f in features])
    y = np.array([f.playoff_success for f in features])
    names = FeatureVector.feature_names()

    return X, y, names


def get_feature_correlations(features: List[FeatureVector]) -> Dict[str, Dict[str, float]]:
    """Calculate correlation matrix between features."""
    X, _, names = create_feature_matrix(features)

    correlations = {}
    for i, name_i in enumerate(names):
        correlations[name_i] = {}
        for j, name_j in enumerate(names):
            corr = np.corrcoef(X[:, i], X[:, j])[0, 1]
            correlations[name_i][name_j] = round(corr, 3)

    return correlations
