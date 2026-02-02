# NHL Framework V7.1 - Quick Reference Guide

**Version:** 7.1 | **Last Updated:** January 25, 2026

---

## One-Page Rapid Assessment

### Step 1: Check Tier Classification

| Tier | Composite Score | Historical Win Rate |
|------|-----------------|---------------------|
| **Elite Contender** | 85+ | 35% of Cup winners |
| **Strong Contender** | 75-84 | 45% of Cup winners |
| **Fringe Contender** | 65-74 | 15% of Cup winners |
| **Longshot** | 55-64 | 4% of Cup winners |
| **Non-Contender** | <55 | <1% of Cup winners |

**Quick Rule:** 80% of Cup winners score 75+ by trade deadline.

---

### Step 2: Check "Must-Have" Metrics

A true contender needs **at least 3 of 4**:

| Metric | Threshold | Why It Matters |
|--------|-----------|----------------|
| GSAx | Top 10 (>+5.0) | Goaltending wins playoffs |
| HDCF% | >52% | Quality chances = goals |
| Road Record | >.500 | Must win away from home |
| PK% | >80% | Discipline in tight games |

**Quick Rule:** Teams missing 2+ fail in Conference Finals 85% of time.

---

### Step 3: Betting Value Assessment

#### Calculate Edge
```
Edge% = Model Probability - Implied Probability

Implied Prob (positive odds): 100 / (Odds + 100)
Implied Prob (negative odds): |Odds| / (|Odds| + 100)
```

#### Value Thresholds
| Edge | Action |
|------|--------|
| >10% | Strong bet (Full Kelly/4) |
| 5-10% | Standard bet (Half Kelly/4) |
| 2-5% | Small bet (Quarter Kelly/4) |
| <2% | Pass |

#### Quick Kelly Sizing
```
Bet Size = Bankroll × (Edge% / Decimal Odds) × 0.25
```

**Example:** $10,000 bankroll, 12% edge, +800 odds
- Kelly = (0.12 / 8.0) × 0.25 = 0.375%
- Bet = $10,000 × 0.00375 = **$37.50**

---

### Step 4: Red Flags (Automatic Downgrades)

| Red Flag | Impact |
|----------|--------|
| Starter GSAx < 0 | -10 pts from composite |
| Road record <.400 | -5 pts |
| PDO > 103 | Regression coming |
| Key injury (top-6 F, top-4 D, starter G) | Manual review required |
| Presidents' Trophy winner | Track record: 3/11 recent Cups |

---

### Step 5: Conference Path Multiplier

| Path Difficulty | Multiplier | Apply When |
|-----------------|------------|------------|
| Brutal | 0.90x | Faces 2+ Elite teams before Finals |
| Hard | 0.95x | Faces 1 Elite + 1 Strong |
| Average | 1.00x | Standard bracket |
| Favorable | 1.05x | Avoids top seeds until Finals |
| Easy | 1.10x | Weak division/wild card path |

---

## V7.1 Weight Summary

| Category | Metrics | Total Weight |
|----------|---------|--------------|
| **Quality Chances** | HDCF%, xGD, xGA | 29% |
| **Goaltending** | GSAx, 30-Day GSAx, HD SV%, Backup | 11% |
| **Special Teams** | PP%, PK% | 14% |
| **Results** | GD, GA, Form | 16% |
| **Roster** | Depth, Star Power, Clutch | 13% |
| **Situational** | Road, CF%, Faceoffs | 9% |
| **Sustainability** | Variance, PDO, Coaching | 7% |
| **Total** | | **100%** |

---

## Historical Champion Profile

**Median Stanley Cup Winner (2015-2024):**
- Composite Score: 78.5
- Regular Season: 105 points
- Road Record: 22-15-4 (.585)
- GSAx: +8.2
- HDCF%: 53.1%
- PK%: 82.4%

**Key Insight:** 9/10 winners ranked Top 8 in at least one of: GSAx, HDCF%, or Road Record.

---

## Pre-Bet Checklist

Before placing any futures bet:

- [ ] Data refreshed within 24 hours
- [ ] Odds are current (just checked)
- [ ] Edge% > 5% minimum
- [ ] No disqualifying injuries
- [ ] CLV tracking shows positive history
- [ ] Bet size within Kelly limits
- [ ] Total exposure < 10% of bankroll

---

## Quick Formulas

**Sigmoid Score:**
```
Score = 100 / (1 + e^(-k × (Value - Midpoint)))
```

**Composite Score:**
```
Composite = Σ (Metric_Score × Weight)
```

**Win Probability (Head-to-Head):**
```
P(A wins) = Score_A / (Score_A + Score_B) × Adjustments
```

**Confidence Interval (90%):**
```
CI = ±1.645 × √(p × (1-p) / n)
```
Where n = 100,000 simulations

---

## Data Source Quick Links

| Data | Source | Refresh |
|------|--------|---------|
| Standings | api-web.nhle.com | Daily |
| xG/GSAx | moneypuck.com/data.htm | 3x/week |
| HDCF%/CF% | naturalstattrick.com | Weekly |
| Injuries | dailyfaceoff.com | Daily |
| Odds | Your sportsbook | Before betting |

---

## Emergency Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| Composite looks wrong | Check weights sum to 100% |
| GSAx missing | Use MoneyPuck goalie table |
| HDCF% = 50% | NST data failed; use MoneyPuck HD metrics |
| Kelly returns negative | Edge is negative; don't bet |
| Probability > 100% | Check home ice soft cap formula |

---

*Quick Reference V7.1 | For full methodology, see Framework_Methodology_V7.1.md*
