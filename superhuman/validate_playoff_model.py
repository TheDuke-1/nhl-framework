"""
Validation Script for Step 4: Playoff Series Model
===================================================
Compares results with and without the enhanced playoff series model.
"""

import sys
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from superhuman.models import EnsemblePredictor, MonteCarloSimulator
from superhuman.real_data_loader import load_real_historical_data, get_available_seasons
from superhuman.playoff_series_model import PlayoffSeriesPredictor, get_series_predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_actual_cup_winners() -> Dict[int, str]:
    """Return actual Cup winners for validation."""
    return {
        2010: 'CHI', 2011: 'BOS', 2012: 'LAK', 2013: 'CHI', 2014: 'LAK',
        2015: 'CHI', 2016: 'PIT', 2017: 'PIT', 2018: 'WSH', 2019: 'STL',
        2020: 'TBL', 2021: 'TBL', 2022: 'COL', 2023: 'VGK', 2024: 'FLA'
    }


def validate_series_model():
    """Validate the playoff series model on historical data."""
    print("\n" + "=" * 60)
    print("STEP 4 VALIDATION: Playoff Series Model")
    print("=" * 60)

    # Test series predictor directly
    print("\n--- Testing PlayoffSeriesPredictor ---")
    predictor = PlayoffSeriesPredictor()
    predictor.fit()

    # Get empirical upset rates
    upset_rates = predictor.get_round_upset_rates()
    print("\nEmpirical Upset Rates by Round:")
    round_names = {1: "Round 1", 2: "Round 2", 3: "Conf Finals", 4: "Cup Finals"}
    for rnd, rate in sorted(upset_rates.items()):
        print(f"  {round_names[rnd]}: {rate:.1%} upset rate")

    # Test predictions at different strength differentials
    print("\nPredicted Higher Seed Win Probability:")
    for rnd in [1, 2, 3, 4]:
        base_prob = predictor.predict_series_probability(
            "TBL", "MTL", round_num=rnd, strength_diff=5, experience_diff=0.5
        )
        print(f"  {round_names[rnd]}: {base_prob:.1%}")


def compare_with_without_enhanced_model():
    """Compare Cup predictions with and without enhanced playoff model."""
    print("\n" + "=" * 60)
    print("COMPARISON: Enhanced vs Basic Playoff Model")
    print("=" * 60)

    cup_winners = get_actual_cup_winners()
    available = get_available_seasons()
    test_seasons = [s for s in range(2012, 2025) if s in available]

    results_enhanced = defaultdict(dict)
    results_basic = defaultdict(dict)

    for test_season in test_seasons:
        # Train on all seasons before test season
        train_seasons = [s for s in range(2010, test_season) if s in available]
        if len(train_seasons) < 2:
            continue

        try:
            training_data = load_real_historical_data(
                start_season=min(train_seasons),
                end_season=max(train_seasons)
            )
        except Exception as e:
            print(f"Skipping {test_season} train data: {e}")
            continue

        if len(training_data) < 30:
            continue

        # Load test season
        try:
            test_data = load_real_historical_data(
                start_season=test_season,
                end_season=test_season
            )
        except Exception as e:
            print(f"Skipping {test_season} test data: {e}")
            continue

        # Train and predict with recency weighting OFF (for fair comparison)
        # Test WITH enhanced model
        predictor_enhanced = EnsemblePredictor(
            use_neural_network=True,
            use_recency_weighting=False
        )
        predictor_enhanced.monte_carlo.use_enhanced_model = True
        predictor_enhanced.fit(training_data)
        predictions_enhanced = predictor_enhanced.predict(test_data)

        # Test WITHOUT enhanced model
        predictor_basic = EnsemblePredictor(
            use_neural_network=True,
            use_recency_weighting=False
        )
        predictor_basic.monte_carlo.use_enhanced_model = False
        predictor_basic.fit(training_data)
        predictions_basic = predictor_basic.predict(test_data)

        # Store results
        actual = cup_winners.get(test_season, "?")

        # Enhanced model ranking
        sorted_enhanced = sorted(predictions_enhanced, key=lambda p: -p.cup_win_probability)
        top_pick_enhanced = sorted_enhanced[0].team if sorted_enhanced else "?"
        rank_enhanced = next(
            (i+1 for i, p in enumerate(sorted_enhanced) if p.team == actual),
            len(sorted_enhanced)
        )

        # Basic model ranking
        sorted_basic = sorted(predictions_basic, key=lambda p: -p.cup_win_probability)
        top_pick_basic = sorted_basic[0].team if sorted_basic else "?"
        rank_basic = next(
            (i+1 for i, p in enumerate(sorted_basic) if p.team == actual),
            len(sorted_basic)
        )

        results_enhanced[test_season] = {
            'pick': top_pick_enhanced,
            'actual': actual,
            'rank': rank_enhanced,
            'correct': top_pick_enhanced == actual
        }
        results_basic[test_season] = {
            'pick': top_pick_basic,
            'actual': actual,
            'rank': rank_basic,
            'correct': top_pick_basic == actual
        }

    # Print comparison
    print("\nSeason-by-Season Comparison:")
    print("-" * 65)
    print(f"{'Season':<8} {'Basic Pick':<12} {'Enhanced Pick':<14} {'Actual':<8} {'Basic Rk':<10} {'Enh Rk'}")
    print("-" * 65)

    for season in sorted(results_enhanced.keys()):
        basic = results_basic[season]
        enhanced = results_enhanced[season]

        basic_mark = "✓" if basic['correct'] else ""
        enh_mark = "✓" if enhanced['correct'] else ""

        print(f"{season:<8} {basic['pick']:<12} {enhanced['pick']:<14} {enhanced['actual']:<8} "
              f"{basic['rank']:<10} {enhanced['rank']}")

    # Summary statistics
    print("\n" + "-" * 65)
    print("SUMMARY STATISTICS")
    print("-" * 65)

    n = len(results_enhanced)

    # Top-N accuracy
    for topn in [1, 3, 5, 8]:
        basic_count = sum(1 for r in results_basic.values() if r['rank'] <= topn)
        enh_count = sum(1 for r in results_enhanced.values() if r['rank'] <= topn)
        print(f"Top-{topn} Accuracy: Basic={basic_count}/{n} ({basic_count/n:.1%}) | "
              f"Enhanced={enh_count}/{n} ({enh_count/n:.1%})")

    # Average rank
    avg_basic = sum(r['rank'] for r in results_basic.values()) / n
    avg_enh = sum(r['rank'] for r in results_enhanced.values()) / n
    print(f"\nAverage Winner Rank: Basic={avg_basic:.2f} | Enhanced={avg_enh:.2f}")

    # Improvements
    improved = sum(
        1 for s in results_enhanced
        if results_enhanced[s]['rank'] < results_basic[s]['rank']
    )
    degraded = sum(
        1 for s in results_enhanced
        if results_enhanced[s]['rank'] > results_basic[s]['rank']
    )
    same = n - improved - degraded

    print(f"\nRank Changes: Improved={improved} | Same={same} | Degraded={degraded}")

    return results_enhanced, results_basic


def validate_full_pipeline():
    """Run full validation with best configuration."""
    print("\n" + "=" * 60)
    print("FULL PIPELINE VALIDATION (Best Config)")
    print("=" * 60)

    cup_winners = get_actual_cup_winners()
    available = get_available_seasons()
    test_seasons = [s for s in range(2012, 2025) if s in available]

    results = []

    for test_season in test_seasons:
        # Train on all seasons before test season
        train_seasons = [s for s in range(2010, test_season) if s in available]
        if len(train_seasons) < 2:
            continue

        try:
            training_data = load_real_historical_data(
                start_season=min(train_seasons),
                end_season=max(train_seasons)
            )
        except Exception as e:
            print(f"Skipping {test_season} train: {e}")
            continue

        if len(training_data) < 30:
            continue

        # Load test season
        try:
            test_data = load_real_historical_data(
                start_season=test_season,
                end_season=test_season
            )
        except Exception as e:
            print(f"Skipping {test_season} test: {e}")
            continue

        # Best configuration: Enhanced model + No recency weighting (for Top-1)
        predictor = EnsemblePredictor(
            use_neural_network=True,
            use_recency_weighting=False
        )
        predictor.fit(training_data)
        predictions = predictor.predict(test_data)

        # Get rankings
        actual = cup_winners.get(test_season, "?")
        sorted_preds = sorted(predictions, key=lambda p: -p.cup_win_probability)
        top_pick = sorted_preds[0].team if sorted_preds else "?"

        rank = next(
            (i+1 for i, p in enumerate(sorted_preds) if p.team == actual),
            len(sorted_preds)
        )

        results.append({
            'season': test_season,
            'pick': top_pick,
            'actual': actual,
            'rank': rank,
            'correct': top_pick == actual,
            'top3': [p.team for p in sorted_preds[:3]],
            'top5': [p.team for p in sorted_preds[:5]]
        })

    # Print results
    print("\nSeason-by-Season Results:")
    print("-" * 55)
    print(f"{'Season':<8} {'Pick':<8} {'Actual':<8} {'Rank':<6} {'Top 3'}")
    print("-" * 55)

    for r in results:
        mark = "✓" if r['correct'] else ""
        top3_str = ", ".join(r['top3'])
        print(f"{r['season']:<8} {r['pick']:<8} {r['actual']:<8} {r['rank']:<6} {top3_str}")

    # Summary
    print("\n" + "-" * 55)
    n = len(results)

    print("\nFinal Accuracy Summary:")
    for topn in [1, 3, 5, 8, 10]:
        count = sum(1 for r in results if r['rank'] <= topn)
        random_rate = topn / 32
        multiplier = (count/n) / random_rate if random_rate > 0 else 0
        print(f"  Top-{topn}: {count}/{n} ({count/n:.1%}) - {multiplier:.1f}x vs random")

    avg_rank = sum(r['rank'] for r in results) / n
    print(f"\n  Average Winner Rank: {avg_rank:.2f}")

    return results


if __name__ == "__main__":
    # Test series model directly
    validate_series_model()

    # Compare with and without enhanced model
    compare_with_without_enhanced_model()

    # Full pipeline validation
    validate_full_pipeline()
