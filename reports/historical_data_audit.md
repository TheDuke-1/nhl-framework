# Historical Data Audit Report

**Date:** February 1, 2026
**Auditor:** Claude Code
**Verdict: Nearly all historical data is AI-generated and unreliable.**

---

## Methodology

Cross-referenced CSV files in `data/historical/` against verified data from Hockey-Reference.com for the 2023-24, 2022-23, 2024-25, and 2009-10 seasons. Checked standings (W/L/OTL/PTS/GF/GA), advanced stats, Vegas odds, and clutch performance data.

---

## Findings by File Type

### 1. Standings CSVs (standings_YYYY.csv) — PARTIALLY FABRICATED

**W/L/OTL/PTS:** Approximately correct for most teams. Usually within 1-3 of real values. Some are exact.

**GF/GA:** Consistently wrong. Off by 10-50 goals per team. This is the clearest indicator of AI fabrication — the model gets the general shape right but invents the specific numbers.

#### Examples — 2023-24 Season (standings_2024.csv vs Hockey Reference)

| Team | Stat | CSV Value | Real Value | Error |
|------|------|-----------|------------|-------|
| FLA | GF | 259 | 268 | -9 |
| NYR | GF | 266 | 282 | -16 |
| NYR | GA | 202 | 229 | -27 |
| BOS | GF | 257 | 267 | -10 |
| BOS | GA | 212 | 224 | -12 |
| TOR | GF | 282 | 303 | -21 |
| TOR | GA | 248 | 263 | -15 |
| COL | GF | 287 | 304 | -17 |
| COL | GA | 229 | 254 | -25 |
| CAR | GA | 213 | 216 | -3 |
| WPG | GF | 254 | 259 | -5 |
| DAL | GF | 298 | 298 | 0 (lucky match) |

#### Examples — 2022-23 Season (standings_2023.csv vs Hockey Reference)

| Team | Stat | CSV Value | Real Value | Error |
|------|------|-----------|------------|-------|
| BOS | GF | 326 | 305 | +21 |
| CAR | GA | 197 | 213 | -16 |
| VGK | GA | 216 | 229 | -13 |
| EDM | GF | 318 | 325 | -7 |
| FLA | GF | 271 | 290 | -19 |
| BUF | GF | 301 | 296 | +5 |

#### Examples — 2009-10 Season (standings_2010.csv vs Hockey Reference)

| Team | Stat | CSV Value | Real Value | Error |
|------|------|-----------|------------|-------|
| WSH | W | 41 | 54 | -13 (MAJOR) |
| WSH | PTS | 95 | 121 | -26 (MAJOR) |
| CHI | W | 48 | 52 | -4 |
| CHI | PTS | 107 | 112 | -5 |
| PIT | W | 51 | 47 | +4 |
| PIT | PTS | 116 | 101 | +15 (MAJOR) |
| DET | W | 48 | 44 | +4 |
| DET | GA | 256 | 233 | +23 |

**Older seasons are worse.** The 2010 data has major errors (Washington off by 26 points). More recent seasons are closer but still fabricated.

### 2. Advanced Stats CSVs (advanced_YYYY.csv) — FABRICATED

**Red flags:**
- Data is suspiciously smooth and follows predictable patterns correlated with team quality
- GSAx values exist for 2010 — but expected goals models weren't publicly available until ~2015-2016
- xGF/xGA values exist for 2010 — same problem, xG models didn't exist in this form
- CF% values are plausible but unverifiable without cross-referencing Natural Stat Trick (which only goes back to 2007-08 with incomplete early data)
- Every value has exactly 1-2 decimal places with no messy real-world data patterns

**Specific issues:**
- 2010: Contains xgf, xga, xgf_pct, hdcf_pct, gsax — none of these metrics were publicly tracked in 2010
- 2015: Uses team codes TBL, LAK, SJS, NJD — inconsistent with the rest of the project which uses TB, LA, SJ, NJ
- Values like shooting_pct and save_pct are reasonable ranges but don't match any real source

### 3. Vegas Odds CSVs (vegas_odds_YYYY.csv) — LIKELY FABRICATED

**Red flags:**
- Implied probabilities are suspiciously round and follow a too-clean distribution
- Real preseason odds are messier with different lines from different books
- The ranking order is generally reasonable (favorites are right) but the specific odds values appear invented
- `actual_made_playoffs` and `actual_won_cup` fields are mostly correct (easy to verify)

**Partially useful:** The `actual_made_playoffs` and `actual_won_cup` columns appear accurate and could be kept as reference for which teams made playoffs each year.

### 4. Clutch CSVs (clutch_YYYY.csv) — FABRICATED

**Red flags:**
- Data follows an extremely predictable pattern where good teams have good clutch stats and bad teams have bad clutch stats
- Real clutch data has much more variance (bad teams can be clutch, good teams can collapse in close games)
- Numbers are suspiciously consistent across categories (a team with X one-goal wins always has proportional comeback wins)
- This data structure doesn't match any known public data source

### 5. compiled_historical.json — FABRICATED

- Claims sources are "MoneyPuck, Natural Stat Trick, Hockey-Reference" but data doesn't match any of them
- Contains only 7-10 teams per season (not all 30-32)
- Points values are approximately correct; advanced stats are invented
- Same issues as the individual CSVs

### 6. stats_2023_24.json — FABRICATED

- Contains the same data as the 2023-24 entry in compiled_historical.json
- Same fabricated advanced stats

---

## Additional Structural Issues

| Issue | Details |
|-------|---------|
| **WPG in 2010** | Winnipeg Jets didn't exist in 2009-10 (Atlanta Thrashers moved in 2011). Should be ATL. |
| **SEA in 2020** | Seattle Kraken listed with 0 games in 2019-20. They didn't join until 2021-22. Entry should be removed. |
| **UTA in 2024** | Listed correctly — the Arizona Coyotes became Utah Hockey Club for 2024-25. But the CSV uses UTA for 2023-24 when they were still ARI. |
| **Inconsistent team codes** | 2015 uses TBL/LAK/SJS/NJD while other years use TB/LA/SJ/NJ |
| **Missing teams in compiled_historical.json** | Only 7-16 teams per season instead of all 30-32 |

---

## What Can Be Salvaged

| Data | Salvageable? | Notes |
|------|-------------|-------|
| W/L/OTL/PTS (recent seasons) | Partially | 2020-2024 are close but still have errors. Must be replaced. |
| GF/GA | No | Consistently wrong across all seasons. |
| Advanced stats (CF%, HDCF%, xG, GSAx) | No | All appear fabricated. |
| Vegas odds | No | Odds values are fabricated. Playoff/Cup winner flags may be correct. |
| Clutch data | No | Entirely fabricated. |
| Cup winners/finalists | Yes | These are verifiable facts and appear correct. |
| Made playoffs flags | Mostly | A few errors (e.g., 2020 used 24-team format) but generally correct. |

---

## Recommendation

**Replace all historical data.** The existing files should be moved to `archive/data_historical_unverified/` and replaced with data scraped from authoritative sources:

1. **Hockey-Reference.com** — Standings, GF/GA, W/L/OTL/PTS (all seasons)
2. **Natural Stat Trick** — CF%, HDCF%, PDO (2007-08 onwards, reliable from ~2013)
3. **MoneyPuck** — xG, GSAx (2015-16 onwards)
4. **Evolving Hockey** — Cross-reference for advanced stats
5. **Cup/playoff results** — Wikipedia or Hockey-Reference (easy to verify)

For pre-2015 seasons, some advanced metrics simply don't exist in public form. The model should be honest about data availability rather than using fabricated values.

---

## Impact on Superhuman Model

The Superhuman ML model was trained on this fabricated data. This means:
- **All learned feature weights are unreliable** — they're fitting noise, not real patterns
- **Backtest results are meaningless** — testing on the same fabricated data you trained on
- **The model needs complete retraining** once real data is available
- **Current predictions should be treated with low confidence**

This is the single most important thing to fix in the project.
