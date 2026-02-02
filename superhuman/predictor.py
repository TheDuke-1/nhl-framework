#!/usr/bin/env python3
"""
Superhuman NHL Prediction System - Main Predictor
==================================================
Production-ready prediction interface.

Usage:
    python -m superhuman.predictor              # Full predictions
    python -m superhuman.predictor --team COL   # Single team detail
    python -m superhuman.predictor --output results.json
"""

import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from .data_loader import load_current_season_data, load_training_data
from .models import EnsemblePredictor
from .data_models import PredictionResult
from .config import CURRENT_SEASON

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class SuperhumanPredictor:
    """
    Main prediction interface for NHL playoff/Cup probability.

    Combines all components:
    - Data loading
    - Feature engineering
    - Ensemble prediction
    - Output formatting
    """

    def __init__(self):
        self.ensemble = EnsemblePredictor()
        self.is_trained = False
        self.results: List[PredictionResult] = []
        self.feature_weights: Dict[str, float] = {}

    def train(self) -> 'SuperhumanPredictor':
        """Train model on historical data."""
        logger.info("Loading training data...")
        training_data = load_training_data()

        logger.info(f"Training ensemble on {len(training_data)} samples...")
        self.ensemble.fit(training_data)

        self.feature_weights = self.ensemble.get_feature_weights()
        self.is_trained = True

        logger.info("Training complete")
        return self

    def predict(self) -> List[PredictionResult]:
        """Generate predictions for current season."""
        if not self.is_trained:
            self.train()

        logger.info("Loading current season data...")
        current_data = load_current_season_data()

        logger.info("Generating predictions...")
        self.results = self.ensemble.predict(current_data)

        # Sort by Cup probability
        self.results.sort(key=lambda r: -r.cup_win_probability)

        return self.results

    def get_team_prediction(self, team: str) -> Optional[PredictionResult]:
        """Get prediction for specific team."""
        if not self.results:
            self.predict()

        team = team.upper()
        return next((r for r in self.results if r.team == team), None)

    def print_predictions(self, top_n: int = 32) -> None:
        """Print formatted prediction table."""
        if not self.results:
            self.predict()

        print()
        print("=" * 80)
        print("SUPERHUMAN NHL PREDICTION SYSTEM")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Season: {CURRENT_SEASON}")
        print()

        # Feature weights
        print("LEARNED FEATURE WEIGHTS:")
        sorted_weights = sorted(
            self.feature_weights.items(),
            key=lambda x: -x[1]
        )
        for name, weight in sorted_weights[:5]:
            print(f"  {name}: {weight:.1f}%")
        print()

        # Predictions table
        header = f"{'Rank':<5} {'Team':<5} {'Tier':<12} {'Strength':<10} {'Playoff%':<10} {'Cup%':<12}"
        print(header)
        print("-" * 70)

        for i, r in enumerate(self.results[:top_n], 1):
            cup_str = f"{r.cup_win_probability*100:.1f}%"
            if r.cup_prob_lower and r.cup_prob_upper:
                cup_str += f" ({r.cup_prob_lower*100:.1f}-{r.cup_prob_upper*100:.1f})"

            print(
                f"{i:<5} {r.team:<5} {r.tier:<12} "
                f"{r.composite_strength:<10.1f} "
                f"{r.playoff_probability*100:>6.1f}%   "
                f"{cup_str:<12}"
            )

        print()

        # Tier summary
        print("TIER BREAKDOWN:")
        tiers = {'Elite': [], 'Contender': [], 'Bubble': [], 'Longshot': []}
        for r in self.results:
            tiers[r.tier].append(r.team)

        for tier, teams in tiers.items():
            print(f"  {tier}: {', '.join(teams)}")

        print()

        # Cup favorites
        print("TOP 5 CUP FAVORITES:")
        for i, r in enumerate(self.results[:5], 1):
            print(f"  {i}. {r.team}: {r.cup_win_probability*100:.1f}%")

    def print_team_detail(self, team: str) -> None:
        """Print detailed prediction for single team."""
        result = self.get_team_prediction(team)

        if not result:
            print(f"Team '{team}' not found")
            return

        print()
        print(f"{'='*50}")
        print(f"{team} - DETAILED PREDICTION")
        print(f"{'='*50}")
        print()
        print(f"Tier:              {result.tier}")
        print(f"Strength Score:    {result.composite_strength:.1f}")
        print(f"Strength Rank:     #{result.strength_rank}")
        print()
        print(f"Playoff Probability: {result.playoff_probability*100:.1f}%")
        print(f"Cup Win Probability: {result.cup_win_probability*100:.2f}%")
        print(f"  90% CI: {result.cup_prob_lower*100:.2f}% - {result.cup_prob_upper*100:.2f}%")

    def to_json(self) -> Dict:
        """Export predictions as JSON-serializable dict."""
        if not self.results:
            self.predict()

        return {
            'generated': datetime.now().isoformat(),
            'season': CURRENT_SEASON,
            'feature_weights': self.feature_weights,
            'predictions': [
                {
                    'rank': i + 1,
                    'team': r.team,
                    'tier': r.tier,
                    'composite_strength': round(r.composite_strength, 2),
                    'playoff_probability': round(r.playoff_probability, 4),
                    'cup_win_probability': round(r.cup_win_probability, 4),
                    'cup_prob_ci': [
                        round(r.cup_prob_lower, 4),
                        round(r.cup_prob_upper, 4)
                    ]
                }
                for i, r in enumerate(self.results)
            ]
        }

    def save_json(self, filepath: str) -> None:
        """Save predictions to JSON file."""
        data = self.to_json()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved predictions to {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Superhuman NHL Prediction System"
    )
    parser.add_argument(
        '--team',
        help="Show detailed prediction for specific team"
    )
    parser.add_argument(
        '--output', '-o',
        help="Save predictions to JSON file"
    )
    parser.add_argument(
        '--top', '-n',
        type=int,
        default=32,
        help="Number of teams to show (default: 32)"
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help="Suppress logging output"
    )

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    predictor = SuperhumanPredictor()
    predictor.predict()

    if args.team:
        predictor.print_team_detail(args.team)
    else:
        predictor.print_predictions(top_n=args.top)

    if args.output:
        predictor.save_json(args.output)


if __name__ == "__main__":
    main()
