# Superhuman NHL Model: Action Plan

## Mission
Build the most accurate NHL prediction model ever created - one that consistently outperforms Vegas odds, expert analysts, and existing public models.

---

## Current State Assessment

### What's Working ✓
- 74.6% playoff accuracy (1.49x better than random)
- Well-calibrated probabilities (0.046 calibration error)
- Low multicollinearity (VIF < 1.1)
- Clean architecture with proper validation

### Critical Gaps ✗
| Issue | Impact | Priority |
|-------|--------|----------|
| Synthetic training data | Weights don't transfer to reality | 🔴 Critical |
| 5 features with zero variance | 35% of feature space wasted | 🔴 Critical |
| Goal differential dominance | Other features add <5% value | 🟠 High |
| Only 16 Cup winners in training | Predictions underpowered | 🟠 High |
| No player-level data | Missing key predictive signal | 🟠 High |
| No game-by-game data | Can't calculate momentum | 🟡 Medium |

---

## Phase 1: Real Data Infrastructure (Week 1-2)

### 1.1 NHL API Integration
**Goal:** Replace synthetic data with 15+ years of real NHL statistics

```python
# Data sources to integrate:
- NHL Stats API (api.nhle.com)
- Natural Stat Trick (advanced stats)
- Money Puck (expected goals models)
- Elite Prospects (prospect data)
```

**Deliverables:**
- [ ] `nhl_api_client.py` - NHL API wrapper
- [ ] `historical_scraper.py` - Backfill 2008-2025 seasons
- [ ] `data/historical/` - Parquet files for each season
- [ ] Automated daily data refresh pipeline

### 1.2 Data Schema Expansion
**Goal:** Capture all predictive signals

**New fields to add:**
```
Team-Level:
- home_record, away_record (road_performance)
- last_10_record, last_20_record (recent_form)
- games_remaining, strength_of_schedule
- back_to_back_record
- overtime_record

Goaltending:
- starter_games, starter_save_pct, starter_gsax
- backup_games, backup_save_pct
- goalie_fatigue_score

Special Situations:
- 5v5_gf_pct, 5v5_xgf_pct
- pp_opportunities, pp_goals
- pk_opportunities, pk_goals_against
- empty_net_goals_for, empty_net_goals_against
```

---

## Phase 2: Player-Level Features (Week 2-3)

### 2.1 Star Power Calculation
**Goal:** Quantify top-end talent impact

```python
def calculate_star_power(roster):
    """
    Components:
    1. Top-6 forward WAR (wins above replacement)
    2. Top-4 defenseman WAR
    3. Starting goalie GSAX
    4. Hart/Norris/Vezina vote getters (weighted)
    5. All-Star selections (last 3 years)
    """
    pass
```

### 2.2 Roster Depth Calculation
**Goal:** Measure beyond top players

```python
def calculate_roster_depth(roster):
    """
    Components:
    1. Bottom-6 forward production
    2. 3rd pairing defenseman metrics
    3. 4th line TOI and effectiveness
    4. Injury replacement performance
    5. AHL call-up quality
    """
    pass
```

### 2.3 Injury Impact Model
**Goal:** Adjust predictions for missing players

```python
def calculate_injury_impact(team, injuries):
    """
    - Player WAR × expected games missed
    - Position scarcity (goalies > top-4 D > top-6 F)
    - Replacement quality from AHL
    """
    pass
```

---

## Phase 3: Advanced Feature Engineering (Week 3-4)

### 3.1 Momentum/Form Features
**Goal:** Capture hot/cold streaks

```python
# New features:
- rolling_5_game_points_pct
- rolling_10_game_gf_pct
- rolling_5_game_xgf_pct
- days_since_last_game
- win_streak / loss_streak
- goal_differential_trend (slope of last 20 games)
```

### 3.2 Opponent-Adjusted Metrics
**Goal:** Account for schedule difficulty

```python
def calculate_opponent_adjusted_stats(team, games):
    """
    For each stat:
    1. Weight by opponent strength
    2. Compare to expected performance
    3. Calculate residual (actual - expected)
    """
    pass
```

### 3.3 Clutch Performance
**Goal:** Measure performance in high-leverage situations

```python
# Clutch indicators:
- record_in_one_goal_games
- 3rd_period_gf_pct_when_tied
- performance_vs_playoff_teams
- record_in_last_10_games_of_season
- playoff_series_win_rate (historical)
```

### 3.4 Sustainability Metrics
**Goal:** Predict regression candidates

```python
# PDO components:
- shooting_pct_vs_career_avg
- save_pct_vs_career_avg
- power_play_pct_vs_league_avg
- pdo_trend (improving or regressing?)
```

---

## Phase 4: Model Architecture Upgrade (Week 4-5)

### 4.1 Gradient Boosting with Proper Calibration
**Goal:** Fix the distribution shift problem

```python
from sklearn.calibration import CalibratedClassifierCV

class CalibratedCupPredictor:
    def __init__(self):
        self.base_model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8
        )
        self.calibrated = CalibratedClassifierCV(
            self.base_model,
            method='isotonic',
            cv=5
        )
```

### 4.2 Bayesian Ensemble
**Goal:** Proper uncertainty quantification

```python
class BayesianEnsemble:
    """
    Combine predictions using Bayesian model averaging:
    1. Ridge regression weights (current)
    2. Gradient boosting
    3. Neural network
    4. Historical team-specific priors

    Weight models by cross-validated likelihood.
    """
    pass
```

### 4.3 Dynamic Monte Carlo
**Goal:** Simulate remaining season, not just playoffs

```python
class DynamicSimulator:
    """
    1. Simulate remaining regular season games
    2. Use current standings + simulated results for seeding
    3. Then simulate playoffs
    4. Account for:
       - Home ice advantage
       - Travel/fatigue
       - Historical matchup data
       - Goalie rest patterns
    """
    pass
```

---

## Phase 5: External Signal Integration (Week 5-6)

### 5.1 Betting Market Baseline
**Goal:** Use market odds as a feature and benchmark

```python
# Integrate:
- Pinnacle closing lines (most efficient market)
- FanDuel/DraftKings Cup futures
- Series prices when available

# Use as:
- Baseline to beat (if we can't beat the market, we're not superhuman)
- Feature input (market wisdom is valuable signal)
- Calibration target (markets are well-calibrated)
```

### 5.2 Expert Consensus
**Goal:** Ensemble with human expertise

```python
# Sources:
- ESPN Power Rankings
- The Athletic rankings
- Dom Luszczyszyn's model (public version)
- Money Puck projections

# Combine:
- Use as features
- Weight by historical accuracy
- Identify where our model differs (alpha opportunities)
```

### 5.3 Social/News Signals
**Goal:** Capture information not in box scores

```python
# Monitor:
- Injury reports (Twitter beat writers)
- Line combinations (Daily Faceoff)
- Goalie start announcements
- Trade deadline activity
- Locker room chemistry signals
```

---

## Phase 6: Validation & Backtesting (Week 6-7)

### 6.1 Rigorous Backtesting Framework
**Goal:** Prove the model works on historical data

```python
class RigorousBacktest:
    """
    For each season 2010-2024:
    1. Train only on data available at that point
    2. Make predictions at multiple points:
       - Pre-season
       - 20 games
       - 40 games
       - 60 games
       - Playoff start
    3. Track:
       - Brier score vs Vegas odds
       - Calibration at each checkpoint
       - ROI if betting on our predictions
    """
    pass
```

### 6.2 Benchmark Comparisons
**Goal:** Prove we're the best

| Benchmark | How to Compare |
|-----------|----------------|
| Vegas odds | Lower Brier score, positive ROI |
| ESPN projections | Higher accuracy at each stage |
| Money Puck model | Head-to-head playoff picks |
| Random baseline | >35% Brier improvement |

### 6.3 Ablation Studies
**Goal:** Understand what drives accuracy

```python
# Test removing each feature/component:
- Without player-level data: how much worse?
- Without momentum features: how much worse?
- Without market data: how much worse?
- With only goal differential: how much worse?

# Identify the "alpha" sources
```

---

## Phase 7: Production System (Week 7-8)

### 7.1 Real-Time Updates
**Goal:** Predictions update after every game

```python
# Pipeline:
1. Game ends → NHL API webhook
2. Fetch updated stats
3. Recalculate features
4. Re-run predictions
5. Update dashboard
6. Send alerts for significant changes
```

### 7.2 Interactive Dashboard
**Goal:** Make predictions accessible and actionable

```
Dashboard features:
- Current Cup probabilities (live)
- Playoff probability over time (chart)
- "What if" scenarios (injuries, trades)
- Model vs market comparison
- Historical accuracy tracker
- Confidence intervals on all predictions
```

### 7.3 API for Integration
**Goal:** Allow others to use our predictions

```python
# Endpoints:
GET /api/predictions/current
GET /api/predictions/{team}
GET /api/predictions/history/{date}
GET /api/model/accuracy
POST /api/simulate/whatif
```

---

## Success Metrics

### Minimum Bar for "Superhuman"
| Metric | Target | Current |
|--------|--------|---------|
| Playoff Brier score | < 0.12 | 0.17 |
| Playoff accuracy | > 85% | 74.6% |
| Beat Vegas Brier | By 5%+ | Unknown |
| Cup winner in top 3 | > 50% | 0% |
| Calibration error | < 0.03 | 0.046 |
| Backtest ROI (flat bet) | > 5% | Unknown |

### Stretch Goals
- Predict Cup winner correctly 2+ times in 10 year backtest
- Beat all public models on Brier score
- Identify "value" bets with 10%+ edge

---

## Immediate Next Steps

### This Week
1. **Set up NHL API client** - Start pulling real data
2. **Build historical database** - 2010-2025, all teams, all games
3. **Fix zero-variance features** - Get real data for road/home splits

### Next Week
4. **Integrate player-level data** - WAR, GSAX, roster composition
5. **Implement momentum features** - Rolling windows on real data
6. **Re-train on real data** - See actual performance

### Week 3
7. **Add betting market baseline** - Know what we need to beat
8. **Run full backtest** - Validate on historical data
9. **Identify remaining gaps** - What's still missing?

---

## Resource Requirements

### Data Sources (Cost)
- NHL API: Free
- Natural Stat Trick: Free (with scraping)
- Money Puck: Free (with scraping)
- Elite Prospects: ~$100/year (API)
- Betting odds historical: ~$200 (one-time)

### Compute
- Daily refresh: Minimal (any laptop)
- Full backtest: 1-2 hours on modern machine
- Monte Carlo (100K sims): ~5 minutes

### Time Investment
- Phase 1-2: 2-3 weeks focused work
- Phase 3-4: 2 weeks
- Phase 5-7: 2-3 weeks
- Total: 6-8 weeks to full superhuman system

---

## Risk Factors

| Risk | Mitigation |
|------|------------|
| NHL API changes | Abstract data layer, cache aggressively |
| Overfitting to historical data | Strict temporal cross-validation |
| Market already efficient | Focus on edge cases, injuries, momentum |
| Data quality issues | Validation checks, multiple sources |
| Model complexity → bugs | Extensive testing, ablation studies |

---

## Conclusion

The current model is a solid foundation but far from superhuman. The path forward requires:

1. **Real data** - Synthetic data is the #1 limitation
2. **More signals** - Player-level, momentum, market data
3. **Better validation** - Prove we beat Vegas
4. **Production quality** - Real-time updates, accessible outputs

With 6-8 weeks of focused work, we can build a model that genuinely outperforms existing public predictions and provides actionable insights for playoff and Cup forecasting.

**The goal is not just accuracy - it's being demonstrably, measurably better than every alternative.**
