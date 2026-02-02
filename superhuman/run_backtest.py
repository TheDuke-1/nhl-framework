#!/usr/bin/env python3
"""
Backtest Runner
===============
Runs time-series cross-validation on real historical data
and saves baseline results to reports/backtest_baseline.json.

Usage:
    python -m superhuman.run_backtest
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    from .config import RANDOM_SEED
    np.random.seed(RANDOM_SEED)
    from .data_loader import load_training_data, CUP_WINNERS
    from .validation import ValidationFramework
    from .betting_odds_loader import load_all_vegas_odds, calculate_vegas_brier_score

    print("=" * 60)
    print("BACKTEST: Real Data Baseline")
    print("=" * 60)

    # Load real training data
    print("\nLoading training data...")
    data = load_training_data()
    print(f"Loaded {len(data)} team-seasons")

    seasons = sorted(set(t.season for t in data))
    print(f"Seasons: {seasons[0]}-{seasons[-1]}")

    # Run time-series cross-validation
    print("\nRunning time-series cross-validation...")
    print("(Train on seasons up to N, test on season N+1)")
    print()

    validator = ValidationFramework()
    result = validator.cross_validate(data)

    # Print results
    validator.print_summary()

    # Additional: per-season Cup pick analysis
    print("\n--- Per-Season Cup Pick Analysis ---")

    by_season = defaultdict(list)
    for ts in data:
        by_season[ts.season].append(ts)

    seasons_list = sorted(by_season.keys())

    # Run individual season backtests to get per-season picks
    from .models import EnsemblePredictor
    cup_picks = {}
    top5_correct = 0
    total_tested = 0

    for idx in range(2, len(seasons_list)):
        train_seasons = seasons_list[:idx]
        test_season = seasons_list[idx]

        train_data = []
        for s in train_seasons:
            train_data.extend(by_season[s])
        test_data = by_season[test_season]

        if len(train_data) < 32 or len(test_data) < 16:
            continue

        model = EnsemblePredictor()
        model.fit(train_data)
        predictions = model.predict(test_data)
        predictions.sort(key=lambda p: -p.cup_win_probability)

        top_pick = predictions[0].team
        top5 = [p.team for p in predictions[:5]]
        actual_winner = CUP_WINNERS.get(test_season, "?")

        correct = "CORRECT" if top_pick == actual_winner else ""
        in_top5 = "top-5" if actual_winner in top5 else ""

        print(f"  {test_season}: Pick={top_pick:>4} ({predictions[0].cup_win_probability*100:.1f}%)  "
              f"Actual={actual_winner:>4}  {correct} {in_top5}")

        cup_picks[test_season] = {
            'top_pick': top_pick,
            'top_pick_prob': round(predictions[0].cup_win_probability, 4),
            'top_5': top5,
            'actual_winner': actual_winner,
            'correct': top_pick == actual_winner,
            'in_top_5': actual_winner in top5,
        }

        if actual_winner in top5:
            top5_correct += 1
        total_tested += 1

    top5_rate = top5_correct / total_tested if total_tested > 0 else 0
    print(f"\n  Top-5 rate: {top5_correct}/{total_tested} ({top5_rate*100:.0f}%)")

    # Vegas benchmark
    print("\n--- Vegas Benchmark ---")
    try:
        vegas_odds = load_all_vegas_odds(start_season=2010, end_season=2024)
        vegas_brier_playoff, n_playoff = calculate_vegas_brier_score(vegas_odds, target='playoff')
        vegas_brier_cup, n_cup = calculate_vegas_brier_score(vegas_odds, target='cup')
        print(f"  Vegas Brier (Playoff): {vegas_brier_playoff:.4f} (n={n_playoff})")
        print(f"  Vegas Brier (Cup):     {vegas_brier_cup:.4f} (n={n_cup})")
        print(f"  Model Brier (Playoff): {result.brier_score_playoff:.4f}")
        print(f"  Model Brier (Cup):     {result.brier_score_cup:.4f}")
    except Exception as e:
        logger.warning(f"Could not compute Vegas benchmark: {e}")
        vegas_brier_playoff = None
        vegas_brier_cup = None

    # Save results
    output = {
        'generated': datetime.now().isoformat(),
        'data_source': 'real_historical_csv',
        'seasons': f"{seasons[0]}-{seasons[-1]}",
        'team_seasons': len(data),
        'cv_results': result.to_dict(),
        'cup_picks': cup_picks,
        'top_5_rate': round(top5_rate, 4),
        'top_5_correct': top5_correct,
        'top_5_total': total_tested,
    }

    if vegas_brier_playoff is not None:
        output['vegas_benchmark'] = {
            'brier_playoff': round(vegas_brier_playoff, 4),
            'brier_cup': round(vegas_brier_cup, 4),
        }

    output_path = Path(__file__).parent.parent / "reports" / "backtest_baseline.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
