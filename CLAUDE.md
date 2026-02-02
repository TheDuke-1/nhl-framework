# NHL Playoff Prediction Framework

## What This Is
A data-driven NHL playoff prediction system that fetches stats from 3 sources (NHL API, MoneyPuck, Natural Stat Trick), merges them into composite team scores, and displays results in a web dashboard. Includes a "Superhuman" ML ensemble model (Ridge regression, Monte Carlo simulation) trained on 2010-2024 historical data.

Current season: 2025-26. Data refreshes daily via GitHub Actions.

## Tech Stack
- **Data pipeline:** Python 3.11 (requests, beautifulsoup4, pandas, lxml)
- **ML system:** Python (numpy, scikit-learn, scipy) — in `superhuman/`
- **Dashboard:** Vanilla HTML/CSS/JS (no framework in production). React/Recharts prototype exists (`nhl_dashboard.jsx`)
- **Automation:** GitHub Actions (daily at 6 AM EST)
- **Hosting:** Static files served via GitHub Pages (index.html is the main dashboard)

## Project Structure
```
data/                    # JSON data files (teams, standings, stats)
data/historical/         # 15 seasons of CSV data (2010-2024)
scripts/                 # Python data pipeline
  fetch_nhl_api.py       # NHL standings → nhl_standings.json
  scrape_nst.py          # Natural Stat Trick → nst_stats.json
  fetch_moneypuck.py     # MoneyPuck xG/GSAx → moneypuck_stats.json (uses pandas)
  merge_data.py          # Combines all 3 → teams.json
  refresh_data.py        # Master orchestrator (checks freshness, runs all)
  validate_data.py       # Data quality checks
  config.py              # Team mappings, API endpoints, thresholds
  utils.py               # Retry logic, validation helpers
superhuman/              # ML prediction system
  predictor.py           # Main interface
  models.py              # Ridge, LogReg, GradBoost, Monte Carlo
  feature_engineering.py # PCA transformation
  validation.py          # Cross-validation, calibration
  playoff_series_model.py # Bracket dynamics & upset rates
  config.py              # Training config (seasons, simulations)
index.html               # Main dashboard (V7.2) — THE production file
dashboard_data.json      # Superhuman model output (probabilities, tiers)
.github/workflows/       # Daily auto-refresh (update-stats.yml)
.claude/                 # Claude Code commands & agents
```

## Commands

### Data Pipeline
```bash
# Refresh all data (checks freshness, skips if recent)
python scripts/refresh_data.py

# Fetch individual sources
python scripts/fetch_nhl_api.py
python scripts/scrape_nst.py
python scripts/fetch_moneypuck.py

# Merge into teams.json
python scripts/merge_data.py

# Validate data quality
python scripts/validate_data.py
```

### Dependencies
```bash
pip install -r scripts/requirements.txt
# requires: requests, beautifulsoup4, pandas, lxml
# superhuman also needs: numpy, scikit-learn, scipy
```

### Dashboard
Open `index.html` in a browser. No build step needed — it's a standalone HTML file with embedded data.

### No Test Suite
There are no unit tests. Validation is done via `validate_data.py` (data quality checks) and the superhuman cross-validation system.

## Data Flow
```
NHL API  →  nhl_standings.json  ─┐
MoneyPuck → moneypuck_stats.json ─┼→ merge_data.py → teams.json → index.html
Nat Stat  → nst_stats.json      ─┘
                                       ↓
                              superhuman/predictor.py → dashboard_data.json
```

## Key Concepts
- **Weight score** (`teams.json` → `weight` field): Composite 100-300 scale using V7.1 weights: HDCF% 25%, GSAx 20%, CF% 15%, PP% 15%, PK% 13%, PDO 12%
- **Tiers:** Elite (85+), Strong Contender (75-84), Fringe (65-74), Longshot (55-64), Non-Contender (<55)
- **Superhuman model:** Uses 14 weighted features (Vegas signal, recent form, goal diff rate, dynasty score, etc.) → playoff/Cup probabilities with confidence intervals
- **GSAx:** Goals Saved Above Expected — goaltending quality metric
- **HDCF%:** High-Danger Corsi For % — best single predictor of playoff success

## Known Issues & Limitations
- **MoneyPuck scraping is fragile.** Their site blocks automated requests intermittently. Pipeline uses `continue-on-error` in GitHub Actions as a workaround.
- **Several `teams.json` fields are unpopulated:** `streak`, `l10`, `divRank`, `confRank` are empty strings. `hasStar` is always false. `recentXgf` is always 50.0. `scf` is always 0.
- **Dashboard data is hardcoded.** All HTML dashboards embed JSON directly — they don't fetch from files at runtime.
- **Multiple dashboard versions exist.** `index.html` is production. The others (`nhl_dashboard.html`, `nhl_dashboard_v3_clean.html`, `nhl_superhuman_dashboard.html`, `nhl_superhuman_dashboard_v2.html`) are older iterations that should probably be archived.
- **Superhuman model trained on synthetic historical data** — real 2010-2024 CSVs exist in `data/historical/` but integration may be incomplete.
- **No mobile responsiveness** on the dashboard.
- **No unit tests.** Only data validation scripts and ML cross-validation.
- **No betting odds integration** — framework is ready for it but no odds data is fetched.

## Code Style
- Python: snake_case, docstrings on main functions, try/except with logging
- HTML/CSS: Vanilla (no frameworks), CSS custom properties for theming, Space Grotesk + JetBrains Mono fonts
- Data: JSON files with metadata headers (source, timestamp, season)
- Config: Centralized in `scripts/config.py` and `superhuman/config.py`

## Claude Code Setup
- **Commands:** `/status`, `/verify`, `/build`, `/plan`, `/spec`, `/commit-push-pr`, `/code-review`
- **Agents:** code-reviewer, code-simplifier, framework-improver, spec-builder, verify-app
- **Hooks:** PostToolUse hook on Write/Edit reminds to verify changes
