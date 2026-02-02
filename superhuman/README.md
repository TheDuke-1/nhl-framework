# Superhuman NHL Prediction System

A data-driven approach to NHL playoff and Stanley Cup prediction using ensemble machine learning.

## Overview

This system replaces manual weight assignment with data-driven optimization:

| Approach | How Weights are Set |
|----------|---------------------|
| V7.1 (Manual) | Expert judgment: "GD should be 30%" |
| Superhuman | Ridge regression learns: "GD explains 20.5% of variance" |

## Quick Start

```bash
# Run predictions
python -m superhuman.predictor

# Single team detail
python -m superhuman.predictor --team COL

# Export to JSON
python -m superhuman.predictor --output predictions.json
```

## Architecture

```
superhuman/
├── config.py           # Constants (teams, seasons, parameters)
├── data_models.py      # TeamSeason, FeatureVector, PredictionResult
├── data_loader.py      # Load historical & current season data
├── feature_engineering.py  # PCA transformation, derived features
├── models.py           # Ensemble (Ridge + LogReg + GradBoost + Monte Carlo)
├── validation.py       # Cross-validation, calibration, backtesting
├── predictor.py        # Main production interface
```

## Methodology

### 1. Feature Engineering (PCA-based)

Transform raw stats into orthogonal features:
- **Goal Differential Rate**: Goals scored/allowed per game
- **Territorial Dominance**: Possession metrics (CF%, FF%, xGF%)
- **Shot Quality Premium**: Expected vs actual goal conversion
- **Goaltending Quality**: Save percentage relative to expected
- **Special Teams Composite**: PP% and PK% combined
- **Sustainability**: PDO regression indicator

### 2. Weight Optimization (Ridge Regression)

Learn feature weights from historical outcomes:
```
Learned weights (example):
  goal_differential_rate: 20.5%
  special_teams_composite: 17.9%
  territorial_dominance: 17.3%
  sustainability: 13.1%
  roster_depth: 10.9%
```

### 3. Playoff Prediction (Logistic Regression)

Binary classifier trained on historical playoff outcomes.
Output: P(make playoffs | features)

### 4. Cup Prediction (Monte Carlo Simulation)

- Simulate full playoff bracket 10,000+ times
- Each series uses strength scores to determine win probability
- Cup probability = % of simulations where team wins

### 5. Probability Normalization

Ensure Cup probabilities sum to 100% across all teams.
Apply playoff gating: teams unlikely to make playoffs get reduced Cup probability.

## Output Example

```
TOP 5 CUP FAVORITES:
  1. TB: 16.2%
  2. COL: 15.7%
  3. BUF: 9.9%
  4. DAL: 7.8%
  5. CAR: 6.5%

TIER BREAKDOWN:
  Elite: TB, COL, BUF, DAL
  Contender: PIT, MIN, VGK, UTA, EDM, OTT, PHI, TOR
  Bubble: CAR, BOS, MTL, WSH, CBJ, NYR, FLA, WPG
  Longshot: DET, NYI, ANA, SJ, LA, NSH, SEA, STL, CGY, NJ, CHI, VAN
```

## Validation Results

Cross-validation on 512 team-seasons:
- **Brier Score (Playoff)**: 0.1702 (better than 0.25 random)
- **Playoff Accuracy**: 74.6%
- **Calibration Error**: 0.0464 (well-calibrated)

## Limitations

1. **Synthetic Training Data**: Currently uses simulated historical data. Real NHL data would improve accuracy.

2. **Missing Features**: Some features don't differentiate teams due to data gaps:
   - road_performance (no home/away splits)
   - star_power (no player-level data)
   - recent_form (no game-by-game data)

3. **Cup Prediction Difficulty**: Correctly picking the Cup winner is inherently difficult (~6% baseline for top pick).

## Files Created

| File | Purpose |
|------|---------|
| PHASE1_REVIEW.md | Data infrastructure review |
| PHASE2_3_REVIEW.md | Ensemble model review |
| PHASE4_REVIEW.md | Validation framework review |
| PHASE5_REVIEW.md | Production system review |

## API Usage

```python
from superhuman import SuperhumanPredictor

# Create and train predictor
predictor = SuperhumanPredictor()
predictor.train()

# Get predictions
results = predictor.predict()

# Access specific team
col = predictor.get_team_prediction('COL')
print(f"COL Cup probability: {col.cup_win_probability:.1%}")

# Export to JSON
predictor.save_json('predictions.json')
```

## Dependencies

- numpy
- scikit-learn
- scipy
