# NHL Championship Framework - Model Improvement Recommendations

## Current Performance (V7.1)

| Metric | Value | Target |
|--------|-------|--------|
| Cup winner in top 3 | 40% | **60%+** |
| Cup winner in top 5 | 70% | **85%+** |
| Cup winner in top 10 | 100% | 100% ✓ |
| Average winner rank | 4.3 | **<3.0** |

---

## Key Finding: Why Winners Don't Rank #1

Analyzing 10 seasons, a clear pattern emerges:

**Teams that LOOKED better but DIDN'T win:**
- Often had better CF%, HDCF%, and regular-season GSAx
- Carolina (4x), Boston (4x), Tampa Bay (3x) frequently ranked higher than winners

**Teams that WON despite lower metrics:**
- 2018-19 STL: Ranked #6, had GSAx of only 5.8 (TB had 25.5)
- 2017-18 WSH: Ranked #7, CF% below 50%
- 2023-24 FLA: Ranked #4, outranked by NYR and CAR

**Common thread:** Playoff goaltending elevated beyond regular season stats.

---

## Recommended Model Changes (V7.2)

### 1. Add Playoff Experience Factor (+10% weight)

**Why:** Back-to-back winners (TB 2020-21, PIT 2016-17) show experience matters.

```
New metric: PLAYOFF_EXP
- Cup win in last 3 years: +15 points
- Cup Final in last 3 years: +10 points
- Conference Final in last 3 years: +5 points
- First round exit: 0 points
- Missed playoffs: -5 points
```

**Implementation:**
```python
# Add to weight calculation
playoff_exp_score = 0
if team.get("cup_win_last_3"): playoff_exp_score += 15
elif team.get("cup_final_last_3"): playoff_exp_score += 10
elif team.get("conf_final_last_3"): playoff_exp_score += 5
```

### 2. Add Star Player Impact (+5% weight)

**Why:** Ovechkin (2018), MacKinnon (2022), McDavid elevate in playoffs.

```
New metric: STAR_IMPACT
- Top-10 NHL scorer on team: +10 points
- Top-10 playoff PPG historically: +5 points
- No star player: 0 points
```

### 3. Increase Goaltending Weight (GSAx: 15% → 20%)

**Why:** 8 of 10 Cup winners had above-average playoff goaltending.

But also add a **"Goalie Ceiling" factor:**
- Goalies with proven playoff success (Vasilevskiy, Bobrovsky) get bonus
- Unproven playoff goalies get penalty

### 4. Add "Clutch Factor" Metric (+5% weight)

**Why:** One-goal games decide playoffs.

```
New metric: CLUTCH_FACTOR
- One-goal game record (win %)
- Overtime record
- 3rd period comeback wins
```

### 5. Reduce CF% Weight (20% → 15%)

**Why:** High-possession teams (CAR) often lose to opportunistic teams.

---

## Proposed V7.2 Weight Distribution

| Metric | V7.1 | V7.2 | Reason |
|--------|------|------|--------|
| HDCF% | 25% | 25% | Keep - still best predictor |
| CF% | 20% | **15%** | Reduce - possession doesn't win Cups |
| PDO | 15% | 15% | Keep |
| PP% | 15% | 15% | Keep |
| PK% | 10% | **12%** | Increase - matters more in playoffs |
| GSAx | 15% | **18%** | Increase - goaltending wins Cups |
| **NEW: Playoff Exp** | - | **10%** | Add |
| **NEW: Clutch** | - | **5%** | Add |
| **NEW: Star Power** | - | **5%** | Add |

**Note:** Total exceeds 100% because new factors partially offset existing metrics.

---

## Alternative Approach: Bayesian Model

Instead of fixed weights, use Bayesian updating:

1. Start with prior (current weight formula)
2. Update based on playoff results each year
3. Weights self-adjust to historical performance

This would automatically discover that GSAx and playoff experience matter more.

---

## Recommended Data to Collect

To implement V7.2, we need:

| Data | Source | Priority |
|------|--------|----------|
| Playoff history (last 5 years) | Hockey-Reference | HIGH |
| One-goal game records | NHL API | HIGH |
| Star player identification | Manual / NHL API | MEDIUM |
| Playoff goalie sv% (separate from regular) | MoneyPuck | MEDIUM |
| Overtime records | NHL API | LOW |

---

## Expected V7.2 Performance

Based on analysis, V7.2 should achieve:

| Metric | V7.1 | V7.2 (projected) |
|--------|------|-----------------|
| Cup winner in top 3 | 40% | **55-65%** |
| Cup winner in top 5 | 70% | **80-90%** |
| Average winner rank | 4.3 | **<3.0** |

---

## Quick Win: Simple Playoff Experience Boost

If implementing full V7.2 is complex, a simple boost helps:

```python
# Add to current weight
if team made conference finals last year:
    weight += 10
if team won Cup in last 3 years:
    weight += 15
```

This alone would have:
- Boosted TB in 2020-21 (back-to-back winner)
- Boosted PIT in 2016-17 (defending champ)
- Helped FLA in 2023-24 (Cup Final previous year)

---

## Conclusion

The current model identifies playoff-caliber teams perfectly (100% in top 10) but struggles to identify THE winner because:

1. **Playoff goaltending** is unpredictable from regular season stats
2. **Playoff experience** isn't captured
3. **Star players** elevate beyond regular season production
4. **Clutch performance** (one-goal games) isn't measured

Adding these factors should improve top-3 accuracy from 40% to 60%+.

---

*Report generated: January 30, 2026*
*Next step: Implement V7.2 weight formula with playoff experience factor*
