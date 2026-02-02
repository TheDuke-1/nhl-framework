
================================================================================
NHL CHAMPIONSHIP PREDICTION MODEL - COMPREHENSIVE EVIDENCE ANALYSIS
================================================================================
Generated: 2026-01-30 14:28

================================================================================
PART 1: MODEL EVOLUTION HISTORY - WHY METRICS WERE CHANGED
================================================================================

VERSION TIMELINE:
-----------------
V3.1 (Baseline)  → V4.0 (Major Overhaul) → V7.0 (Production) → V7.1 → V7.2

KEY CHANGES AND RATIONALE:

V3.1 → V4.0:
  - GSAx: 5% → 10% (doubled based on observing goalie-driven Cup wins)
  - PP%: 0% → 6% (added - was completely missing)
  - Implemented sigmoid scoring (eliminated arbitrary tier cliffs)
  - Performance: AUC improved 0.72 → 0.83

V4.0 → V7.1:
  - Major restructuring to 100% weight system
  - Added 16+ metrics including: road performance, faceoffs, depth, coaching
  - CF% reduced: 5% → 2% (deemed redundant with HDCF%)
  - Added 30-day rolling GSAx (to catch mid-season goalie emergence like STL 2019)

V7.1 → V7.2 (CURRENT):
  - GSAx: 15% → 20% (anecdotal belief goaltending wins Cups)
  - CF%: 20% → 15% (belief possession is overrated)
  - PK%: 10% → 13% (playoff importance assumption)
  - PDO: 15% → 12% (luck regresses assumption)

PROBLEM: Changes were made based on ASSUMPTIONS, not EVIDENCE.

================================================================================
PART 2: BACKTEST EVIDENCE - WHAT THE DATA ACTUALLY SHOWS
================================================================================

INDIVIDUAL METRIC PREDICTIVE POWER (10 seasons, 85 playoff teams):
------------------------------------------------------------------

Metric      Avg Winner Rank    Top-5 Rate    Winner-Elite Rate*
--------------------------------------------------------------
PP%              4.0              70%              60%  ← BEST
GSAx             4.2              80%              40%
PDO              4.1              90%              N/A
Points           4.3              60%              40%
HDCF%            4.7              70%              20%  ← OVERWEIGHTED
CF%              4.8              60%              20%  ← OVERWEIGHTED
PK%              4.8              60%              20%  ← OVERWEIGHTED

*Winner-Elite Rate = % of Cup winners who ranked top-25% in that metric

CORRELATION WITH PLAYOFF SUCCESS:
---------------------------------
CRITICAL FINDING: NO metric shows strong correlation (|r| > 0.2) with
playoff success among playoff teams.

This means: Among teams that MAKE the playoffs, analytics alone
do NOT reliably predict who wins the Cup.

CUP WINNER PROFILE (Average across 10 winners):
-----------------------------------------------
  HDCF%:  51.0% (Range: 48.8-54.5) - Often just above average
  CF%:    51.9% (Range: 49.5-55.8) - Often just above average
  GSAx:   10.8  (Range: 5.2-18.2)  - Wide variance!
  PP%:    22.4% (Range: 18.5-25.8) - Consistently above average
  PK%:    82.2% (Range: 80.1-85.8) - Consistently good
  PDO:    101.1 (Range: 100.2-102.5) - Sustainable, not fluky

================================================================================
PART 3: EVIDENCE-BASED WEIGHT RECOMMENDATIONS
================================================================================

CURRENT V7.2 vs EVIDENCE-BASED WEIGHTS:
---------------------------------------

Metric     V7.2 Weight    Evidence Says    Recommended    Rationale
------------------------------------------------------------------------
PP%           15%         60% elite rate      25%        Most consistent winner trait
GSAx          20%         40% elite rate      20%        Keep - high variance but impactful
PDO           12%         90% top-5 rate      15%        Sustainability matters more
HDCF%         25%         20% elite rate      15%        REDUCE - overweighted
CF%           15%         20% elite rate      10%        REDUCE - overweighted
PK%           13%         20% elite rate      10%        REDUCE - less predictive
Points        N/A         40% elite rate       5%        ADD - regular season success

PROPOSED EVIDENCE-BASED FORMULA (V8.0):
---------------------------------------
  PP%:    25% - Cup winners consistently elite in power play
  GSAx:   20% - Goaltending wins Cups (hot goalie phenomenon)
  PDO:    15% - Sustainable success indicator
  HDCF%:  15% - Quality chances still matter
  CF%:    10% - Possession has diminishing returns
  PK%:    10% - Important but not differentiating
  Points:  5% - Regular season validation

================================================================================
PART 4: WHAT THE MODEL MISSES - IMPROVEMENT OPPORTUNITIES
================================================================================

1. PLAYOFF-SPECIFIC FACTORS (not currently tracked):
   - Playoff experience (teams with recent Cup runs win more)
   - Playoff goaltender performance (regular season GSAx ≠ playoff GSAx)
   - Coach playoff experience and adjustments
   - Road playoff record (all Cup winners have winning road records)

2. TIMING-BASED FACTORS:
   - Trade deadline acquisitions
   - Injury returns (McDavid returning, etc.)
   - Hot streaks entering playoffs (last 20 games > season average)

3. MATCHUP-SPECIFIC FACTORS:
   - Head-to-head season series
   - Style matchups (possession vs counter-attack)
   - Goaltender vs specific team history

4. INTANGIBLES (hard to quantify):
   - Captain leadership (Ovechkin 2018)
   - "Championship DNA" (back-to-back winners)
   - Desperation factor (teams with aging cores)

================================================================================
PART 5: ACTION ITEMS FOR MODEL IMPROVEMENT
================================================================================

IMMEDIATE (V8.0):
1. □ Rebalance weights based on evidence (PP% up, HDCF%/CF% down)
2. □ Add playoff experience factor (+5% for recent Cup Final appearances)
3. □ Track last-20-games momentum separately from season averages
4. □ Add "sustainability score" based on PDO and shot quality

DATA COLLECTION NEEDED:
5. □ Historical playoff-specific GSAx (different from regular season)
6. □ Coach playoff records (currently incomplete)
7. □ Trade deadline impact tracking
8. □ Road playoff performance history

MODEL STRUCTURE CHANGES:
9. □ Separate "Make Playoffs" model from "Win Cup" model
10. □ Implement playoff bracket simulation with matchup adjustments
11. □ Add confidence intervals to all predictions
12. □ Create ensemble model with multiple weight configurations

VALIDATION IMPROVEMENTS:
13. □ Expand historical data to ALL playoff teams (not just 6-16)
14. □ Cross-validate with out-of-sample testing
15. □ Track and publish model calibration metrics
16. □ Implement rolling backtest (predict next season, validate)

================================================================================
CONCLUSION
================================================================================

The current model achieves 70% top-5 accuracy for Cup winners, which is
actually quite good given the inherent unpredictability of playoff hockey.

However, the weight distribution does NOT match the evidence:
- PP% is the most reliable Cup winner trait but is underweighted
- HDCF% and CF% are overweighted relative to their predictive power
- Playoff-specific factors are missing entirely

The model should be REFOCUSED:
1. For PLAYOFF QUALIFICATION: Current possession metrics work well
2. For CUP PREDICTION: Emphasize PP%, goaltending, sustainability

Key Insight: "The best regular season team rarely wins the Cup."
             Our model should reflect this reality.

================================================================================
