"""
Playoff Series Prediction Model
================================
A dedicated model for predicting playoff series outcomes.

Unlike regular season predictions, this model focuses on:
- Head-to-head matchup dynamics
- Playoff experience
- Home ice advantage
- Round-specific patterns (later rounds = more parity)
"""

import csv
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .config import RANDOM_SEED

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "historical"


@dataclass
class SeriesMatchup:
    """A playoff series matchup between two teams."""
    year: int
    round: int
    higher_seed: str
    lower_seed: str
    winner: Optional[str] = None
    games_played: Optional[int] = None

    @property
    def was_upset(self) -> bool:
        """Did the lower seed win?"""
        return self.winner == self.lower_seed


@dataclass
class SeriesFeatures:
    """Features for predicting a playoff series."""
    strength_diff: float       # Higher seed strength - lower seed strength
    seed_diff: int             # Seed number difference (1-8 vs 1-8)
    round_number: int          # 1-4 (later rounds = more parity)
    higher_seed_exp: float     # Higher seed playoff experience
    lower_seed_exp: float      # Lower seed playoff experience
    higher_seed_dynasty: float # Higher seed recent cups
    lower_seed_dynasty: float  # Lower seed recent cups

    def to_array(self) -> np.ndarray:
        return np.array([
            self.strength_diff,
            self.seed_diff,
            self.round_number,
            self.higher_seed_exp - self.lower_seed_exp,  # Experience difference
            self.higher_seed_dynasty - self.lower_seed_dynasty,  # Dynasty difference
        ])


class PlayoffSeriesPredictor:
    """
    Predicts playoff series outcomes using matchup-specific features.

    Key insight: Playoff series are different from regular season games.
    - Home ice matters less (2-2-1-1-1 format)
    - Experience and "playoff DNA" matter more
    - Later rounds show more parity (better teams remaining)
    """

    def __init__(self):
        self.model = LogisticRegression(
            C=1.0,
            penalty='l2',
            solver='lbfgs',
            max_iter=1000,
            random_state=RANDOM_SEED
        )
        self.scaler = StandardScaler()
        self.is_fitted = False

        # Empirical round adjustments (from historical data)
        # Later rounds have more upsets
        self.round_parity_factor = {
            1: 0.0,    # Round 1: seeding matters most
            2: 0.05,   # Round 2: slightly more parity
            3: 0.10,   # Conf Finals: near 50-50
            4: 0.08,   # Cup Finals: slight parity
        }

        # Base win probability for higher seed by round
        self.base_win_prob = {
            1: 0.59,   # Round 1: higher seed wins 59%
            2: 0.53,   # Round 2: 53%
            3: 0.50,   # Conf Finals: 50%
            4: 0.53,   # Cup Finals: 53%
        }

    def load_historical_series(self) -> List[Tuple[SeriesMatchup, int]]:
        """Load historical series with outcomes."""
        filepath = DATA_DIR / "playoff_series_all.csv"

        if not filepath.exists():
            logger.warning(f"Series data not found: {filepath}")
            return []

        series_list = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                matchup = SeriesMatchup(
                    year=int(row['year']),
                    round=int(row['round']),
                    higher_seed=row['higher_seed'],
                    lower_seed=row['lower_seed'],
                    winner=row['winner'],
                    games_played=int(row['games_played'])
                )
                # Outcome: 1 if higher seed won, 0 if upset
                outcome = 0 if matchup.was_upset else 1
                series_list.append((matchup, outcome))

        logger.info(f"Loaded {len(series_list)} historical series")
        return series_list

    def fit(
        self,
        team_strengths: Dict[int, Dict[str, float]] = None,
        team_experience: Dict[int, Dict[str, float]] = None
    ) -> 'PlayoffSeriesPredictor':
        """
        Fit the model on historical series data.

        Args:
            team_strengths: {year: {team: strength_score}}
            team_experience: {year: {team: experience_score}}
        """
        series_data = self.load_historical_series()

        if not series_data:
            logger.warning("No series data to train on")
            return self

        # Create features
        X = []
        y = []

        for matchup, outcome in series_data:
            # Get team strengths (default to 50 if not provided)
            if team_strengths and matchup.year in team_strengths:
                str_high = team_strengths[matchup.year].get(matchup.higher_seed, 50)
                str_low = team_strengths[matchup.year].get(matchup.lower_seed, 50)
            else:
                str_high = 55  # Higher seed assumed slightly stronger
                str_low = 50

            # Get experience (default to 0 if not provided)
            if team_experience and matchup.year in team_experience:
                exp_high = team_experience[matchup.year].get(matchup.higher_seed, 0)
                exp_low = team_experience[matchup.year].get(matchup.lower_seed, 0)
            else:
                exp_high = 0.5  # Assume some experience for playoff teams
                exp_low = 0.3

            features = SeriesFeatures(
                strength_diff=str_high - str_low,
                seed_diff=4,  # Approximate average seed diff
                round_number=matchup.round,
                higher_seed_exp=exp_high,
                lower_seed_exp=exp_low,
                higher_seed_dynasty=0,
                lower_seed_dynasty=0
            )

            X.append(features.to_array())
            y.append(outcome)

        X = np.array(X)
        y = np.array(y)

        # Scale and fit
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True

        # Log learned weights
        logger.info(f"Playoff series model fitted on {len(y)} series")
        logger.info(f"Feature importance: {self.model.coef_[0]}")

        return self

    def predict_series_probability(
        self,
        higher_seed: str,
        lower_seed: str,
        round_num: int,
        strength_diff: float = 5.0,
        experience_diff: float = 0.0,
        dynasty_diff: float = 0.0
    ) -> float:
        """
        Predict probability that higher seed wins the series.

        Args:
            higher_seed: Team abbreviation of higher seed
            lower_seed: Team abbreviation of lower seed
            round_num: Playoff round (1-4)
            strength_diff: Composite strength difference
            experience_diff: Playoff experience difference
            dynasty_diff: Dynasty/recent success difference

        Returns:
            Probability (0-1) that higher seed wins
        """
        if not self.is_fitted:
            # Fall back to empirical base rates
            return self.base_win_prob.get(round_num, 0.55)

        features = SeriesFeatures(
            strength_diff=strength_diff,
            seed_diff=4,  # Average
            round_number=round_num,
            higher_seed_exp=experience_diff / 2 + 0.5,
            lower_seed_exp=-experience_diff / 2 + 0.5,
            higher_seed_dynasty=dynasty_diff / 2,
            lower_seed_dynasty=-dynasty_diff / 2
        )

        X = features.to_array().reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        prob = self.model.predict_proba(X_scaled)[0, 1]

        # Apply round-specific parity adjustment
        parity = self.round_parity_factor.get(round_num, 0)
        adjusted_prob = prob * (1 - parity) + 0.5 * parity

        # Clip to reasonable bounds
        return np.clip(adjusted_prob, 0.25, 0.75)

    def get_round_upset_rates(self) -> Dict[int, float]:
        """Get empirical upset rates by round."""
        series_data = self.load_historical_series()

        rates = {}
        for rnd in [1, 2, 3, 4]:
            rnd_series = [s for s, _ in series_data if s.round == rnd]
            if rnd_series:
                upsets = sum(1 for s in rnd_series if s.was_upset)
                rates[rnd] = upsets / len(rnd_series)

        return rates


class EnhancedMonteCarloSimulator:
    """
    Monte Carlo simulator that uses the playoff series model.

    Key improvements over basic MC:
    - Uses trained series prediction model
    - Accounts for round-specific parity
    - Incorporates playoff experience
    """

    def __init__(
        self,
        series_predictor: PlayoffSeriesPredictor,
        n_simulations: int = 10000
    ):
        self.series_predictor = series_predictor
        self.n_sims = n_simulations

    def simulate_series(
        self,
        team_a: str,
        team_b: str,
        strength_a: float,
        strength_b: float,
        round_num: int,
        experience_a: float = 0,
        experience_b: float = 0
    ) -> str:
        """Simulate a single playoff series."""
        # Determine higher/lower seed by strength
        if strength_a >= strength_b:
            higher, lower = team_a, team_b
            str_diff = strength_a - strength_b
            exp_diff = experience_a - experience_b
        else:
            higher, lower = team_b, team_a
            str_diff = strength_b - strength_a
            exp_diff = experience_b - experience_a

        # Get win probability from series model
        prob_higher_wins = self.series_predictor.predict_series_probability(
            higher_seed=higher,
            lower_seed=lower,
            round_num=round_num,
            strength_diff=str_diff,
            experience_diff=exp_diff
        )

        # Simulate series outcome
        if np.random.random() < prob_higher_wins:
            return higher
        else:
            return lower

    def simulate_bracket(
        self,
        playoff_teams: List[Tuple[str, float, float]],  # (team, strength, experience)
        conference: str
    ) -> str:
        """
        Simulate a conference playoff bracket.

        Args:
            playoff_teams: List of (team, strength, experience) sorted by seed
            conference: 'East' or 'West'

        Returns:
            Conference champion
        """
        if len(playoff_teams) < 8:
            # Pad with weak teams if needed
            while len(playoff_teams) < 8:
                playoff_teams.append(('BYE', 0, 0))

        # Round 1: 1v8, 2v7, 3v6, 4v5
        matchups = [(0, 7), (1, 6), (2, 5), (3, 4)]
        r1_winners = []

        for i, j in matchups:
            if playoff_teams[j][0] == 'BYE':
                r1_winners.append(playoff_teams[i])
            else:
                winner = self.simulate_series(
                    playoff_teams[i][0], playoff_teams[j][0],
                    playoff_teams[i][1], playoff_teams[j][1],
                    round_num=1,
                    experience_a=playoff_teams[i][2],
                    experience_b=playoff_teams[j][2]
                )
                winner_data = playoff_teams[i] if winner == playoff_teams[i][0] else playoff_teams[j]
                r1_winners.append(winner_data)

        # Round 2: 1/8 winner vs 4/5 winner, 2/7 winner vs 3/6 winner
        r2_matchups = [(0, 3), (1, 2)]
        r2_winners = []

        for i, j in r2_matchups:
            winner = self.simulate_series(
                r1_winners[i][0], r1_winners[j][0],
                r1_winners[i][1], r1_winners[j][1],
                round_num=2,
                experience_a=r1_winners[i][2],
                experience_b=r1_winners[j][2]
            )
            winner_data = r1_winners[i] if winner == r1_winners[i][0] else r1_winners[j]
            r2_winners.append(winner_data)

        # Conference Finals
        conf_champ = self.simulate_series(
            r2_winners[0][0], r2_winners[1][0],
            r2_winners[0][1], r2_winners[1][1],
            round_num=3,
            experience_a=r2_winners[0][2],
            experience_b=r2_winners[1][2]
        )

        return conf_champ


# Module-level predictor instance
_series_predictor: Optional[PlayoffSeriesPredictor] = None


def get_series_predictor() -> PlayoffSeriesPredictor:
    """Get or create the series predictor singleton."""
    global _series_predictor
    if _series_predictor is None:
        _series_predictor = PlayoffSeriesPredictor()
        _series_predictor.fit()
    return _series_predictor
