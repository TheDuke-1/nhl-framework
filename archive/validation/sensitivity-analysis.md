# NHL Championship Framework V4.0 - Sensitivity Analysis

## Overview

This document analyzes which metrics have the largest impact on team rankings and identifies teams with "fragile" predictions that are sensitive to small weight changes.

## Methodology

Each metric weight was tested with ±10% adjustments (e.g., HDCF% at 12% was tested at 10.8% and 13.2%) while keeping other weights normalized. Impact was measured by:
1. Change in top-10 team composition
2. Rank position shifts for individual teams
3. Tier boundary movements

---

## Metric Sensitivity Rankings

### High Impact (>3 rank positions shift on average)

| Metric | Weight | Sensitivity | Impact on Predictions |
|--------|--------|-------------|----------------------|
| **HDCF%** | 12% | Very High | +10% weight moves 2-3 teams in/out of top 10 |
| **GSAx** | 10% | Very High | Goaltending-heavy teams shift 4-5 positions |
| **xGD** | 11% | High | Process-oriented teams shift 2-3 positions |

**Analysis**: These three metrics account for 33% of total weight and drive most ranking variance. Teams that excel in one but not others are most sensitive to weight changes.

### Medium Impact (1-3 rank positions shift)

| Metric | Weight | Sensitivity | Impact on Predictions |
|--------|--------|-------------|----------------------|
| **xGA** | 10% | Medium | Defensive teams shift 1-2 positions |
| **Form** | 7% | Medium | Hot/cold teams swing noticeably |
| **PK%** | 8% | Medium | Special teams specialists affected |
| **PP%** | 6% | Medium-Low | Power play teams shift 1 position |

### Low Impact (<1 rank position shift)

| Metric | Weight | Sensitivity | Impact on Predictions |
|--------|--------|-------------|----------------------|
| **Depth** | 6% | Low | Minimal impact on rankings |
| **CF%** | 5% | Low | Correlated with HDCF%, redundant |
| **PDO** | 4% | Low | Uncertainty indicator, not ranking driver |
| **Star Power** | 5% | Low | Binary metric, fixed impact |
| **GD** | 3% | Very Low | Mostly captured by xGD |
| **GA** | 4% | Low | Captured by xGA |
| **Weight** | 4% | Very Low | Minimal ranking impact |
| **Playoff Variance** | 5% | Low | Consistency bonus, stable |

---

## Team Sensitivity Profiles

### Most Fragile Predictions (High Sensitivity)

These teams have rankings that could shift significantly with small methodology changes:

| Team | Current Rank | Risk Factor | Sensitivity Score |
|------|--------------|-------------|-------------------|
| **TB** | 6 | High HDCF%, Elite GSAx, Low xGA | 8.2/10 |
| **NYR** | 11 | Star-dependent, volatile GSAx | 7.8/10 |
| **DAL** | 5 | High Form boost, average analytics | 7.5/10 |
| **VGK** | 9 | Balanced but near tier boundary | 7.2/10 |
| **EDM** | 15 | Star power carrying analytics gaps | 7.0/10 |

**What "fragile" means**: These teams could move ±3-5 positions if weight methodology changes or if their key strength metric (e.g., GSAx) regresses slightly.

### Most Robust Predictions (Low Sensitivity)

These teams have rankings that remain stable across methodology variations:

| Team | Current Rank | Stability Factor | Sensitivity Score |
|------|--------------|------------------|-------------------|
| **COL** | 1 | Elite in all categories | 1.5/10 |
| **CAR** | 2 | Balanced excellence | 2.0/10 |
| **NJ** | 3 | Strong across metrics | 2.3/10 |
| **FLA** | 7 | Consistent contender profile | 2.8/10 |
| **CGY** | 32 | Consistently weak | 1.8/10 |

**What "robust" means**: These teams would remain within ±1-2 positions regardless of reasonable weight adjustments.

---

## Tier Boundary Sensitivity

### Elite/Contender Boundary (73 points)

Teams within 5 points of boundary are most sensitive to tier classification:

| Team | Score | Distance to Boundary | Sensitivity |
|------|-------|---------------------|-------------|
| WSH | 71 | +2 to Elite | High |
| PIT | 72 | +1 to Elite | Very High |
| OTT | 69 | +4 to Elite | Medium |

### Contender/Bubble Boundary (56 points)

| Team | Score | Distance to Boundary | Sensitivity |
|------|-------|---------------------|-------------|
| NYI | 58 | +2 to Bubble | High |
| PHI | 57 | +1 to Bubble | Very High |
| CHI | 55 | -1 to Contender | Very High |

---

## Weight Correlation Analysis

### Positive Correlations (weights reinforce each other)
- HDCF% ↔ xGD: r = 0.72 (teams good at one tend to be good at other)
- xGA ↔ GSAx: r = 0.58 (good defense helps goalie stats)
- Form ↔ PDO: r = 0.45 (hot teams have elevated PDO)

### Negative Correlations (weights offset each other)
- PDO ↔ xGD: r = -0.31 (lucky teams may have poor underlying numbers)
- Weight ↔ CF%: r = -0.22 (heavier teams often lower possession)

### Independence (minimal correlation)
- Star Power ↔ GSAx: r = 0.08 (star skaters don't predict goalie performance)
- Depth ↔ Form: r = 0.12 (depth doesn't strongly predict hot streaks)

---

## Recommendations

### 1. Monitor Fragile Predictions
Add sensitivity indicator to team cards in UI:
- **Green (Robust)**: Sensitivity score < 3/10
- **Yellow (Moderate)**: Sensitivity score 3-6/10
- **Red (Fragile)**: Sensitivity score > 6/10

### 2. Weight Adjustment Guidelines
If considering weight changes:
- ±10% on HDCF%/GSAx/xGD: Expect 2-4 rank shuffles
- ±10% on medium-impact metrics: Expect 1-2 rank shuffles
- ±10% on low-impact metrics: Minimal change expected

### 3. Tier Boundary Buffer
For teams within 3 points of tier boundaries:
- Report both tiers in analysis (e.g., "Contender, near-Elite")
- Use confidence intervals to express uncertainty

### 4. Diversification Value
Teams with balanced profiles (low variance across metrics) are more reliable predictions than teams with extreme strengths/weaknesses.

---

## Key Takeaways

1. **33% of weight drives most variance**: HDCF%, GSAx, and xGD together determine ranking stability
2. **Goaltending is now properly weighted**: 10% GSAx creates appropriate sensitivity to goalie performance
3. **~20% of teams are "fragile"**: Their rankings could shift significantly with methodology changes
4. **~30% of teams are "robust"**: Elite and bottom-tier teams are stable regardless of weight changes
5. **Tier boundaries matter**: Teams near 73 and 56 points have highest classification uncertainty

---

*Last Updated: January 20, 2026*
*Framework Version: V4.0*
