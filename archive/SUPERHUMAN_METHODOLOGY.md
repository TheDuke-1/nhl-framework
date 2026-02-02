# Building a Superhuman NHL Prediction System

## From First Principles: A Complete Methodology

**Objective:** Create the most accurate predictor of:
1. Team strength (composite ranking)
2. Playoff probability
3. Stanley Cup probability

**Philosophy:** Let the data determine the weights, not human intuition.

---

## Part 1: The Fundamental Approach

### Why Most Models Fail

Traditional hockey models fail because they:
1. **Use intuition-based weights** - "Goaltending feels like 15%" is not rigorous
2. **Ignore multicollinearity** - Correlated metrics get double-counted
3. **Overfit to recent history** - Optimizing for 2019 STL doesn't generalize
4. **Confuse process and outcome** - xG is process; goals are outcome. Both matter differently
5. **Treat all games equally** - A January game ≠ a March game for playoff prediction

### The Superhuman Approach

We will:
1. **Let regression determine weights** from 20+ years of data
2. **Use orthogonal (uncorrelated) features** via PCA or careful selection
3. **Separate models for different predictions** (playoffs vs Cup)
4. **Time-weight recent performance** appropriately
5. **Validate rigorously** with proper train/test splits

---

## Part 2: Data Architecture

### 2.1 Historical Data Collection (Minimum 15 Seasons)

| Data Type | Source | Granularity | Purpose |
|-----------|--------|-------------|---------|
| Game results | NHL API | Per-game | Outcome ground truth |
| Shot data | MoneyPuck | Per-game | xG, HDCF calculation |
| Goalie stats | MoneyPuck | Per-game | GSAx, HD SV% |
| Player stats | NHL API | Per-game | Star power, depth |
| Standings | NHL API | Daily snapshots | Point pace, playoff odds |
| Playoff results | NHL API | Per-series | Cup probability ground truth |
| Injuries | Manual/DailyFaceoff | Daily | Roster impact |
| Betting odds | Historical archives | Pre-playoff | Market baseline |

### 2.2 Feature Categories

**Process Metrics** (How they play):
- Expected goals for/against (xGF, xGA)
- High-danger chance share (HDCF%)
- Shot attempt share (CF%)
- Zone entry/exit rates (if available)
- Defensive structure metrics

**Outcome Metrics** (Results achieved):
- Goal differential
- Win percentage
- Points percentage
- Record in close games

**Situational Metrics** (Context-specific):
- Road performance
- Back-to-back performance
- Performance vs playoff teams
- Performance when trailing
- 3rd period performance

**Sustainability Indicators** (Luck/regression signals):
- PDO (shooting% + save%)
- Shooting percentage vs expected
- Save percentage vs expected
- Record in OT/shootouts

**Roster Metrics** (Player quality):
- Top player points-per-game
- Depth scoring (players with 15+ goals)
- Top-pair defenseman quality
- Goaltender GSAx
- Backup goaltender quality

**Momentum Metrics** (Recent form):
- Last 10/20/30 game performance
- Rolling xGF%
- Rolling GSAx
- Streak/slump indicators

---

## Part 3: Feature Engineering

### 3.1 Creating Orthogonal Features

**Problem:** Raw metrics are highly correlated (as we found: xGD ↔ xGF% at r=0.998)

**Solution:** Principal Component Analysis (PCA) or manual orthogonalization

```python
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def create_orthogonal_features(team_data):
    """Transform correlated metrics into independent components."""

    # Group 1: Possession/xG metrics (currently 31% of model, highly correlated)
    possession_metrics = ['hdcfPct', 'cfPct', 'xgf', 'xga', 'xgd', 'scfPct']

    # Standardize
    scaler = StandardScaler()
    possession_scaled = scaler.fit_transform(team_data[possession_metrics])

    # PCA to extract independent components
    pca = PCA(n_components=2)  # Reduce to 2 independent features
    possession_pca = pca.fit_transform(possession_scaled)

    # PC1 = "Territorial Dominance" (overall possession quality)
    # PC2 = "Shot Quality Premium" (quality vs quantity tradeoff)

    team_data['territorial_dominance'] = possession_pca[:, 0]
    team_data['shot_quality_premium'] = possession_pca[:, 1]

    return team_data
```

### 3.2 Time-Weighted Features

**Insight:** Recent performance is more predictive than early-season

```python
def calculate_time_weighted_metric(games, metric, half_life_games=20):
    """
    Exponentially weight recent games more heavily.

    half_life_games: Number of games for weight to decay by 50%
    """
    weights = []
    values = []

    for i, game in enumerate(reversed(games)):  # Most recent first
        decay = 0.5 ** (i / half_life_games)
        weights.append(decay)
        values.append(game[metric])

    return np.average(values, weights=weights)
```

### 3.3 Derived Features

```python
def engineer_features(team):
    """Create derived features with predictive power."""

    features = {}

    # 1. Goal differential per game (normalize for games played)
    features['gd_per_game'] = team['gd'] / team['gp']

    # 2. Points pace (projected 82-game points)
    features['points_pace'] = (team['pts'] / team['gp']) * 82

    # 3. Pythagorean expectation (expected win% from goals)
    gf, ga = team['gf'], team['ga']
    features['pythag_win_pct'] = gf**2.37 / (gf**2.37 + ga**2.37)

    # 4. Luck factor (actual vs expected wins)
    expected_wins = features['pythag_win_pct'] * team['gp']
    features['luck_factor'] = team['w'] - expected_wins

    # 5. Close game dominance
    features['clutch_factor'] = (
        team['ot_wins'] * 1.5 +
        team['one_goal_wins'] -
        team['blown_leads']
    ) / team['gp']

    # 6. Goaltending reliability (GSAx stability)
    features['goalie_floor'] = min(team['starter_gsax'], team['backup_gsax'])
    features['goalie_ceiling'] = max(team['starter_gsax'], team['backup_gsax'])

    # 7. Playoff-style readiness
    features['playoff_style'] = (
        0.3 * team['pk_pct_rank'] +
        0.3 * team['road_win_pct_rank'] +
        0.2 * team['gsax_rank'] +
        0.2 * team['gd_rank']
    )

    return features
```

---

## Part 4: Model Architecture

### 4.1 Ensemble Approach

**No single model is optimal.** Use an ensemble:

```
┌─────────────────────────────────────────────────────────────┐
│                    ENSEMBLE PREDICTION                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Logistic   │  │   Gradient   │  │    Neural    │       │
│  │  Regression  │  │   Boosting   │  │   Network    │       │
│  │  (Baseline)  │  │  (XGBoost)   │  │   (MLP)      │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └────────────┬────┴────────────────┘                │
│                      │                                       │
│              ┌───────▼───────┐                              │
│              │   Weighted    │                              │
│              │   Average     │                              │
│              │  (Meta-Model) │                              │
│              └───────┬───────┘                              │
│                      │                                       │
│              ┌───────▼───────┐                              │
│              │   Calibrated  │                              │
│              │  Probability  │                              │
│              └───────────────┘                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Model 1: Logistic Regression (Interpretable Baseline)

```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

class PlayoffPredictor:
    """Logistic regression for playoff probability."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = LogisticRegression(
            penalty='l1',  # Lasso for feature selection
            solver='saga',
            C=0.1,  # Regularization strength
            max_iter=1000
        )

    def fit(self, X, y):
        """
        X: Feature matrix (teams x features)
        y: Binary outcome (1 = made playoffs, 0 = missed)
        """
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

        # Extract learned weights
        self.feature_weights = dict(zip(
            self.feature_names,
            self.model.coef_[0]
        ))

    def predict_proba(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]
```

### 4.3 Model 2: Gradient Boosting (Capture Non-Linearities)

```python
import xgboost as xgb

class CupPredictor:
    """XGBoost for Stanley Cup probability."""

    def __init__(self):
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,  # Shallow trees prevent overfitting
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='binary:logistic',
            eval_metric='logloss',
            use_label_encoder=False
        )

    def fit(self, X, y, eval_set=None):
        """
        X: Feature matrix
        y: Binary (1 = won Cup, 0 = didn't)
        """
        self.model.fit(
            X, y,
            eval_set=eval_set,
            early_stopping_rounds=10,
            verbose=False
        )

    def predict_proba(self, X):
        return self.model.predict_proba(X)[:, 1]

    def get_feature_importance(self):
        return dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))
```

### 4.4 Model 3: Monte Carlo Simulation (Capture Playoff Randomness)

```python
class MonteCarloPlayoffs:
    """Simulate playoff bracket thousands of times."""

    def __init__(self, n_simulations=100000):
        self.n_sims = n_simulations

    def simulate_series(self, team_a, team_b, team_a_strength, team_b_strength):
        """
        Simulate best-of-7 series using Elo-style win probability.

        Returns: probability team_a wins series
        """
        # Elo-style expected score
        expected_a = 1 / (1 + 10**((team_b_strength - team_a_strength) / 400))

        # Add home ice advantage
        home_boost = 0.04

        # Simulate 10000 series
        wins_a = 0
        for _ in range(10000):
            a_wins, b_wins = 0, 0
            game = 0
            home_pattern = [True, True, False, False, True, False, True]

            while a_wins < 4 and b_wins < 4:
                prob_a = expected_a + (home_boost if home_pattern[game] else -home_boost)
                prob_a = max(0.15, min(0.85, prob_a))  # Bound probabilities

                if random.random() < prob_a:
                    a_wins += 1
                else:
                    b_wins += 1
                game += 1

            if a_wins == 4:
                wins_a += 1

        return wins_a / 10000

    def simulate_full_playoffs(self, playoff_teams, team_strengths):
        """
        Run full playoff simulation n_sims times.

        Returns: Cup probability for each team
        """
        cup_wins = defaultdict(int)

        for _ in range(self.n_sims):
            # Simulate each round
            winner = self._simulate_bracket(playoff_teams, team_strengths)
            cup_wins[winner] += 1

        return {team: wins/self.n_sims for team, wins in cup_wins.items()}
```

---

## Part 5: Weight Optimization

### 5.1 Let Data Determine Weights

**Key Insight:** Don't guess weights. Use regularized regression to find optimal weights.

```python
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import GridSearchCV

def optimize_weights(X, y, method='ridge'):
    """
    Use regularized regression to find optimal feature weights.

    X: Feature matrix (historical team-seasons)
    y: Outcome (playoff success metric)

    Returns: Optimal weights per feature
    """
    if method == 'ridge':
        # Ridge regression: keeps all features, shrinks weights
        model = Ridge()
        param_grid = {'alpha': [0.01, 0.1, 1, 10, 100]}
    else:
        # Lasso regression: eliminates useless features
        model = Lasso()
        param_grid = {'alpha': [0.001, 0.01, 0.1, 1]}

    # Cross-validated grid search
    grid_search = GridSearchCV(
        model,
        param_grid,
        cv=5,  # 5-fold cross-validation
        scoring='neg_mean_squared_error'
    )

    grid_search.fit(X, y)

    best_model = grid_search.best_estimator_

    # Extract and normalize weights to sum to 100%
    raw_weights = np.abs(best_model.coef_)
    normalized_weights = raw_weights / raw_weights.sum() * 100

    return dict(zip(feature_names, normalized_weights))
```

### 5.2 Target Variable Construction

**Critical Decision:** What is y (the target)?

For **Playoff Probability:**
```python
y_playoff = 1 if team made playoffs else 0
```

For **Cup Probability**, use a continuous measure:
```python
def calculate_playoff_success_score(team_season):
    """
    Continuous measure of playoff success.
    Allows regression to learn from degrees of success.
    """
    if not team_season['made_playoffs']:
        return 0.0

    rounds_won = team_season['playoff_rounds_won']

    # Exponential scaling: Cup worth more than sum of rounds
    scores = {
        0: 0.10,  # Made playoffs, lost R1
        1: 0.25,  # Won R1
        2: 0.45,  # Conference Finals
        3: 0.70,  # Cup Finals
        4: 1.00   # Won Cup
    }

    return scores.get(rounds_won, 0)
```

### 5.3 Feature Selection via Importance

```python
def select_features_by_importance(X, y, threshold=0.02):
    """
    Remove features that don't contribute meaningfully.
    """
    # Fit random forest for importance scores
    from sklearn.ensemble import RandomForestClassifier

    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X, y)

    importances = rf.feature_importances_

    # Keep features with importance > threshold
    selected = [
        feat for feat, imp in zip(feature_names, importances)
        if imp > threshold
    ]

    print(f"Selected {len(selected)} of {len(feature_names)} features")

    return selected
```

---

## Part 6: The Formula

### 6.1 Final Superhuman Formula Structure

After optimization, the formula will look like:

```
TEAM_STRENGTH = Σ (wi × fi × ti)

Where:
  wi = Optimized weight for feature i (from regression)
  fi = Normalized feature value (z-score)
  ti = Time decay factor (more recent = higher)
```

### 6.2 Expected Optimized Weights (Hypothetical)

Based on hockey analytics research, we'd expect regression to discover:

| Feature Category | Expected Weight | Rationale |
|-----------------|-----------------|-----------|
| Goal Differential (rate) | 15-20% | Strongest single predictor |
| Territorial Dominance (PCA) | 12-15% | Sustainable process metric |
| Goaltending (GSAx) | 10-15% | High-leverage position |
| Special Teams Composite | 10-12% | PK especially predictive |
| Road Performance | 8-10% | Playoff necessity |
| Recent Form (L20 xGF%) | 8-10% | Momentum matters |
| Roster Depth | 6-8% | Injury insurance |
| Star Power | 5-7% | Ceiling raiser |
| Close-Game Performance | 4-6% | Clutch factor |
| Schedule Difficulty Adjustment | 3-5% | Context matters |
| Sustainability (anti-PDO) | 2-4% | Regression indicator |

### 6.3 Probability Conversion

```python
def strength_to_playoff_probability(strength_score, all_team_scores):
    """
    Convert strength score to calibrated playoff probability.
    """
    # Rank-based logistic transformation
    rank = sorted(all_team_scores, reverse=True).index(strength_score) + 1

    # Logistic function calibrated to historical make rates
    # Top 8 per conference make playoffs
    prob = 1 / (1 + np.exp(0.3 * (rank - 16)))  # Midpoint at rank 16

    return np.clip(prob, 0.01, 0.99)

def strength_to_cup_probability(strength_score, all_team_scores, playoff_teams):
    """
    Convert strength to Cup probability via simulation.
    """
    if strength_score not in playoff_teams:
        return 0.0

    # Run Monte Carlo simulation
    mc = MonteCarloPlayoffs(n_simulations=50000)
    cup_probs = mc.simulate_full_playoffs(playoff_teams, all_team_scores)

    return cup_probs[strength_score]
```

---

## Part 7: Validation Framework

### 7.1 Proper Train/Test Split

**Critical:** Never test on data used for training.

```python
def temporal_train_test_split(data, test_seasons=3):
    """
    Use older seasons for training, recent for testing.
    This mimics real-world prediction scenario.
    """
    all_seasons = sorted(data['season'].unique())

    test_seasons = all_seasons[-test_seasons:]
    train_seasons = all_seasons[:-test_seasons]

    train = data[data['season'].isin(train_seasons)]
    test = data[data['season'].isin(test_seasons)]

    return train, test
```

### 7.2 Evaluation Metrics

```python
def evaluate_model(predictions, actuals):
    """Comprehensive model evaluation."""

    metrics = {}

    # 1. Brier Score (probability accuracy)
    metrics['brier_score'] = np.mean((predictions - actuals) ** 2)

    # 2. Log Loss (penalizes confident wrong predictions)
    from sklearn.metrics import log_loss
    metrics['log_loss'] = log_loss(actuals, predictions)

    # 3. AUC-ROC (discrimination ability)
    from sklearn.metrics import roc_auc_score
    metrics['auc_roc'] = roc_auc_score(actuals, predictions)

    # 4. Calibration Error
    from sklearn.calibration import calibration_curve
    prob_true, prob_pred = calibration_curve(actuals, predictions, n_bins=10)
    metrics['calibration_error'] = np.mean(np.abs(prob_true - prob_pred))

    # 5. Top-N Accuracy (did champion come from top N?)
    for n in [3, 5, 8]:
        top_n = np.argsort(predictions)[-n:]
        champion_idx = np.argmax(actuals)
        metrics[f'top_{n}_accuracy'] = 1 if champion_idx in top_n else 0

    return metrics
```

### 7.3 Calibration

```python
from sklearn.calibration import CalibratedClassifierCV

def calibrate_probabilities(model, X_calib, y_calib):
    """
    Ensure predicted probabilities match actual frequencies.
    """
    calibrated = CalibratedClassifierCV(
        model,
        method='isotonic',  # Non-parametric calibration
        cv='prefit'
    )

    calibrated.fit(X_calib, y_calib)

    return calibrated
```

---

## Part 8: Implementation Roadmap

### Phase 1: Data Infrastructure (Weeks 1-3)

1. Build historical database (15+ seasons)
2. Automate daily data ingestion
3. Create feature calculation pipeline
4. Implement data validation checks

### Phase 2: Feature Engineering (Weeks 4-5)

1. Calculate all raw metrics
2. Apply PCA to correlated groups
3. Create time-weighted versions
4. Engineer derived features
5. Validate feature distributions

### Phase 3: Model Development (Weeks 6-8)

1. Train baseline logistic regression
2. Train XGBoost model
3. Build Monte Carlo simulator
4. Create ensemble meta-model
5. Calibrate probability outputs

### Phase 4: Validation (Weeks 9-10)

1. Run temporal cross-validation
2. Backtest against 10+ seasons
3. Compare to market (betting odds)
4. Analyze failure modes
5. Document model limitations

### Phase 5: Production (Weeks 11-12)

1. Build real-time update pipeline
2. Create dashboard/API
3. Implement monitoring
4. Set up alerting for anomalies
5. Document maintenance procedures

---

## Part 9: Expected Performance

### Baseline Comparisons

| Predictor | Cup Winner in Top 5 | Brier Score |
|-----------|---------------------|-------------|
| Random | 31% | 0.060 |
| Points-only | 55% | 0.052 |
| Betting markets | 70% | 0.045 |
| Current V7.1 | 70% | ~0.048 |
| **Superhuman Target** | **85%+** | **<0.040** |

### Why Superhuman is Achievable

1. **Data advantage**: Using more features than markets price
2. **No bias**: Regression finds weights without human preconceptions
3. **Ensemble power**: Combining models captures different signals
4. **Proper validation**: Won't overfit to recent anomalies
5. **Continuous learning**: Can retrain as new data arrives

---

## Part 10: Key Principles Summary

### The 10 Commandments of Superhuman Prediction

1. **Let data determine weights** - Never guess
2. **Eliminate redundancy** - Correlated features get double-counted
3. **Validate properly** - Train/test split is sacred
4. **Calibrate probabilities** - 20% should mean 20%
5. **Ensemble models** - No single model is best
6. **Time-weight appropriately** - Recent matters more
7. **Separate process from outcome** - Both have value
8. **Account for randomness** - Playoffs are high-variance
9. **Monitor and update** - Models decay without maintenance
10. **Document limitations** - Know what you don't know

---

*Methodology Document v1.0*
*Approach: Empirical weight optimization with ensemble modeling*
