# SPEC: NHL Playoff Framework — Full Project Overhaul

## Overview
Rebuild the NHL Playoff Prediction Framework from the ground up: verify/replace historical training data, retrain the Superhuman ML model on real data, fix the data pipeline, add betting odds integration, and ship a new single-file dashboard with sports broadcast styling. The goal is a system Matt trusts enough to bet with and share with friends via a single URL.

## Phasing Strategy
Foundation-first approach. Fix data and model trust before touching the dashboard.

---

## Phase 1: Data Foundation (Do First)

### 1.1 Audit Historical Data
- [ ] Spot-check `data/historical/` CSVs against authoritative sources (Hockey Reference, NHL.com)
- [ ] For each season (2010-2024), verify: standings, advanced stats (CF%, HDCF%, xG, GSAx), special teams (PP%, PK%), PDO
- [ ] Flag any files that are synthetic/AI-generated vs real
- [ ] Document findings in `reports/historical_data_audit.md`

### 1.2 Scrape Verified Historical Data
- [ ] Build scraper for Hockey Reference (primary source) — regular season team stats 2010-2024
- [ ] Build scraper for Natural Stat Trick or Evolving Hockey (secondary source) — advanced stats
- [ ] Cross-reference both sources; flag discrepancies >2%
- [ ] Output: clean, verified CSVs in `data/historical/` (replace any bad data)
- [ ] Include playoff results for each season (who won each round, Cup winner) for backtest validation

### 1.3 Fix Current Data Pipeline
- [ ] Fix MoneyPuck scraper — try Selenium/Playwright headless browser approach
- [ ] Add alternative xG/GSAx source (Evolving Hockey or Hockey Reference) as cross-reference
- [ ] Populate empty `teams.json` fields: `streak`, `l10`, `divRank`, `confRank` (available from NHL API)
- [ ] Fix `recentXgf` (currently hardcoded to 50.0) — calculate from last 10-15 games
- [ ] Fix `scf` (currently 0) — pull from NST data
- [ ] Add data freshness indicator to output JSON (timestamp, source status, staleness warning)
- [ ] Add cross-validation step: compare overlapping metrics between sources, flag disagreements

### 1.4 Add Betting Odds Scraping
- [ ] Identify best public source for Cup futures + make/miss playoff odds (VegasInsider, OddsShark, or similar)
- [ ] Build scraper to pull current odds for all 32 teams
- [ ] Store in `data/odds.json` with timestamp and source
- [ ] Add to daily GitHub Actions refresh pipeline
- [ ] Store historical odds snapshots in `data/historical/odds/` for backtest comparison

---

## Phase 2: Model Rebuild

### 2.1 Retrain Superhuman Model on Verified Data
- [ ] Wire `superhuman/data_loader.py` to read from verified historical CSVs
- [ ] Retrain Ridge regression, logistic regression, and Monte Carlo models
- [ ] Recalculate feature weights (the 14 factors) from data, not hand-tuning
- [ ] Document new learned weights vs old V7.1 weights — show what changed and why

### 2.2 Backtest & Validate
- [ ] Run leave-one-season-out backtest for 2015-2024 (10 seasons)
- [ ] For each season: record model's top-1, top-3, top-5 Cup winner accuracy
- [ ] Compare model's pre-playoff probabilities to actual Vegas odds that season
- [ ] Calculate: did the model find real edges? (model says 15% but Vegas said 8% — did those teams outperform?)
- [ ] Generate `reports/backtest_results.md` with clear tables and conclusions

### 2.3 Playoff Probability Calculator
- [ ] Calculate make/miss playoff probability for all 32 teams
- [ ] Factor in: current points, games remaining, strength of remaining schedule, current pace
- [ ] Output clinch/elimination magic numbers where applicable
- [ ] Store week-over-week snapshots for trend tracking (last 4 weeks)

### 2.4 Retire V7.1 Manual Weights
- [ ] Remove hand-tuned weight system from `merge_data.py`
- [ ] Single model: Superhuman data-driven predictions only
- [ ] Keep V7.1 documentation in `archive/` for reference

---

## Phase 3: Dashboard Rebuild

### 3.1 Architecture
- Single self-contained HTML file (`index.html`)
- Loads `dashboard_data.json` via fetch() (works on GitHub Pages since both files are same-origin)
- Vanilla HTML/CSS/JS — no framework, no build step
- GitHub Actions rebuilds `dashboard_data.json` daily; HTML file rarely changes

### 3.2 Visual Design
- **Style:** Sports broadcast aesthetic (ESPN/NHL.com energy)
- **Colors:** Dark background, team primary colors as badges/dots per team
- **Typography:** Bold, high-contrast, sports-style fonts
- **Layout:** Tab-based navigation between views
- **Mobile:** Desktop-first, but shouldn't be broken on phone (responsive grid, no horizontal scroll)

### 3.3 Dashboard Views/Tabs

**Tab 1: Power Rankings**
- All 32 teams ranked by composite strength score
- Columns: Rank, Team (with color badge), Tier, Composite Score, Cup Prob%, Playoff Prob%, HDCF%, GSAx, CF%, PP%, PK%, PDO
- Sortable by any column
- Tier indicated by colored left border (green/blue/orange/red)
- Row highlighting on hover

**Tab 2: Tier Overview**
- Teams grouped into 4 tiers: Elite, Contender, Bubble, Longshot
- Visual card/panel per tier with team color badges
- Each team shows: composite score, Cup probability, key strength/weakness

**Tab 3: Playoff Race (by Conference)**
- Eastern Conference and Western Conference sections
- Each team shows: current points, games played, games remaining, playoff probability %, trend (last 4 weeks sparkline), clinch/elimination magic number
- Teams in playoff spots highlighted differently from those outside
- Sorted by current standing within each conference

**Tab 4: Betting Value**
- Side-by-side table: Team | Model Cup Prob | Market Odds | Implied Prob | Edge | Value Flag
- Same for make/miss playoffs
- Value flags: highlight rows where model edge > X% (configurable threshold)
- Color code: green = value bet, red = market overpricing

**Tab 5: Playoff Bracket**
- Visual bracket layout matching real NHL playoff format (4 rounds, 16 teams)
- Default: model's projected bracket with probabilities at each matchup
- Interactive: click a team to advance them; recalculates downstream probabilities
- "Reset to model" button to restore default projection
- Show series win probability for each matchup

**Tab 6: Model Performance**
- Backtest results table: season-by-season accuracy (top-1, top-3, top-5)
- Model vs Vegas comparison chart
- Key performance stats (overall accuracy, calibration, edge found)
- Last updated timestamp and data freshness indicator

**Tab 7: Insights**
- Auto-generated key insights from current data:
  - Biggest movers (up/down) in last week
  - Value bet alerts (new value bets since last update)
  - Trend warnings (teams with declining metrics)
  - Notable stat leaders (best HDCF%, best GSAx, etc.)

### 3.4 Data Contract
`dashboard_data.json` must include:
```json
{
  "metadata": { "generated", "season", "modelVersion", "dataFreshness" },
  "teams": [{ "rank", "code", "name", "conference", "division", "tier",
               "compositeStrength", "cupProbability", "playoffProbability",
               "hdcfPct", "gsax", "cfPct", "ppPct", "pkPct", "pdo",
               "points", "gamesPlayed", "gamesRemaining",
               "clinchNumber", "eliminationNumber",
               "trendData": [last 4 weeks of composite scores],
               "marketOdds": { "cupOdds", "impliedProb", "edge" },
               "playoffMarketOdds": { "odds", "impliedProb", "edge" }
            }],
  "bracket": { projected matchups with probabilities },
  "backtest": { season-by-season results },
  "insights": [{ "type", "text", "severity" }],
  "featureWeights": { learned weights from model }
}
```

---

## Phase 4: Cleanup & Ship

### 4.1 Archive Old Files
- [ ] Create `archive/` directory
- [ ] Move all old dashboard versions (nhl_dashboard*.html, dashboard_preview.html, test_dashboard.html, nhl_dashboard.jsx)
- [ ] Move old docs (Audit_Report.md, Audit_Report_V2.md, CHECKPOINT_2_PRESENTATION.md, TECHNICAL_REVIEW_OPTION_C.md, etc.)
- [ ] Move Framework_Methodology_V7.1.md and Quick_Reference_V7.1.md (replaced by data-driven model)
- [ ] Keep only: index.html, CLAUDE.md, SPEC, dashboard_data.json, data/, scripts/, superhuman/, .github/, .claude/

### 4.2 GitHub Pages Setup
- [ ] Ensure GitHub Pages is enabled (serves from main branch root)
- [ ] index.html + dashboard_data.json are the only files needed at root for the live site
- [ ] Test that the URL works and data loads correctly
- [ ] Share URL with Matt's group

### 4.3 Update Automation
- [ ] Update GitHub Actions to: fetch all data sources → run model → generate dashboard_data.json → commit & push
- [ ] Add odds scraping to the daily pipeline
- [ ] Add data validation step (reject update if data looks wrong)
- [ ] Add simple health check: if pipeline fails 3 days in a row, create a GitHub issue

---

## Verification Checklist
- [ ] Historical data audit complete — documented which data is real vs synthetic
- [ ] At least 10 seasons of verified historical data available
- [ ] Model retrained on real data with documented accuracy metrics
- [ ] Backtest shows model performance vs Vegas across 2015-2024
- [ ] All 32 teams present with all fields populated in teams.json (no empty strings, no placeholder values)
- [ ] MoneyPuck scraper works reliably OR alternative source integrated
- [ ] Odds data scraping works and updates daily
- [ ] Dashboard loads data from dashboard_data.json (not hardcoded)
- [ ] All 7 dashboard tabs render correctly
- [ ] Bracket simulator is interactive (click to advance, reset button works)
- [ ] Mobile: dashboard is usable (not broken) on phone screen
- [ ] Old files archived, repo is clean
- [ ] GitHub Pages serves the dashboard at a shareable URL
- [ ] Daily automation runs end-to-end without manual intervention

## Edge Cases
- **Mid-season team changes:** Utah Hockey Club (formerly Arizona). Config must handle name mapping across historical data.
- **MoneyPuck goes down:** Pipeline should continue with NHL API + NST data. Flag MoneyPuck as stale, don't block update.
- **Odds source changes format:** Scraper should fail gracefully and use last known odds. Dashboard shows "odds data stale" warning.
- **Season hasn't started yet:** Dashboard should show "Preseason — no data available" rather than crashing.
- **Playoff teams not yet determined:** Bracket tab should show projected seedings with probability, not assume matchups are final.
- **Clinch/elimination edge cases:** Teams can clinch playoff berth, division title, or Presidents' Trophy. Track the most relevant one.

## Out of Scope (Decided NOT to do)
- Player-level data / injury tracking
- Email/SMS notifications or alerts
- Historical team comparison ("this team looks like 2022 Avalanche")
- React or any JS framework — staying vanilla
- Multiple sportsbook comparison (one odds source is enough)
- Game-by-game predictions (only season-level and series-level)
- Unit test suite (validation scripts are sufficient for now)
