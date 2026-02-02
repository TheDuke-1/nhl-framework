# Phase 2/3 Review: Ensemble Model System

## Issues Found and Fixed

### CRITICAL - FIXED

1. **Cup probabilities sum to 166%, not 100%**
   - Monte Carlo + GB classifier probabilities not normalized
   - **FIX APPLIED:** Added normalization step in `EnsemblePredictor.predict()`

2. **Gradient Boosting classifier inverted (distribution shift)**
   - VAN (worst team) was getting 81.9% Cup probability
   - COL (best team) was getting 0.7%
   - Cause: GB trained on synthetic data with different distribution than real data
   - **FIX APPLIED:** Removed GB from ensemble, use only Monte Carlo with playoff gating

3. **Tier thresholds too high**
   - Most teams classified as "Bubble" with fixed thresholds
   - **FIX APPLIED:** Added `_classify_tier_percentile()` using rank-based classification

### HIGH - DOCUMENTED

4. **clutch_performance excluded from weights**
   - Feature has zero variance in current data
   - Not differentiating teams
   - **STATUS:** Documented, would need game-by-game data

5. **recent_form always 0.0**
   - Would need game-by-game data to calculate momentum
   - **STATUS:** Documented, feature excluded from model

### MEDIUM

6. **Star power weight only 4.4%**
   - Current season data has starPPG = 0 for all teams
   - Model can't learn proper weight with no variation
   - **STATUS:** Documented limitation

7. **road_performance same for all teams**
   - Current data doesn't have home/away splits
   - **STATUS:** Documented, feature not differentiating

## Fixes Applied Summary

1. **Normalization** - Cup probabilities now sum to 100%
2. **Percentile tiers** - Distribution-based tier assignment
3. **GB classifier removed** - Suffering from distribution shift
4. **Playoff gating** - Cup probability scaled by playoff probability

## Verification Results

After fixes:
```
Top Cup Favorites:
1. TB: 16.2% (72 pts, strength 55.3)
2. COL: 15.7% (79 pts, strength 55.5)
3. BUF: 9.9% (67 pts, strength 52.3)

Bottom Teams (correctly low):
- VAN: 0.0% (39 pts, worst team)
- CGY: 0.0% (48 pts)
- STL: 0.0% (49 pts)

Total: 100.0%
```

## Remaining Architecture Issues

1. **Synthetic training data** - Not representative of real distributions
   - Weights learned may not transfer well
   - Should use historical NHL data when available

2. **Missing features** - Several features not differentiating:
   - road_performance, star_power, clutch_performance, recent_form
   - These need richer data sources

3. **Monte Carlo uses static playoff seeding**
   - Doesn't simulate remaining regular season games
   - Assumes current standings = final standings
