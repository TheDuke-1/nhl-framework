# SPEC: NHL Playoff Framework — Model Rebuild + Dashboard

## Overview
Rebuild the prediction model on verified historical data with fully data-driven weights, then build a 6-tab dashboard with modern sports app styling. The model predicts Cup probability, playoff probability, bracket outcomes, and round-by-round advancement. The dashboard displays all of this at TheDuke-1.github.io/nhl-framework, updated daily via GitHub Actions.

---

## Requirements

### Model Rebuild
1. Scrape fresh historical data (2010-2024, 15 seasons) from ALL available sources: NHL API, Hockey Reference, Natural Stat Trick, MoneyPuck CSV downloads. Research additional reliable sources. Cross-reference all sources for accuracy.
2. Model learns all feature weights from data — no hand-tuning. Retire V7.1 manual weight system from `merge_data.py` entirely.
3. Model outputs: Cup win probability, playoff make/miss probability, projected bracket with series win probabilities, round-by-round advancement probability, conference champion probability — for all 32 teams.
4. Backtest across 2010-2024 must meet three bars: (a) demonstrate positive edge vs Vegas odds, (b) Cup winner in model's top 5 at least 70% of seasons, (c) calibrated probabilities (predicted % ≈ actual %).
5. COVID-shortened 2020 season included in training with a `shortened_season` feature flag so model can learn it behaves differently.
6. Team relocations (ARI → UTA) treated as same franchise — continuous history via config mapping.
7. Automated injury tracking from multiple sources (NHL API + DailyFaceoff + others). Cross-reference for accuracy. Impact quantified via WAR-based metric validated against historical injury impact data. Data-driven, not manual tiers.
8. Confidence intervals calculated and stored in `dashboard_data.json` but NOT displayed on dashboard.

### Dashboard
9. 6 tabs: Power Rankings, Playoff Race, Betting Value, Bracket, Model Performance, Insights.
10. Modern sports app aesthetic (The Athletic / FanDuel style). Dark mode only. Card-based layout, good whitespace.
11. Team identity: colored left border bar + full team name.
12. File structure: `index.html` loads separate CSS and JS files. No build step. Works on GitHub Pages.
13. Desktop-focused. Mobile is out of scope for now.
14. Fully public — no authentication.
15. Data freshness: timestamp in header + detailed per-source status on click/hover.
16. Glossary page (linked from footer) explaining all advanced stats in plain English.
17. Tooltips on column headers linking to glossary definitions (stretch goal — not required for launch).

### Pipeline & Automation
18. GitHub Actions runs full pipeline daily at 6 AM EST: fetch all data → train model → generate `dashboard_data.json` → commit & push.
19. If ML model fails in CI: create a GitHub issue describing the failure, do NOT commit anything. Dashboard shows last good data.
20. Weekly snapshots stored for 4-week trend tracking in Insights tab.
21. Odds pre-fetched by pipeline into `dashboard_data.json`. Dashboard also supports manual odds override input.

---

## UI/UX: Tab-by-Tab Detail

### Tab 1: Power Rankings
- All 32 teams ranked by model composite score
- Visual tier dividers separating 4 tiers: Elite, Contender, Bubble, Pretender
- Columns: Rank, Team (color bar + name), Tier, Record (W-L-OTL), Points, Cup%, Playoff%, then the model's weighted factors (whatever features the data-driven model selects as most important), Injury Impact column
- Injured players shown subtly (e.g., small text below team name or hover detail)
- Sortable by clicking column headers (ascending/descending toggle)
- Conference filter dropdown (All / Eastern / Western)
- No click-to-expand on rows (future feature)

### Tab 2: Playoff Race
- Split by conference: Eastern and Western
- Each conference shows two views:
  - **Current Standings**: actual W-L-OTL, Points, GP, Games Remaining, current division/conference rank
  - **Projected Final**: model's projected final points, projected final rank, playoff probability %
- Teams in current playoff positions visually distinguished from those outside
- Sorted by current standing within each conference

### Tab 3: Betting Value
- Two sections: Cup Futures and Make/Miss Playoffs
- Columns: Team, Model Probability, Market Odds, Implied Market Probability, Edge (model - market), Value Flag
- Value flag triggers at 5%+ positive edge (model thinks team is undervalued)
- Color coding: green rows = value bet, red rows = market overpricing the team
- Manual override input: user can paste in odds from their specific sportsbook. Overrides pre-fetched odds for edge calculation. Stored in browser localStorage so it persists across visits.

### Tab 4: Bracket
- **Default view**: model's Monte Carlo simulation results showing projected bracket and series probabilities
- Visual bracket layout matching real NHL playoff format (4 rounds, 16 teams)
- Toggle between "Projected" bracket (model predictions) and "Actual" bracket (real matchups once playoffs begin)
- **Interactive mode**: click a team to advance them. Downstream probabilities recalculate based on the user's selections.
- "Reset to Model" button restores Monte Carlo default projections
- Each matchup shows series win probability (e.g., "COL 68% — MIN 32%")

### Tab 5: Model Performance
- Summary stats at top: overall accuracy rate, Cup winner in top-5 rate, Brier score, edge vs Vegas
- Season-by-season table: Year, Model's #1 Pick, Model's Top 5, Actual Cup Winner, Was Winner in Top 5?, Model Prob for Winner, Vegas Prob for Winner, Edge
- Clear visual indicators (green checkmark / red X) for correct/incorrect predictions

### Tab 6: Insights
- News feed layout — most recent observations at top
- Auto-generated from weekly pipeline comparisons (4-week window):
  - Biggest movers (teams rising/falling in composite score)
  - New value bet alerts (teams crossing the 5% edge threshold)
  - Trend warnings (teams with declining metrics over 3+ weeks)
  - Notable stat leaders (best HDCF%, best GSAx, hottest recent form)
  - Injury alerts (significant new injuries and their estimated impact)
- Each item is 1-2 sentences with timestamp

### Header
- Project title / branding
- Tab navigation
- "Last updated: [date]" timestamp. Click to see per-source detail (NHL API ✓, MoneyPuck ✓, NST ✓, Odds ✓ with individual timestamps)

### Footer
- Link to Glossary page
- "Powered by [model name]" or similar
- Link to GitHub repo

### Glossary Page
- Separate HTML file (`glossary.html`) or section
- Plain-English definitions of all metrics: HDCF%, GSAx, CF%, PDO, xGF%, Brier score, WAR, etc.
- Organized alphabetically or by category (offense, defense, goaltending, model metrics)

---

## Data Model

### `dashboard_data.json` (generated by pipeline)
```json
{
  "metadata": {
    "generatedAt": "ISO timestamp",
    "season": "2025-26",
    "modelVersion": "2.0",
    "dataFreshness": {
      "nhl_api": { "status": "ok", "lastFetch": "ISO timestamp" },
      "moneypuck": { "status": "ok", "lastFetch": "ISO timestamp" },
      "nst": { "status": "ok", "lastFetch": "ISO timestamp" },
      "odds": { "status": "ok", "lastFetch": "ISO timestamp" },
      "injuries": { "status": "ok", "lastFetch": "ISO timestamp" }
    },
    "trainingSeasons": "2010-2024",
    "featureWeights": { "feature_name": weight, ... }
  },
  "teams": [{
    "rank": 1,
    "code": "COL",
    "name": "Colorado Avalanche",
    "conference": "West",
    "division": "Central",
    "tier": "Elite",
    "compositeScore": 92.5,
    "cupProbability": 0.152,
    "cupConfidenceInterval": [0.08, 0.22],
    "playoffProbability": 0.99,
    "conferenceProbability": 0.31,
    "record": { "w": 36, "l": 8, "otl": 9 },
    "points": 81,
    "gamesPlayed": 53,
    "gamesRemaining": 29,
    "projectedPoints": 119,
    "projectedRank": 1,
    "stats": {
      "hdcfPct": 55.29,
      "gsax": 21.22,
      "cfPct": 55.96,
      "ppPct": 15.5,
      "pkPct": 84.1,
      "pdo": 1.032,
      "xgfPct": 56.22
    },
    "injuries": {
      "totalWarLost": 2.1,
      "players": [
        { "name": "Player Name", "position": "F", "war": 2.1, "status": "IR", "returnDate": "TBD" }
      ]
    },
    "marketOdds": {
      "cupOdds": "+350",
      "cupImpliedProb": 0.222,
      "cupEdge": -0.07,
      "playoffOdds": "-5000",
      "playoffImpliedProb": 0.98,
      "playoffEdge": 0.01
    },
    "trendData": [90.1, 91.3, 92.0, 92.5]
  }],
  "bracket": {
    "projected": {
      "round1": [
        { "higher": "COL", "lower": "team2", "higherWinProb": 0.72 },
        ...
      ],
      "round2": [...],
      "confFinals": [...],
      "final": [...]
    },
    "actual": null
  },
  "roundAdvancement": {
    "COL": { "round1": 0.92, "round2": 0.68, "confFinal": 0.41, "cupFinal": 0.25, "cupWin": 0.152 },
    ...
  },
  "backtest": {
    "summary": {
      "overallAccuracy": 0.73,
      "top5Rate": 0.80,
      "brierScore": 0.042,
      "edgeVsVegas": "+2.3%"
    },
    "seasons": [{
      "year": 2024,
      "modelTop1": "FLA",
      "modelTop5": ["FLA", "COL", "DAL", "CAR", "EDM"],
      "actualWinner": "FLA",
      "winnerInTop5": true,
      "modelProbForWinner": 0.14,
      "vegasProbForWinner": 0.11,
      "edge": 0.03
    }]
  },
  "insights": [
    { "type": "mover_up", "text": "Columbus has risen 8 spots in composite rankings over the past 3 weeks (9-1-0 in last 10)", "date": "2026-02-01" },
    { "type": "value_bet", "text": "Pittsburgh now shows 5.5% edge for Cup futures — model says 5.5%, market implies 1.7%", "date": "2026-02-01" },
    { "type": "trend_warning", "text": "Toronto has dropped from 12th to 22nd in composite score. 2-6-2 in last 10.", "date": "2026-02-01" },
    { "type": "injury_alert", "text": "Key injury: [Player] out for [Team]. Estimated WAR impact: -2.1", "date": "2026-02-01" }
  ]
}
```

### Historical Training Data (`data/historical/`)
Per-season CSVs verified against multiple sources:
- `standings_{year}.csv` — W, L, OTL, PTS, GF, GA, PP%, PK%
- `advanced_{year}.csv` — CF%, HDCF%, xGF%, PDO, SCF%
- `goaltending_{year}.csv` — GSAx, SV%, HD SV%
- `playoff_history_{year}.csv` — round results, series outcomes, Cup winner
- `vegas_odds_{year}.csv` — preseason Cup futures for each team
- `injuries_{year}.csv` — significant injuries and game impact (for WAR validation)
- `players_{year}.csv` — player WAR/value metrics

### Weekly Snapshots (`data/snapshots/`)
- `snapshot_{date}.json` — composite scores and key metrics for all 32 teams
- Pipeline stores one per week, keeps last 4

---

## Implementation Plan (Build Order)

### Step 1: Scrape & Verify Historical Data
- Build scrapers for Hockey Reference, NHL API historical endpoints, NST archives, MoneyPuck CSV downloads
- Research additional reliable sources (Evolving Hockey, Corsica successors, etc.)
- Scrape all 15 seasons (2010-2024)
- Cross-reference metrics across sources. Flag discrepancies >2%.
- Output: verified CSVs in `data/historical/` replacing any existing synthetic data
- Document verification results in `reports/historical_data_audit.md`

### Step 2: Build Injury Tracking Pipeline
- Build scrapers for NHL API injury reports and DailyFaceoff
- Research player WAR/value sources (Evolving Hockey, Hockey Reference)
- Create injury impact model: WAR-based immediate estimate, validated against historical injury data
- Add to daily pipeline
- Output: injuries stored in `data/injuries.json`

### Step 3: Train & Validate Model
- Rewrite model to use verified historical data
- Fully data-driven feature selection and weighting
- Add `shortened_season` flag for 2020
- Map ARI → UTA as continuous franchise
- Implement: Cup probability, playoff probability, bracket simulation (Monte Carlo), round-by-round advancement, conference champion probability
- Run leave-one-season-out backtest for all 15 seasons
- Validate against three success bars: edge vs Vegas, top-5 accuracy ≥70%, calibrated probabilities
- Generate backtest report

### Step 4: Retire V7.1 Weights
- Remove hand-tuned weight calculation from `merge_data.py`
- All predictions flow through the retrained ML model
- Old weight system documented in `archive/` for reference

### Step 5: Update Pipeline for Full CI
- Update `update-stats.yml` to install ML dependencies (scikit-learn, numpy, scipy)
- Add model training step to daily pipeline
- Add injury fetch step
- Implement: on failure, create GitHub issue and block commit
- Add weekly snapshot storage (keep last 4)
- Generate `dashboard_data.json` matching the data contract above

### Step 6: Build Dashboard — Rankings Tab
- Create `index.html`, `css/style.css`, `js/app.js` structure
- Implement tab navigation framework
- Build Power Rankings table with tier dividers
- Add sortable columns and conference filter
- Add injury column
- Fetch and render from `dashboard_data.json`

### Step 7: Build Dashboard — Playoff Race Tab
- Current standings by conference (from data)
- Projected final standings (from model)
- Playoff line visual indicator

### Step 8: Build Dashboard — Betting Value Tab
- Cup futures and make/miss playoffs tables
- Edge calculation and value flag (5%+ threshold)
- Manual odds override input with localStorage persistence

### Step 9: Build Dashboard — Bracket Tab
- Bracket layout (4 rounds, 16 teams)
- Default: Monte Carlo projected results
- Toggle between Projected and Actual (when playoffs start)
- Click-to-advance interactive simulation with downstream recalculation
- Reset to Model button

### Step 10: Build Dashboard — Model Performance Tab
- Summary stats header
- Season-by-season backtest table
- Visual checkmarks for correct predictions

### Step 11: Build Dashboard — Insights Tab
- News feed layout
- Auto-generated from weekly snapshot comparisons
- Mover, value bet, trend warning, stat leader, and injury alert categories

### Step 12: Build Glossary & Polish
- Create glossary.html with all metric definitions
- Add header timestamp + source detail popover
- Add footer with glossary link and repo link
- Cross-browser testing
- Performance check (page load time)

### Step 13: Enable GitHub Pages
- Enable Pages in repo settings (serve from main branch root)
- Verify dashboard loads at TheDuke-1.github.io/nhl-framework
- Verify daily pipeline updates are reflected on the live site

### Step 14: Off-Season Mode
- When season ends (June), dashboard automatically shows final season results
- Last rankings, Cup winner highlighted, model accuracy for the season
- Static until next season's data starts flowing (~October)

---

## Verification Checklist

- [ ] Historical data for all 15 seasons scraped from 3+ sources and cross-referenced
- [ ] Model trains fully from data — no hand-tuned weights anywhere in codebase
- [ ] Backtest: Cup winner in top 5 for ≥70% of seasons (≥11/15)
- [ ] Backtest: model shows positive edge vs Vegas odds across the 15 seasons
- [ ] Backtest: probability calibration is reasonable (Brier score reported)
- [ ] Injury tracking pipeline fetches from 2+ sources and cross-references
- [ ] Injury impact is WAR-based and data-driven
- [ ] `dashboard_data.json` matches the data contract schema above
- [ ] All 6 dashboard tabs render correctly
- [ ] Power Rankings: sortable columns work, conference filter works, tier dividers display
- [ ] Playoff Race: shows both actual and projected standings
- [ ] Betting Value: edge calculation correct, value flags trigger at 5%+, manual override works and persists
- [ ] Bracket: Monte Carlo default renders, click-to-advance works, downstream recalculation works, reset works
- [ ] Bracket: projected/actual toggle works (actual available once playoffs start)
- [ ] Model Performance: backtest table renders with correct data
- [ ] Insights: auto-generated observations display in news feed format
- [ ] Glossary page exists with plain-English definitions
- [ ] Header shows last updated timestamp with per-source detail on click
- [ ] GitHub Actions pipeline: fetch → train → generate JSON → commit runs successfully
- [ ] Pipeline failure: creates GitHub issue and does NOT commit
- [ ] GitHub Pages serves dashboard at public URL
- [ ] Off-season: dashboard shows last season final results

---

## Edge Cases

- **MoneyPuck blocks scraping**: pipeline uses `continue-on-error`, model trains with available sources. Quality may degrade but doesn't break.
- **Injury source goes down**: use last known injury data. Flag as stale in metadata.
- **Team relocates mid-project**: config mapping handles franchise identity changes (already handles ARI→UTA).
- **COVID-like shortened season**: `shortened_season` flag in training data. Model learns to treat it differently.
- **Odds source changes format**: scraper fails gracefully. Dashboard shows "odds data stale" in source status. Manual override still works.
- **Season hasn't started**: dashboard shows previous season final results.
- **Playoff matchups not yet set**: bracket tab shows projected seedings from Monte Carlo. Switches to actual once playoffs begin.
- **All games cancelled (lockout)**: dashboard shows "No active season" message with last available data.
- **Browser localStorage full/disabled**: manual odds override fails silently. Pre-fetched odds still display.
- **User advances team in bracket that's already eliminated**: reset their selection, show the actual result.

---

## Out of Scope (Explicitly NOT doing)

- Mobile-responsive design (desktop only for now)
- Email/SMS notifications or alerts
- Game-by-game predictions (season-level and series-level only)
- Multiple sportsbook comparison (one odds source + manual override)
- React or any JS framework — staying vanilla HTML/CSS/JS
- Unit test suite (validation scripts + ML cross-validation are sufficient)
- Historical team comparison ("this team looks like 2022 Avalanche")
- Dark/light mode toggle (dark mode only)
- Click-to-expand team detail cards (future feature)
- Custom domain (using GitHub Pages default URL)
- Player-level stats on dashboard (injuries tracked but individual player stats not displayed beyond injury context)
