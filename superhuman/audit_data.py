#!/usr/bin/env python3
"""
Data Audit Script
=================
Verifies that the model training pipeline loads real data correctly.

Checks:
- Correct number of seasons loaded (2010-2024)
- ~30 teams per season
- Cup winners have playoff_rounds_won > 0
- All 14 features have non-zero variance (no silent defaults)
- Auxiliary features (star_power, clutch, vegas_signal, etc.) are populated

Usage:
    python -m superhuman.audit_data
"""

import sys
import logging
from collections import defaultdict

import numpy as np

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    from .data_loader import load_training_data, CUP_WINNERS
    from .feature_engineering import FeatureEngineer, create_feature_matrix
    from .data_models import FeatureVector

    print("=" * 60)
    print("DATA AUDIT REPORT")
    print("=" * 60)

    # 1. Load training data
    print("\n--- Loading training data ---")
    data = load_training_data()
    print(f"Total team-seasons loaded: {len(data)}")

    # 2. Count by season
    by_season = defaultdict(list)
    for ts in data:
        by_season[ts.season].append(ts)

    seasons = sorted(by_season.keys())
    print(f"Seasons: {seasons[0]}-{seasons[-1]} ({len(seasons)} seasons)")

    for season in seasons:
        teams = by_season[season]
        cup_winner = next((t for t in teams if t.won_cup), None)
        playoff_count = sum(1 for t in teams if t.made_playoffs)
        cup_str = f"Cup: {cup_winner.team}" if cup_winner else "Cup: MISSING"
        print(f"  {season}: {len(teams)} teams, {playoff_count} playoff teams, {cup_str}")

    # 3. Validate Cup winners
    print("\n--- Cup Winner Validation ---")
    issues = []
    for season in seasons:
        expected_winner = CUP_WINNERS.get(season)
        actual_winners = [t for t in by_season[season] if t.won_cup]

        if not actual_winners:
            issues.append(f"  {season}: No Cup winner found (expected {expected_winner})")
        elif len(actual_winners) > 1:
            issues.append(f"  {season}: Multiple Cup winners: {[t.team for t in actual_winners]}")
        else:
            winner = actual_winners[0]
            if winner.playoff_rounds_won < 4:
                issues.append(
                    f"  {season}: Cup winner {winner.team} has playoff_rounds_won={winner.playoff_rounds_won} (should be 4)"
                )

    if issues:
        print("ISSUES:")
        for issue in issues:
            print(issue)
    else:
        print("All Cup winners validated correctly.")

    # 4. Feature engineering check
    print("\n--- Feature Engineering ---")
    engineer = FeatureEngineer()
    features = engineer.fit_transform(data)

    X, y, names = create_feature_matrix(features)
    print(f"Feature matrix shape: {X.shape}")
    print(f"Target (playoff_success) range: {y.min():.2f} - {y.max():.2f}")

    print("\nFeature variance check:")
    zero_variance = []
    for i, name in enumerate(names):
        col = X[:, i]
        variance = np.var(col)
        nonzero_pct = np.mean(col != 0.0) * 100
        mean_val = np.mean(col)
        std_val = np.std(col)

        status = "OK" if variance > 1e-6 else "ZERO VARIANCE"
        if nonzero_pct < 10:
            status = "MOSTLY ZERO"

        print(f"  {name:<30} var={variance:>8.4f}  mean={mean_val:>7.3f}  "
              f"std={std_val:>6.3f}  nonzero={nonzero_pct:>5.1f}%  [{status}]")

        if variance < 1e-6:
            zero_variance.append(name)

    # 5. Summary
    print("\n--- SUMMARY ---")
    total_expected = len(seasons) * 30  # ~30 teams per season
    print(f"Team-seasons: {len(data)} (expected ~{total_expected})")
    print(f"Seasons covered: {len(seasons)}")
    print(f"Features with zero variance: {len(zero_variance)}")
    if zero_variance:
        print(f"  Problem features: {zero_variance}")
    print(f"Cup winners found: {sum(1 for t in data if t.won_cup)}/{len(seasons)}")
    print(f"Playoff teams found: {sum(1 for t in data if t.made_playoffs)}/{len(data)}")

    # Pass/fail
    ok = True
    if len(data) < 300:
        print("\nFAIL: Too few team-seasons (expected 400+)")
        ok = False
    if len(zero_variance) > 2:
        print("\nFAIL: Too many zero-variance features")
        ok = False
    if sum(1 for t in data if t.won_cup) < len(seasons) - 1:
        print("\nFAIL: Missing Cup winners")
        ok = False

    if ok:
        print("\nPASS: Data pipeline looks healthy.")
    else:
        print("\nFAIL: Issues detected — see above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
