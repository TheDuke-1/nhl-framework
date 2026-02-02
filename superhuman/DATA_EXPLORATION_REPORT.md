# Data Exploration Report: Superhuman NHL Prediction System

## Executive Summary

Comprehensive data profiling of the superhuman prediction system reveals a well-structured dataset with some critical data quality issues that impact model performance.

**Key Findings:**
- 🔴 5 features have zero variance in current season data
- 🟢 Low multicollinearity (all VIF < 1.1)
- 🟢 Strong correlation between predictions and actual team quality
- ⚠️ Some raw metrics missing in source data (ff_pct, sf_pct, hdcf, hdca)

---

## 1. Data Sources Overview

| Data Source | Rows | Columns | Grain | Primary Key |
|-------------|------|---------|-------|-------------|
| Current Season (teams.json) | 32 | 43 | Team | team |
| Historical (synthetic) | 512 | 43 | Team-Season | (team, season) |
| Feature Vectors | 512/32 | 11 | Team-Season | (team, season) |
| Predictions | 32 | 9 | Team | team |

### Season Coverage
- Training: 2010-2025 (16 seasons × 32 teams = 512 samples)
- Current: 2026 season

---

## 2. Completeness Analysis

### Current Season Data (teams.json)
All 43 columns have **0% null rate** - data is complete.

### Zero-Variance Columns (Critical Issues)
The following columns have identical values for all teams:

| Column | Value | Impact |
|--------|-------|--------|
| ff_pct | 50.0 | Cannot differentiate teams |
| sf_pct | 50.0 | Cannot differentiate teams |
| hdcf | 0 | Missing high-danger chances |
| hdca | 0 | Missing high-danger chances |
| save_pct | 0.9 | All teams same save % |

**Recommendation:** These fields need real data from NHL API or must be excluded from the model.

---

## 3. Feature Quality Assessment

### Training Data Feature Distributions

| Feature | Mean | Std | Min | Max | Status |
|---------|------|-----|-----|-----|--------|
| goal_differential_rate | -0.005 | 0.432 | -1.22 | 1.44 | 🟢 Good |
| territorial_dominance | 0.000 | 1.034 | -3.23 | 2.89 | 🟢 Good |
| shot_quality_premium | -0.000 | 1.004 | -2.81 | 2.56 | 🟢 Good |
| goaltending_quality | -0.026 | 1.053 | -3.39 | 3.93 | 🟢 Good |
| special_teams_composite | -0.004 | 0.436 | -1.19 | 1.28 | 🟢 Good |
| road_performance | -0.168 | 0.304 | -1.00 | 0.62 | ⚠️ Low variance |
| roster_depth | 0.735 | 0.230 | 0.30 | 1.10 | ⚠️ Low variance |
| star_power | 0.205 | 0.299 | -0.40 | 1.15 | ⚠️ Low variance |
| clutch_performance | 0.000 | 0.000 | 0.00 | 0.00 | 🔴 Zero variance |
| recent_form | 0.000 | 0.000 | 0.00 | 0.00 | 🔴 Zero variance |

### Current Season Feature Issues

| Feature | Issue | Root Cause |
|---------|-------|------------|
| road_performance | All 0.0 | No home/away split data |
| roster_depth | All 0.78 | Same calculation for all |
| star_power | All -1.6 | starPPG = 0 in source |
| clutch_performance | All 0.0 | Not implemented |
| recent_form | All 0.0 | No game-by-game data |

---

## 4. Multicollinearity Analysis

All features show **low multicollinearity** (VIF < 1.1), indicating independent information:

| Feature | VIF | Status |
|---------|-----|--------|
| goal_differential_rate | 1.01 | 🟢 Excellent |
| territorial_dominance | 1.02 | 🟢 Excellent |
| shot_quality_premium | 1.01 | 🟢 Excellent |
| goaltending_quality | 1.02 | 🟢 Excellent |
| special_teams_composite | 1.01 | 🟢 Excellent |
| sustainability | 1.01 | 🟢 Excellent |

**Note:** This is a significant improvement over V7.1 which had r=0.998 between xGD and xGF%.

---

## 5. Feature-Outcome Correlations

### Correlation with Playoffs (made_playoffs)

| Feature | r | Strength |
|---------|---|----------|
| goal_differential_rate | 0.394 | Moderate |
| territorial_dominance | 0.269 | Moderate |
| special_teams_composite | 0.251 | Moderate |
| goaltending_quality | 0.178 | Weak |
| shot_quality_premium | 0.024 | Weak |
| sustainability | -0.055 | Weak |

### Correlation with Points

| Feature | r | Strength |
|---------|---|----------|
| goal_differential_rate | 0.965 | **Very Strong** |
| All others | < 0.07 | Weak |

**Finding:** goal_differential_rate is the dominant predictor, explaining 93% of variance in points.

---

## 6. Prediction Validation

### Prediction-Reality Correlations

| Metric | vs Points | vs Goal Diff |
|--------|-----------|--------------|
| Strength | 0.753 | 0.879 |
| Playoff Prob | 0.767 | 0.889 |
| Cup Prob | 0.778 | 0.861 |

All predictions show strong positive correlation with actual team quality metrics.

### Tier Distribution

| Tier | Teams | Points Range | Mean Points |
|------|-------|--------------|-------------|
| Elite | 4 | 67-79 | 71.8 |
| Contender | 8 | 57-72 | 61.9 |
| Bubble | 8 | 49-71 | 59.9 |
| Longshot | 12 | 39-70 | 55.4 |

### Sanity Checks ✓

- ✅ Cup probabilities sum to 100.0%
- ✅ Top team by points (COL) = Top by strength (COL)
- ✅ Bottom team by points (VAN) = Bottom by strength (VAN)
- ✅ Strength vs Rank correlation: r = 0.963

---

## 7. Data Quality Issues Summary

### Critical (Must Fix)

1. **5 features with zero variance** in current data
   - road_performance, roster_depth, star_power, clutch_performance, recent_form
   - Impact: ~35% of feature space is non-differentiating

2. **Missing raw data** for possession metrics
   - ff_pct, sf_pct, hdcf, hdca all placeholder values
   - Impact: territorial_dominance feature relies on cf_pct only

### High (Should Fix)

3. **Synthetic training data**
   - Historical data is simulated, not real NHL stats
   - Impact: Learned weights may not transfer to real data

4. **Outcome leakage potential**
   - Stats and outcomes generated together
   - Mitigated by independent generation, but ideally use real data

### Medium (Nice to Have)

5. **Game-by-game data missing**
   - No recent_form (momentum) calculation possible
   - No clutch_performance calculation possible

---

## 8. Recommendations

### Immediate Actions
1. **Data sourcing**: Obtain real historical NHL data from NHL API
2. **Feature pruning**: Remove zero-variance features from model
3. **Feature weighting**: Reduce weight on features with no current season variance

### Model Improvements
1. Add home/away splits for road_performance
2. Add player-level data for star_power
3. Add game-by-game results for recent_form

### Monitoring
1. Track feature variance over time
2. Validate predictions against actual playoff outcomes
3. Retrain annually with new season data
