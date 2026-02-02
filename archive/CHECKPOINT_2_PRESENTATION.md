# CHECKPOINT 2: Phase 2 Draft Structure Review

**Date:** January 26, 2026
**Status:** Ready for Review

---

## Deliverables Completed

| Deliverable | Status | Location |
|-------------|--------|----------|
| Master Spreadsheet | ✅ Structure Complete | `NHL_Framework_V7.1_Master.xlsx` |
| Methodology Documentation | ✅ Complete | `Framework_Methodology_V7.1.md` |
| Data Refresh Protocol | ✅ Complete | `Data_Refresh_Protocol.md` |
| Quick Reference Guide | ✅ Complete | `Quick_Reference_V7.1.md` |
| Backtest Results | ✅ Complete | `Backtest_Results_V7.1.md` |

---

## 1. Spreadsheet Structure Review

### Tabs Created (9 Total)

| Tab | Purpose | Status |
|-----|---------|--------|
| Team Rankings | All 32 teams, all metrics, weighted composite | Headers + 5 sample teams |
| Data Input | Raw data entry, timestamps, configuration | Structure complete |
| Road Performance | Road splits and calculations | Headers + structure |
| Goaltending Detail | GSAx integration components | Headers + sub-weights |
| Playoff Probability | 16-team bracket by conference | Structure with E1-E8, W1-W8 |
| Cup Probability | Monte Carlo output with CI | Top 10 template |
| Betting Dashboard | Edge calculation, Kelly sizing, CLV tracking | Full formulas |
| Historical Benchmarks | 2015-2025 champions | 10 champions populated |
| Formulas Reference | All calculations documented | Complete |

### Sample Population

5 teams populated as examples:
1. Colorado Avalanche (COL)
2. Carolina Hurricanes (CAR)
3. Tampa Bay Lightning (TB)
4. Detroit Red Wings (DET)
5. Dallas Stars (DAL)

---

## 2. V7.1 Weight Implementation

The Team Rankings tab implements all V7.1 weights in the Raw Score formula (Column AJ):

```
Raw Score =
  HDCF% × 0.11 +    (11%)
  xGD × 0.09 +      (9%)
  xGA × 0.09 +      (9%)
  CF% × 0.02 +      (2%)
  GSAx × 0.05 +     (5% - see Goaltending Detail)
  30D_GSAx × 0.03 + (3%)
  HD_SV% × 0.02 +   (2%)
  PK% × 0.08 +      (8%)
  PP% × 0.06 +      (6%)
  GD × 0.06 +       (6%)
  GA × 0.02 +       (2%)
  Road × 0.05 +     (5% - combined from 4 components)
  Form × 0.08 +     (8%)
  Depth × 0.06 +    (6%)
  Star × 0.05 +     (5%)
  FO × 0.02 +       (2% - combined from 3 components)
  Coach × 0.03 +    (3%)
  Variance × 0.03 + (3%)
  Clutch × 0.02 +   (2%)
  PDO × 0.01        (1%)
  ─────────────────
  TOTAL = 100%
```

Composite Score = Raw Score × 10 (scaled to 0-100)

---

## 3. Goaltending Formula (Condition 3)

The Goaltending Detail tab documents the GSAx integration:

**Total Goaltending Weight: 11%**

| Component | Weight | Calculation |
|-----------|--------|-------------|
| Season GSAx | 5% | sigmoid(GSAx, k=0.15, mid=0) |
| 30-Day Rolling GSAx | 3% | sigmoid(30D_GSAx, k=0.2, mid=0) |
| HD Save% | 2% | (HD_SV% - 0.80) × 20 |
| Backup Bonus | 1% | IF backup_GSAx > 0 THEN min(0.5, backup_GSAx/10) |

**Conditional Logic:**
- If starter games < 30: Season GSAx weight reduced to 3%, difference added to rolling
- If starter injured: Backup becomes primary, backup bonus = 0

---

## 4. Kelly Formula Verification

The Betting Dashboard includes a verification section (Rows 21-26):

**Test Case:** 12% model probability, +800 American odds

| Step | Formula | Result |
|------|---------|--------|
| Decimal Odds | 800/100 + 1 | 9 |
| Full Kelly% | ((9 × 0.12) - (1 - 0.12)) / (9 - 1) × 100 | 1.0% |
| Quarter Kelly% | 1.0% × 0.25 | 0.25% |
| Bet on $10,000 | 0.25% × $10,000 | **$25.00** |

**Verification:** ✅ Matches the worked example from Audit V2 ($25 at 12%/+800)

The spreadsheet formula in Column F:
```excel
=IF(C9=0,0,IF(C9>0,
  ((((C9/100)+1)*(B9/100))-(1-B9/100))/((C9/100)),
  ((((100/ABS(C9))+1)*(B9/100))-(1-B9/100))/((100/ABS(C9)))
))*100
```

This handles both positive and negative American odds correctly.

---

## 5. Betting Dashboard Draft

### Sections Implemented

**A. Value Identification Table (Rows 8-18)**
- 10 team slots with input cells for Model Prob% and Odds
- Auto-calculated: Implied%, Edge%, Full Kelly%, Qtr Kelly%, Bet Size
- Value flag: YES if Edge > threshold (configurable)

**B. Kelly Verification (Rows 21-26)**
- Step-by-step calculation with formulas
- Matches documented worked example

**C. CLV Tracking Log (Rows 29-34)**
- 5 entry rows for bet tracking
- Fields: Date, Team, Market, Your Odds, Close Odds
- Auto-calculated: Your Impl%, Close Impl%, CLV%
- Manual entry: Result, P/L

**D. CLV Summary (Rows 37-41)**
- Total Bets count
- Average CLV%
- Total P/L
- Skill indicator: "YES" if avg CLV > 2%

---

## 6. Conditions Status Update

| # | Condition | Status | Location |
|---|-----------|--------|----------|
| 1 | Document backtest reconstruction limitations | ✅ Complete | Backtest_Results_V7.1.md §1.1 |
| 2 | Clarify road performance data (regular season vs playoff) | ✅ Complete | Methodology §5.2.3 - REGULAR SEASON |
| 3 | Specify GSAx integration formula | ✅ Complete | Methodology §6, Spreadsheet Goaltending Detail tab |
| 4 | Verify or remove 2019 STL claim | ✅ Verified | Methodology §8.4 with Feb 2019 data |
| 5 | Assign conference path weight/multiplier | ✅ Complete | Methodology §7 - 0.90x to 1.10x |
| 6 | Decide on Presidents' Trophy adjustment | ✅ Decided: DO NOT ADD | Methodology §8.5 with rationale |

---

## 7. Files Ready for Review

```
NHL Playoff Project/
├── NHL_Framework_V7.1_Master.xlsx    (19 KB - structure + 5 teams)
├── Framework_Methodology_V7.1.md      (24 KB - complete)
├── Data_Refresh_Protocol.md           (7 KB - complete)
├── Quick_Reference_V7.1.md            (5 KB - complete)
├── Backtest_Results_V7.1.md           (14 KB - complete)
├── Audit_Report_V2.md                 (26 KB - approved)
└── CHECKPOINT_2_PRESENTATION.md       (this file)
```

---

## 8. Pending After Approval

Upon Checkpoint 2 approval:

1. **Full Population:** Add all 32 teams to spreadsheet with current data
2. **Data Fetch:** Run data refresh from NHL API and MoneyPuck
3. **Validation:** Cross-reference 3 teams against source data
4. **Final Review:** Checkpoint 3 presentation

---

## 9. Questions for Reviewer

1. Should the 5 sample teams remain after full population, or should all teams be refreshed with live data?

2. The CLV tracking log has 5 rows - should this be expanded to 20+ for a full season?

3. The Historical Benchmarks tab includes 2024-25 FLA as a placeholder (season in progress) - should this be removed until confirmed?

---

**Checkpoint 2 Status: READY FOR REVIEW**

*Awaiting approval to proceed with full spreadsheet population.*
