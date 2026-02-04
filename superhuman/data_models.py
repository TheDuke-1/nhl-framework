"""
Superhuman NHL Prediction System - Data Models
===============================================
Dataclasses for structured data representation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import numpy as np


@dataclass
class TeamSeason:
    """Complete team data for a single season."""

    # Identifiers
    team: str
    season: int  # End year (e.g., 2024 for 2023-24 season)
    division: str = ""  # e.g., "Atlantic", "Metropolitan", "Central", "Pacific"

    # Basic stats
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    ot_losses: int = 0
    points: int = 0

    # Goal stats
    goals_for: int = 0
    goals_against: int = 0

    # Advanced possession (5v5)
    cf_pct: float = 50.0
    ff_pct: float = 50.0
    sf_pct: float = 50.0

    # Expected goals (5v5)
    xgf: float = 0.0
    xga: float = 0.0
    xgf_pct: float = 50.0

    # High-danger chances
    hdcf: float = 0.0
    hdca: float = 0.0
    hdcf_pct: float = 50.0

    # Goaltending
    gsax: float = 0.0
    save_pct: float = 0.900
    hd_save_pct: float = 0.820

    # Special teams
    pp_pct: float = 20.0
    pk_pct: float = 80.0

    # Home/Away splits (for road_performance calculation)
    home_wins: int = 0
    home_losses: int = 0
    home_ot_losses: int = 0
    away_wins: int = 0
    away_losses: int = 0
    away_ot_losses: int = 0

    # Derived metrics
    expected_goals_diff: float = 0.0
    recent_form: float = 0.0  # Last 10/20 games performance
    star_ppg: float = 0.0     # Top player points per game

    # Close games
    one_goal_wins: int = 0
    one_goal_losses: int = 0
    ot_wins: int = 0
    comeback_wins: int = 0
    blown_leads: int = 0

    # Roster
    top_scorer_points: int = 0
    top_scorer_ppg: float = 0.0
    players_20_goals: int = 0
    players_40_points: int = 0

    # Sustainability
    pdo: float = 100.0
    shooting_pct: float = 10.0

    # Playoff results
    made_playoffs: bool = False
    playoff_seed: int = 0
    playoff_rounds_won: int = 0
    won_cup: bool = False

    @property
    def goal_differential(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def gd_per_game(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.goal_differential / self.games_played

    @property
    def points_pct(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.points / (self.games_played * 2) * 100

    @property
    def xgd(self) -> float:
        return self.xgf - self.xga

    @property
    def xgd_per_game(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.xgd / self.games_played

    @property
    def home_games(self) -> int:
        return self.home_wins + self.home_losses + self.home_ot_losses

    @property
    def away_games(self) -> int:
        return self.away_wins + self.away_losses + self.away_ot_losses

    @property
    def home_win_pct(self) -> float:
        if self.home_games == 0:
            return 0.0
        return self.home_wins / self.home_games * 100

    @property
    def away_win_pct(self) -> float:
        if self.away_games == 0:
            return 0.0
        return self.away_wins / self.away_games * 100

    @property
    def road_differential(self) -> float:
        """Difference between home and away win rate."""
        return self.home_win_pct - self.away_win_pct

    @property
    def clutch_score(self) -> float:
        """Net close-game performance."""
        return (self.one_goal_wins + self.ot_wins + self.comeback_wins
                - self.one_goal_losses - self.blown_leads)

    @property
    def playoff_success_score(self) -> float:
        """Continuous measure of playoff success for regression."""
        if not self.made_playoffs:
            return 0.0

        scores = {
            0: 0.10,  # Lost R1
            1: 0.25,  # Won R1
            2: 0.45,  # Conference Finals
            3: 0.70,  # Cup Finals
            4: 1.00   # Won Cup
        }
        return scores.get(self.playoff_rounds_won, 0.0)


@dataclass
class FeatureVector:
    """Processed features ready for model input."""

    team: str
    season: int

    # Core features (will be populated after PCA)
    goal_differential_rate: float = 0.0
    territorial_dominance: float = 0.0  # PCA component 1
    shot_quality_premium: float = 0.0   # PCA component 2
    goaltending_quality: float = 0.0
    special_teams_composite: float = 0.0
    road_performance: float = 0.0
    recent_form: float = 0.0
    roster_depth: float = 0.0
    star_power: float = 0.0
    clutch_performance: float = 0.0
    sustainability: float = 0.0
    vegas_cup_signal: float = 0.0  # Vegas market Cup probability
    playoff_experience: float = 0.0  # Recent playoff history
    dynasty_score: float = 0.0  # Recent championship success

    # Target variables
    made_playoffs: bool = False
    playoff_success: float = 0.0
    won_cup: bool = False

    def to_array(self) -> np.ndarray:
        """Convert features to numpy array for model input."""
        return np.array([
            self.goal_differential_rate,
            self.territorial_dominance,
            self.shot_quality_premium,
            self.goaltending_quality,
            self.special_teams_composite,
            self.road_performance,
            self.recent_form,
            self.roster_depth,
            self.star_power,
            self.clutch_performance,
            self.sustainability,
            self.vegas_cup_signal,
            self.playoff_experience,
            self.dynasty_score
        ])

    @staticmethod
    def feature_names() -> List[str]:
        """Return ordered feature names."""
        return [
            "goal_differential_rate",
            "territorial_dominance",
            "shot_quality_premium",
            "goaltending_quality",
            "special_teams_composite",
            "road_performance",
            "recent_form",
            "roster_depth",
            "star_power",
            "clutch_performance",
            "sustainability",
            "vegas_cup_signal",
            "playoff_experience",
            "dynasty_score"
        ]


@dataclass
class ConferenceTrace:
    """Trace of a single conference playoff simulation."""
    r1_winners: List[str] = field(default_factory=list)
    r2_winners: List[str] = field(default_factory=list)
    conf_champion: str = ""
    r1_matchups: List[tuple] = field(default_factory=list)  # [(higher, lower), ...]
    r2_matchups: List[tuple] = field(default_factory=list)
    conf_final_matchup: tuple = ()  # (teamA, teamB)


@dataclass
class MonteCarloResult:
    """Full results from Monte Carlo simulation."""

    # Existing: Cup win probabilities per team
    cup_probabilities: Dict[str, float] = field(default_factory=dict)

    # Round advancement: team -> {1: prob, 2: prob, 3: prob (conf final), 4: prob (cup final), "cup": prob}
    round_advancement: Dict[str, Dict] = field(default_factory=dict)

    # Projected R1 matchups per conference: conf -> [(higher, lower, higher_win_prob)]
    projected_matchups: Dict[str, List[tuple]] = field(default_factory=dict)

    # Conference final appearance probabilities (reached conf final, i.e. won R2)
    conf_final_appearance_probs: Dict[str, float] = field(default_factory=dict)

    # Cup Final appearance probabilities
    cup_final_probs: Dict[str, float] = field(default_factory=dict)

    # R2 matchup tracking per bracket slot: {conf: [[slot0_matchups], [slot1_matchups]]}
    r2_matchups: Dict[str, List[tuple]] = field(default_factory=dict)
    conf_final_matchups: Dict[str, List[tuple]] = field(default_factory=dict)
    cup_final_matchups: List[tuple] = field(default_factory=list)

    # Pace-projected standings: team -> projected end-of-season points
    projected_standings: Dict[str, float] = field(default_factory=dict)


@dataclass
class PredictionResult:
    """Model prediction output."""

    team: str
    season: int

    # Strength score
    composite_strength: float = 0.0
    strength_rank: int = 0

    # Probabilities
    playoff_probability: float = 0.0
    conference_final_probability: float = 0.0
    cup_final_probability: float = 0.0
    cup_win_probability: float = 0.0

    # Confidence intervals (90%)
    cup_prob_lower: float = 0.0
    cup_prob_upper: float = 0.0

    # Tier classification
    tier: str = "Unknown"  # Elite, Contender, Bubble, Longshot

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "team": self.team,
            "season": self.season,
            "composite_strength": round(self.composite_strength, 2),
            "strength_rank": self.strength_rank,
            "playoff_probability": round(self.playoff_probability, 3),
            "conference_final_probability": round(self.conference_final_probability, 3),
            "cup_final_probability": round(self.cup_final_probability, 3),
            "cup_win_probability": round(self.cup_win_probability, 3),
            "cup_prob_ci": [round(self.cup_prob_lower, 3), round(self.cup_prob_upper, 3)],
            "tier": self.tier
        }
