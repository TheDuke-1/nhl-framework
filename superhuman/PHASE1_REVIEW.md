# Phase 1 Review: Data Infrastructure

## Issues Found

### CRITICAL

1. **PCA Explained Variance = [1.0, 0.0]**
   - First component captures 100% of variance
   - This means input features are perfectly collinear
   - Root cause: Synthetic historical data creates stats proportionally to outcomes
   - **FIX:** Add noise and independence to synthetic data generation

2. **Synthetic Data Leaks Outcome**
   - `base_gd = np.random.normal(0, 30)` then `if won_cup: base_gd += 40`
   - All other stats derive from `base_gd`
   - This creates perfect prediction (model will overfit)
   - **FIX:** Generate each stat independently with realistic distributions

### HIGH

3. **High Correlation Remains: gd_rate vs special_teams (0.827)**
   - Special teams calculation depends on GD indirectly via synthetic data
   - Violates orthogonality goal
   - **FIX:** Generate PP% and PK% from separate random processes

4. **recent_form is always 0.0**
   - No game-by-game data to calculate momentum
   - Creates NaN warnings in correlation calculations
   - **FIX:** Either remove from model or synthesize plausible values

### MEDIUM

5. **road_performance not calculated correctly**
   - Synthetic data sets road stats but doesn't vary by team
   - All teams get similar road performance
   - **FIX:** Generate road stats with team-specific variance

6. **star_power always 0 for current season**
   - `top_scorer_ppg` loaded as 0.0 from teams.json
   - 5% of model weight is wasted
   - **FIX:** Calculate from actual team data or document limitation

### LOW

7. **PCA fitted on synthetic data, applied to real data**
   - Mismatch between training distribution and inference distribution
   - Could cause feature drift
   - **FIX:** Consider refitting on combined data or using fixed transformations

## Anti-Patterns Detected

1. **Magic numbers without constants**
   - `base_gd / 3`, `base_gd / 6`, etc. scattered in code
   - Hard to understand and maintain
   - **FIX:** Define named constants with documented rationale

2. **Inconsistent PDO handling**
   - Sometimes 100-scale, sometimes 1.0-scale
   - Conversion logic duplicated
   - **FIX:** Standardize on one scale (100) everywhere

3. **No logging or progress indicators**
   - Silent failures hard to debug
   - **FIX:** Add logging module

## Dead Code

1. `TIME_DECAY_HALF_LIFE` defined but never used
2. `FeatureWeights` dataclass defined but never instantiated

## Refactoring Needed

1. **Separate synthetic data from real data loading**
   - Current: `load_historical_data()` synthesizes if file missing
   - Better: Explicit `synthesize_training_data()` function

2. **Add type hints to return values**
   - Some functions missing return type annotations

---

## Fixes to Apply

1. Rewrite synthetic data generation with independent random processes
2. Remove perfect correlation between stats and outcomes
3. Handle missing `recent_form` explicitly
4. Add logging
5. Define constants for magic numbers
