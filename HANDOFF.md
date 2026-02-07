# NHL Playoff Prediction Framework — Complete Project Handoff

## Copy the prompt below this line to recreate the entire project from scratch.

---

# PROMPT: Build the NHL Playoff Prediction Framework

Build a complete, production-ready NHL playoff prediction system. This is a data-driven framework that fetches stats from 3 external sources (NHL API, MoneyPuck, Natural Stat Trick), merges them into composite team scores, runs an ML ensemble model (Ridge regression, Gradient Boosting, Neural Network, Monte Carlo simulation) trained on 2010-2025 historical data, and displays results in a premium dark-themed web dashboard. The system refreshes daily via GitHub Actions.

**Current season: 2025-26. Python 3.11. No frontend frameworks — vanilla HTML/CSS/JS.**

---

## PROJECT STRUCTURE

```
NHL Playoff Project/
├── index.html                    # Main dashboard (standalone HTML entry point)
├── dashboard_data.json           # ML model output consumed by dashboard
├── css/
│   └── style.css                 # Complete design system (~1800 lines)
├── js/
│   ├── app.js                    # Bootstrap, data loading, tab routing
│   ├── rankings.js               # Power rankings tab
│   ├── playoff-race.js           # Conference standings tab
│   ├── betting.js                # Betting value/edge tab
│   ├── bracket.js                # Full playoff bracket tab
│   ├── performance.js            # Model backtest tab
│   ├── insights.js               # Auto-generated insights tab
│   └── data.js                   # Embedded data fallback (auto-generated)
├── data/
│   ├── teams.json                # Merged pipeline output (32 teams)
│   ├── nhl_standings.json        # NHL API data
│   ├── moneypuck_stats.json      # MoneyPuck xG data
│   ├── nst_stats.json            # Natural Stat Trick advanced stats
│   ├── odds.json                 # Betting odds (optional)
│   ├── injuries.json             # Injury data (optional)
│   ├── historical/verified/      # 15 seasons of CSV data (2010-2024)
│   └── snapshots/                # Weekly data snapshots
├── scripts/
│   ├── config.py                 # Team mappings, API endpoints, constants
│   ├── utils.py                  # Retry logic, validation, I/O helpers
│   ├── fetch_nhl_api.py          # NHL standings + PP%/PK%
│   ├── scrape_nst.py             # Natural Stat Trick web scraping
│   ├── fetch_moneypuck.py        # MoneyPuck CSV download
│   ├── merge_data.py             # Combine 3 sources → teams.json
│   ├── refresh_data.py           # Master orchestrator
│   ├── validate_data.py          # Data quality checks
│   ├── fetch_odds.py             # Odds fetching (placeholder)
│   ├── fetch_injuries.py         # Injury fetching (placeholder)
│   ├── requirements.txt          # Python dependencies
│   └── requirements-test.txt     # Test dependencies
├── superhuman/
│   ├── __init__.py               # Package init
│   ├── config.py                 # ML config, seasons, team structures
│   ├── data_models.py            # TeamSeason, FeatureVector, PredictionResult dataclasses
│   ├── data_loader.py            # Load current + synthesize training data
│   ├── real_data_loader.py       # Load real historical CSVs
│   ├── feature_engineering.py    # PCA, 14 features, composite scores
│   ├── models.py                 # Ensemble: LogReg, GradBoost, NN, Monte Carlo
│   ├── predictor.py              # Main prediction interface
│   ├── validation.py             # Cross-validation, backtest
│   ├── playoff_series_model.py   # Series prediction with round-specific rates
│   ├── dashboard_generator.py    # Generate dashboard_data.json
│   ├── player_data_loader.py     # Real player stats loader
│   ├── recent_form_loader.py     # Recent form feature
│   ├── betting_odds_loader.py    # Vegas odds feature
│   ├── clutch_data_loader.py     # Clutch performance feature
│   ├── playoff_experience_loader.py # Playoff experience + dynasty features
│   ├── nhl_api.py                # NHL API helpers
│   ├── audit_data.py             # Data auditing utility
│   ├── validate_playoff_model.py # Playoff model validation
│   └── run_backtest.py           # Backtest runner
├── tests/
│   ├── conftest.py               # Shared pytest fixtures
│   ├── test_dashboard.py         # HTML structure tests (6 tests)
│   ├── test_data_pipeline.py     # teams.json integrity tests (8 tests)
│   └── test_superhuman.py        # dashboard_data.json tests (6 tests)
├── .github/workflows/
│   └── update-stats.yml          # Daily auto-refresh at 6 AM EST
├── pytest.ini                    # Test configuration
├── .gitignore                    # Python, IDE, OS ignores
├── history/                      # Daily snapshot JSONs
└── CLAUDE.md                     # Project documentation
```

---

## PART 1: DATA PIPELINE

### 1A. scripts/config.py — Central Configuration

```python
CURRENT_SEASON = "2025-26"
SEASON_ID = "20252026"          # Used in NHL API & NST URLs
SEASON_END_YEAR = 2026
DATA_DIR = Path(__file__).parent.parent / "data"
SCRIPTS_DIR = Path(__file__).parent
```

**All 32 NHL Teams:**
```python
ALL_TEAMS = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL",
    "DAL", "DET", "EDM", "FLA", "LA", "MIN", "MTL", "NJ",
    "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJ",
    "STL", "TB", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH"
]
```

**Team Info (conference/division for all 32):**
```python
TEAM_INFO = {
    "ANA": {"name": "Anaheim Ducks", "conf": "West", "div": "Pacific"},
    "BOS": {"name": "Boston Bruins", "conf": "East", "div": "Atlantic"},
    "BUF": {"name": "Buffalo Sabres", "conf": "East", "div": "Atlantic"},
    "CAR": {"name": "Carolina Hurricanes", "conf": "East", "div": "Metropolitan"},
    "CBJ": {"name": "Columbus Blue Jackets", "conf": "East", "div": "Metropolitan"},
    "CGY": {"name": "Calgary Flames", "conf": "West", "div": "Pacific"},
    "CHI": {"name": "Chicago Blackhawks", "conf": "West", "div": "Central"},
    "COL": {"name": "Colorado Avalanche", "conf": "West", "div": "Central"},
    "DAL": {"name": "Dallas Stars", "conf": "West", "div": "Central"},
    "DET": {"name": "Detroit Red Wings", "conf": "East", "div": "Atlantic"},
    "EDM": {"name": "Edmonton Oilers", "conf": "West", "div": "Pacific"},
    "FLA": {"name": "Florida Panthers", "conf": "East", "div": "Atlantic"},
    "LA":  {"name": "Los Angeles Kings", "conf": "West", "div": "Pacific"},
    "MIN": {"name": "Minnesota Wild", "conf": "West", "div": "Central"},
    "MTL": {"name": "Montreal Canadiens", "conf": "East", "div": "Atlantic"},
    "NJ":  {"name": "New Jersey Devils", "conf": "East", "div": "Metropolitan"},
    "NSH": {"name": "Nashville Predators", "conf": "West", "div": "Central"},
    "NYI": {"name": "New York Islanders", "conf": "East", "div": "Metropolitan"},
    "NYR": {"name": "New York Rangers", "conf": "East", "div": "Metropolitan"},
    "OTT": {"name": "Ottawa Senators", "conf": "East", "div": "Atlantic"},
    "PHI": {"name": "Philadelphia Flyers", "conf": "East", "div": "Metropolitan"},
    "PIT": {"name": "Pittsburgh Penguins", "conf": "East", "div": "Metropolitan"},
    "SEA": {"name": "Seattle Kraken", "conf": "West", "div": "Pacific"},
    "SJ":  {"name": "San Jose Sharks", "conf": "West", "div": "Pacific"},
    "STL": {"name": "St. Louis Blues", "conf": "West", "div": "Central"},
    "TB":  {"name": "Tampa Bay Lightning", "conf": "East", "div": "Atlantic"},
    "TOR": {"name": "Toronto Maple Leafs", "conf": "East", "div": "Atlantic"},
    "UTA": {"name": "Utah Hockey Club", "conf": "West", "div": "Central"},
    "VAN": {"name": "Vancouver Canucks", "conf": "West", "div": "Pacific"},
    "VGK": {"name": "Vegas Golden Knights", "conf": "West", "div": "Pacific"},
    "WPG": {"name": "Winnipeg Jets", "conf": "West", "div": "Central"},
    "WSH": {"name": "Washington Capitals", "conf": "East", "div": "Metropolitan"},
}
```

**Conference/Division Structure:**
```python
CONFERENCES = {
    "East": {
        "Atlantic": ["BOS", "BUF", "DET", "FLA", "MTL", "OTT", "TB", "TOR"],
        "Metropolitan": ["CAR", "CBJ", "NJ", "NYI", "NYR", "PHI", "PIT", "WSH"]
    },
    "West": {
        "Central": ["CHI", "COL", "DAL", "MIN", "NSH", "STL", "UTA", "WPG"],
        "Pacific": ["ANA", "CGY", "EDM", "LA", "SEA", "SJ", "VAN", "VGK"]
    }
}
```

**NHL API Endpoints:**
```python
NHL_API = {
    "standings": "https://api-web.nhle.com/v1/standings/now",
    "pp_stats": f"https://api.nhle.com/stats/rest/en/team/powerplay?cayenneExp=seasonId={SEASON_ID}",
    "pk_stats": f"https://api.nhle.com/stats/rest/en/team/penaltykill?cayenneExp=seasonId={SEASON_ID}",
}
```

**NHL API Team Abbreviation Mapping** (API uses different abbrevs):
```python
NHL_API_TEAM_MAP = {
    "LAK": "LA", "NJD": "NJ", "SJS": "SJ", "TBL": "TB"
}
```

**NST Team Name Mapping** (full names from website → standard abbreviations):
Map all 32 full team names to abbreviations, including variations like "Montréal Canadiens" → "MTL", "St Louis Blues" → "STL", "Utah Hockey Club" → "UTA", etc.

**Data Freshness Thresholds:**
```python
FRESHNESS_THRESHOLDS = {
    "nhl_standings": 24,   # hours
    "moneypuck_stats": 48,
    "nst_stats": 72,
    "odds": 168,
    "teams": 24,
}
```

**Metric Validation Ranges:**
```python
VALID_RANGES = {
    "hdcfPct": (35, 65),
    "cfPct": (40, 60),
    "pdo": (95, 105),
    "ppPct": (10, 35),
    "pkPct": (65, 95),
    "gsax": (-40, 40),
    "pts": (0, 150),
}
```

**Helper Functions:**
- `get_current_timestamp()` → ISO UTC string with Z suffix
- `normalize_team_abbrev(abbrev, source)` → standard abbreviation
- `get_team_name(abbrev)` → full team name
- `get_team_info(abbrev)` → {conf, div} dict

### 1B. scripts/utils.py — Shared Utilities

**Logging:** `setup_logging(name)` → configured logger with INFO level

**HTTP:** `fetch_url(url, timeout=30)` with up to 3 retries, exponential backoff (5s, 10s, 15s), custom `FetchError` exception. Also `fetch_json(url)` that parses response as JSON.

**File I/O:**
- `load_json_file(filepath)` → dict (returns {} on error)
- `save_json_file(filepath, data, indent=2)` → creates parent dirs
- `get_file_age_hours(filepath)` → float or None

**Freshness:**
- `check_data_freshness(data_type)` → (is_fresh, age_hours, threshold_hours)
- `get_data_freshness_report()` → list of status dicts for 5 key files

**Validation:**
- `validate_metric_range(value, metric_name)` → (is_valid, message). Special PDO handling: if value < 2, multiply by 100.
- `validate_team_data(team_data, required_fields)` → (is_valid, errors_list)
- `validate_teams_data(teams_dict, min_teams=32)` → (is_valid, summary)

**Numeric:** `safe_float(value, default=0.0)`, `safe_int(value, default=0)`, `round_to(value, decimals=1)`

**Metadata:** `create_metadata(source, url=None, notes=None, extra=None)` → standardized dict with source, season, fetchedAt

**Console:** `print_header(title, char="=")`, `print_status(label, status, color=None)` with ANSI colors

### 1C. scripts/fetch_nhl_api.py — NHL Standings

Fetches standings from `https://api-web.nhle.com/v1/standings/now` and PP%/PK% from separate stats endpoints.

**parse_standings(data):** For each team in standings:
- Extract: team abbrev (mapped via NHL_API_TEAM_MAP), teamName, conf (East/West), div
- Extract: gp, w, l, otl, pts, gf, ga
- Extract: streak (e.g., "W2"), l10 (e.g., "7-2-1"), home record, away record
- Extract: divRank, confRank, leagueRank
- Calculate: `recentPts` = L10 points percentage: `(wins*2 + otl) / (total*2) * 100`

**fetch_pp_pk_stats():** Fetches from separate PP and PK endpoints. Maps teamFullName → abbreviation. Handles both ratio (0.225) and percentage (22.5) formats with sanity checks (PP% 5-40%, PK% 60-95%).

**Output → data/nhl_standings.json:**
```json
{
  "_metadata": { "source": "NHL API", "endpoints": [...], "fetchedAt": "...", "teamCount": 32 },
  "teams": {
    "BOS": { "team": "BOS", "teamName": "...", "conf": "East", "div": "Atlantic",
             "gp": 52, "w": 35, "l": 12, "otl": 5, "pts": 75,
             "gf": 150, "ga": 95, "ppPct": 24.5, "pkPct": 82.1,
             "streak": "W2", "l10": "7-2-1", "home": "18-5-2", "away": "17-7-3",
             "divRank": 1, "confRank": 2, "leagueRank": 3, "recentPts": 75.0 }
  }
}
```

### 1D. scripts/scrape_nst.py — Natural Stat Trick

Scrapes HTML table from `https://www.naturalstattrick.com/teamtable.php` with parameters for 5v5, all scores, regular season.

**Parameters:** `fromseason=20252026, thruseason=20252026, stype=2, sit=5v5, score=all, rate=n, team=all, loc=B, gpf=410`

**Parsing:** Uses BeautifulSoup with lxml parser. Finds table with id='teams' (fallback: first table). Extracts headers from `<thead>` to determine column order. Has default column order fallback. Maps team names via TEAM_NAME_MAP with fuzzy matching.

**Metrics extracted:**
- CF, CA, CF% (Corsi)
- HDCF, HDCA, HDCF% (High-Danger Corsi — best single predictor)
- xGF, xGA, xGF% (Expected Goals)
- GSAx = xGA - GA (positive = better goaltending)
- SCF, SCA, SCF% (Scoring Chances)
- SH%, SV%, PDO

**Output → data/nst_stats.json:**
```json
{
  "_metadata": { "source": "Natural Stat Trick", "url": "...", "season": "2025-26",
                 "fetchedAt": "...", "teamCount": 32, "notes": "5v5 situation, all scores" },
  "teams": {
    "BOS": { "team": "BOS", "gp": 52, "cf": 1548, "ca": 1402, "cfPct": 52.4,
             "hdcf": 285, "hdca": 248, "hdcfPct": 53.5,
             "xgf": 125.6, "xga": 98.4, "xgfPct": 56.1, "gsax": 8.2,
             "scf": 425, "sca": 380, "scfPct": 52.8,
             "shPct": 8.1, "svPct": 91.5, "pdo": 1.002 }
  }
}
```

### 1E. scripts/fetch_moneypuck.py — MoneyPuck xG

Downloads CSV from `https://moneypuck.com/moneypuck/playerData/seasonSummary/2026/regular/teams.csv`. Uses pandas to filter to 5v5 situation.

**Metrics extracted:**
- xgf (xGoalsFor), xga (xGoalsAgainst), xgf60, xga60
- gsax = (goalsAgainst - xGoalsAgainst) * -1
- cf, ca, cfPct, ff, fa, shotsFor, shotsAgainst, xgfPct

**Output → data/moneypuck_stats.json** (same structure as NST but different fields)

**Note:** MoneyPuck is fragile — site blocks automated requests intermittently. Pipeline uses `continue-on-error`.

### 1F. scripts/merge_data.py — Data Merger

**Priority:** NHL API (standings) → NST (advanced stats, PRIMARY) → MoneyPuck (backup xG) → Odds (optional)

**Defaults:**
```python
DEFAULTS = {
    "gp": 0, "w": 0, "l": 0, "otl": 0, "pts": 0, "gf": 0, "ga": 0,
    "ppPct": 20.0, "pkPct": 80.0, "cf": 0, "cfPct": 50.0,
    "xgf": 0, "xga": 0, "hdcf": 0, "hdcfPct": 50.0, "pdo": 1.000, "gsax": 0.0,
    "scf": 0, "scfPct": 50.0, "xgfPct": 50.0, "recentForm": 50.0, "weight": 200,
}
```

**Merge process per team:**
1. Initialize with defaults + team info from TEAM_INFO
2. Merge NHL API: gp, w, l, otl, pts, gf, ga, ppPct, pkPct, streak, l10, home, away, ranks, recentForm
3. Merge NST (PRIMARY): cf, cfPct, hdcf, hdcfPct, pdo, scf, scfPct, xgf, xga, xgfPct, gsax
4. Merge MoneyPuck (SECONDARY): only if NST didn't provide xGF. Always store mp_xgf, mp_gsax for cross-reference
5. Derive: xgd = xgf - xga, gd = gf - ga, ptsPct = pts / (gp * 2) * 100
6. Merge odds (optional): playoffPct, divisionPct, cupPct, impliedCupOdds, projPts

**Sort** by points descending, then games played descending.

**Output → data/teams.json:**
```json
{
  "_metadata": {
    "generatedAt": "...", "sources": { "nhl_api": "...", "moneypuck": "...", "nst": "...", "odds": "..." },
    "teamCount": 32, "version": "7.3"
  },
  "teams": [
    { "team": "COL", "name": "Colorado Avalanche", "conf": "West", "div": "Central",
      "gp": 53, "w": 36, "l": 8, "otl": 9, "pts": 81, "gf": 208, "ga": 134,
      "ppPct": 15.5, "pkPct": 84.1, "cf": 2991.0, "cfPct": 55.96,
      "xgf": 135.12, "xga": 105.22, "hdcf": 570.0, "hdcfPct": 55.29,
      "pdo": 1.032, "gsax": 21.22, "scf": 1450.0, "scfPct": 57.38,
      "xgfPct": 56.22, "recentForm": 50.0, "weight": 200,
      "streak": "W", "l10": "4-4-2", "home": "20-2-4", "away": "16-6-5",
      "divRank": 1, "confRank": 1, "xgd": 29.9, "gd": 74, "ptsPct": 76.4 }
  ]
}
```

### 1G. scripts/refresh_data.py — Orchestrator

CLI: `python refresh_data.py [--force] [--check] [--validate]`

Steps (in order):
1. Fetch NHL API standings (skip if fresh, unless --force)
2. Fetch NST stats
3. Fetch odds
4. Check MoneyPuck freshness (may need browser fetch)
5. Merge all data
6. Validate output (32 teams, ranges, freshness)

Uses subprocess with timeouts (120s for fetches, 60s for merge). Reports status with color-coded output.

### 1H. scripts/validate_data.py — Quality Assurance

Validates all 4 data files: NST, NHL API, MoneyPuck, merged teams.json.

**Checks per file:**
- Data freshness (≤ 7 days old)
- Team count (exactly 32)
- Metric ranges (HDCF% 35-65, CF% 40-60, PDO 0.95-1.05, PP% 10-35, PK% 70-95, GSAx -40 to 40)
- Default value detection (all teams having default = data failure)
- Special: HDCF% not all 50.0 (NST), PP%/PK% not all 0 (NHL API), GSAx not all 0 (MoneyPuck)

Exit code 0 = pass, 1 = fail.

---

## PART 2: SUPERHUMAN ML PREDICTION SYSTEM

### 2A. superhuman/config.py — ML Configuration

```python
TRAINING_SEASONS = list(range(2010, 2023))  # 2010-2022
TEST_SEASONS = list(range(2023, 2026))       # 2023-2025
CURRENT_SEASON = 2026
N_SIMULATIONS = 50000
RANDOM_SEED = 42
TIME_DECAY_HALF_LIFE = 20
PLAYOFF_TEAMS_PER_CONFERENCE = 8
GAMES_IN_SEASON = 82
MERGE_RELOCATED_FRANCHISES = True
```

**Historical Team Map:** ARI→UTA, PHX→UTA, ATL→WPG, LAK→LA, NJD→NJ, SJS→SJ, TBL→TB

**Key function:** `select_conference_playoff_teams(conf_name, team_pts)` — implements real NHL rules: top 3 per division + 2 best remaining wildcards.

### 2B. superhuman/data_models.py — Data Structures

**TeamSeason** (dataclass): Complete team data for one season.
- Identifiers: team, season, division
- Basic stats: games_played, wins, losses, ot_losses, points
- Goals: goals_for, goals_against
- Possession (5v5): cf_pct, ff_pct, sf_pct
- Expected goals: xgf, xga, xgf_pct
- High-danger: hdcf, hdca, hdcf_pct
- Goaltending: gsax, save_pct, hd_save_pct
- Special teams: pp_pct, pk_pct
- Home/Away splits for road_performance
- Close games: one_goal_wins/losses, ot_wins, comeback_wins, blown_leads
- Roster: top_scorer_points/ppg, players_20_goals/40_points
- Sustainability: pdo, shooting_pct
- Playoff results: made_playoffs, playoff_seed, playoff_rounds_won, won_cup
- Properties: goal_differential, gd_per_game, points_pct, xgd, xgd_per_game, home/away_win_pct, road_differential, clutch_score
- `playoff_success_score`: 0=missed, 0.10=lost R1, 0.25=won R1, 0.45=conf finals, 0.70=cup finals, 1.00=won Cup

**FeatureVector** (dataclass): 14 features for model input.
1. goal_differential_rate
2. territorial_dominance (PCA component 1)
3. shot_quality_premium (PCA component 2)
4. goaltending_quality
5. special_teams_composite
6. road_performance
7. recent_form
8. roster_depth
9. star_power
10. clutch_performance
11. sustainability
12. vegas_cup_signal
13. playoff_experience
14. dynasty_score
- Targets: made_playoffs, playoff_success, won_cup
- `to_array()` → numpy array of 14 features
- `feature_names()` → ordered list of names

**ConferenceTrace** (dataclass): Single conference playoff simulation trace (r1_winners, r2_winners, conf_champion, matchups per round).

**MonteCarloResult** (dataclass): Full MC simulation results — cup_probabilities, round_advancement, projected_matchups, conf_final/cup_final probs, r2/cf/cup_final matchup tracking, projected_standings.

**PredictionResult** (dataclass): Final output per team — composite_strength, strength_rank, playoff/conf_final/cup_final/cup_win probabilities, 90% CI, tier classification.

### 2C. superhuman/data_loader.py — Data Loading

**load_current_season_data():** Loads data/teams.json → List[TeamSeason]. Maps JSON fields to TeamSeason fields. Normalizes PDO (if < 2, multiply by 100).

**load_training_data():** Tries real CSV data first (via real_data_loader), falls back to synthetic data. Needs ≥32 records (one season) to use real data.

**synthesize_training_data():** Creates synthetic historical data for 2010-2025.
- Step 1: Generate INDEPENDENT stats from distributions (no stat derived from another):
  - goals_for: N(250, 25), goals_against: N(250, 25)
  - cf_pct: N(50, 3.5), xgf_pct: N(50, 3.5), hdcf_pct: N(50, 4.0)
  - gsax: N(0, 10), pp_pct: N(20, 3), pk_pct: N(80, 3), pdo: N(100, 1.5)
  - Points derived from GD with noise: pts = 82 + int(gd * 0.7) + random(-8, 9)
- Step 2: Assign playoff outcomes based on relative strength rankings with noise
- Uses known Cup winners/finalists as ground truth (CUP_WINNERS dict: 2010-2025)

**CUP_WINNERS:** {2010: "CHI", 2011: "BOS", 2012: "LA", 2013: "CHI", 2014: "LA", 2015: "CHI", 2016: "PIT", 2017: "PIT", 2018: "WSH", 2019: "STL", 2020: "TB", 2021: "TB", 2022: "COL", 2023: "VGK", 2024: "FLA", 2025: "FLA"}

**CUP_FINALISTS:** {2010: "PHI", 2011: "VAN", 2012: "NJ", 2013: "BOS", 2014: "NYR", 2015: "TB", 2016: "SJ", 2017: "NSH", 2018: "VGK", 2019: "BOS", 2020: "DAL", 2021: "MTL", 2022: "TB", 2023: "FLA", 2024: "EDM", 2025: "EDM"}

### 2D. superhuman/feature_engineering.py — Feature Transformation

**FeatureEngineer** class:

**PCA on possession metrics:** Extracts 4 correlated metrics (hdcf_pct, cf_pct, xgf_pct, xgd_per_game*10) → 2 PCA components (territorial_dominance, shot_quality_premium).

**14 Feature Calculations:**

1. **goal_differential_rate** = gd_per_game (goals for minus against, per game)
2. **territorial_dominance** = PCA component 1 of [HDCF%, CF%, xGF%, xGD/game]
3. **shot_quality_premium** = PCA component 2
4. **goaltending_quality** = gsax / 10.0 (normalize to ~-3 to +3)
5. **special_teams_composite** = 0.4 * (PP% - 20)/5 + 0.6 * (PK% - 80)/5
6. **road_performance** = (away_win_pct - home_win_pct * 0.85) * 2
7. **recent_form** = from recent_form_loader (last 10-20 games performance)
8. **roster_depth** = from player_data_loader or proxy: players_20_goals scoring, or gf_per_game
9. **star_power** = from player_data_loader or proxy: top_scorer_ppg, or offensive output
10. **clutch_performance** = from clutch_data_loader (OT wins, one-goal wins, comebacks)
11. **sustainability** = -|PDO - 100| / 5 (high PDO = regression risk)
12. **vegas_cup_signal** = (cup_implied_prob - 0.03) * 15 (from betting odds)
13. **playoff_experience** = weighted recent playoff rounds won
14. **dynasty_score** = recency-weighted Cup wins and Finals appearances

**create_feature_matrix(features):** Converts FeatureVector list → (X numpy array, y targets, feature names).

### 2E. superhuman/models.py — Ensemble Models

**calculate_recency_weights(features, decay_rate=0.15, cup_winner_boost=2.0):**
Exponential decay by year: `exp(-0.15 * years_ago)`. Cup winners get 2x boost. Normalized so weights average to 1.

**WeightOptimizer (Ridge Regression):**
- Ridge(alpha=1.0) to find optimal feature weights
- StandardScaler preprocessing, zero-variance removal
- Outputs normalized weights summing to 100%

**PlayoffClassifier (Logistic Regression):**
- LogisticRegression(penalty='l2', C=0.5, solver='lbfgs', max_iter=1000)
- Predicts binary: made playoffs or not
- StandardScaler preprocessing

**CupPredictor (Gradient Boosting):**
- GradientBoostingClassifier(n_estimators=50, max_depth=3, learning_rate=0.1, subsample=0.8)
- Predicts binary: won Cup or not

**NeuralNetworkPredictor (MLP):**
- MLPClassifier(hidden_layer_sizes=(64, 32, 16), activation='relu', solver='adam', alpha=0.01, early_stopping=True)
- Wrapped in CalibratedClassifierCV(method='sigmoid', cv=3) for calibrated probabilities
- Fallback to uncalibrated if calibration fails

**CupProbabilityCalibrator:**
- IsotonicRegression(y_min=0.001, y_max=0.50) for final Cup probability calibration

**MonteCarloSimulator:**
- 50,000 simulations by default (configurable via N_SIMULATIONS in config)
- **Pace-projected standings:** projects end-of-season points from current pace, adds Gaussian noise per sim (σ = 0.5 * √remaining_games)
- **NHL playoff selection:** Real rules — top 3 per division + 2 wildcards
- **NHL seeding:** Div winner 1 vs WC2, Div winner 2 vs WC1, 2nd vs 3rd within divisions. Bracket A (indices 0,1) and Bracket B (indices 2,3).
- **Series simulation (basic):** Logistic: `prob_a = 1 / (1 + exp(-0.03 * strength_diff))`, blended with round parity rates, home ice advantage (+0.04 home, -0.02 away). Best-of-7 with home pattern [H,H,A,A,H,A,H].
- **Series simulation (enhanced):** Uses playoff_series_model if available for round-specific upset rates and experience factors.
- **Round base rates:** R1: 0.59, R2: 0.53, CF: 0.50, Cup Final: 0.53
- **R1 matchup tracking:** Top 4 by frequency per conference, consolidates flipped pairs, ensures each team appears in ≤1 matchup
- **R2+ matchup tracking:** Frequency thresholds — R2/CF: 5% of sims, Cup Final: 1%
- **Conference trace:** Tracks r1_winners, r2_winners, conf_champion, all matchups per round

**EnsemblePredictor** — main model combining all sub-models:
- Components: FeatureEngineer, WeightOptimizer, PlayoffClassifier, CupPredictor, NeuralNetworkPredictor, CupProbabilityCalibrator, MonteCarloSimulator(n=10000)
- **Cup ensemble weights:** Gradient Boosting 30%, Neural Network 30%, Monte Carlo 40%
- **Without NN fallback:** GB 40%, MC 60%
- **Training flow:** Feature engineering → recency weights → train all sub-models with sample weights → fit Cup calibrator
- **Prediction flow:** Transform features → get strength scores → get model probs → run MC simulation with experience scores → weighted ensemble → gate by playoff probability (`prob * min(1.0, playoff_prob + 0.1)`) → normalize to sum to 100%
- **Strength scores:** Base 50 + weighted sum of (weight * feature_value / 10)
- **Confidence intervals:** Beta distribution: α = prob*n + 1, β = (1-prob)*n + 1, 90% CI
- **Tier classification (percentile-based):** Top 4 = Elite, next 8 = Contender, next 8 = Bubble, bottom 12 = Longshot

### 2F. superhuman/predictor.py — Main Interface

**SuperhumanPredictor** class:
- `train()` → loads training data, trains ensemble
- `predict()` → loads current season data, generates predictions, sorts by Cup prob
- `print_predictions(top_n=32)` → formatted table output
- `to_json()` → serializable dict
- `save_json(filepath)` → write to file

CLI: `python -m superhuman.predictor [--team COL] [--output results.json] [--top 10] [--quiet]`

### 2G. superhuman/dashboard_generator.py — JSON Output Generator

**Tier Config:**
```python
TIER_CONFIG = {
    "Elite": {"color": "#10b981", "bg": "rgba(16, 185, 129, 0.15)", "icon": "🏆"},
    "Contender": {"color": "#3b82f6", "bg": "rgba(59, 130, 246, 0.15)", "icon": "🎯"},
    "Bubble": {"color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.15)", "icon": "⚡"},
    "Longshot": {"color": "#ef4444", "bg": "rgba(239, 68, 68, 0.15)", "icon": "🎲"},
}
```

**Complete TEAM_INFO dict** with name, city, conference, division for all 32 teams.

**METRIC_DEFINITIONS dict** for glossary (14 metrics with name, short description, formula).

**generate_dashboard_data():**
1. Run SuperhumanPredictor.predict()
2. Load injury data (if available)
3. Build team array: rank, code, name, city, conference, division, tier, tierColor, tierBg, tierIcon, compositeStrength, strengthRank, playoffProbability (×100), conferenceProbability, cupFinalProbability, cupProbability, cupProbLower, cupProbUpper, injuries, totalWarLost
4. Build feature weights array: key, name, description, weight (sorted by weight descending)
5. Build tier summary, playoff picture (top 8 per conf by playoff prob), cup favorites (top 10)
6. Build round advancement from MC: round1, round2, confFinal, cupFinal, cupWin (all × 100)
7. Build bracket: projected (from MC) + actual (from current standings)
8. Generate backtest report
9. Detect significant changes from previous snapshot (tier changes, 5+ rank jumps, 3%+ odds swings)
10. Include last 30 days of history

**build_projected_bracket(mc_result):** Transforms MC results into bracket structure:
- Per conference: round1 (4 matchups with higher/lower/higherWinProb), round2 (2 slots, each with ranked matchup possibilities), confFinal (top 3 matchup possibilities)
- Cup Final: top 5 most likely matchups
- Champion: team with highest cup probability
- Projected seeds using select_conference_playoff_teams()

**build_actual_bracket():** Reads nhl_standings.json, builds bracket using real NHL seeding rules.

**save_historical_snapshot():** Saves date + team code/rank/tier/strength/playoffProb/cupProb to history/ directory.

**Output → dashboard_data.json:**
```json
{
  "meta": {
    "generated": "2026-02-03T19:46:08.729936",
    "season": 2026,
    "seasonDisplay": "2025-26",
    "modelVersion": "2.1 - Full Bracket Model",
    "lastUpdate": "February 03, 2026 at 07:46 PM"
  },
  "teams": [ { "rank": 1, "code": "COL", "name": "Colorado Avalanche", "city": "Denver",
               "conference": "West", "division": "Central", "tier": "Elite",
               "tierColor": "#10b981", "tierBg": "rgba(16, 185, 129, 0.15)", "tierIcon": "🏆",
               "compositeStrength": 63.2, "strengthRank": 1,
               "playoffProbability": 100.0, "conferenceProbability": 31.57,
               "cupFinalProbability": 16.53, "cupProbability": 11.1,
               "cupProbLower": 10.6, "cupProbUpper": 11.63,
               "injuries": [...], "totalWarLost": 3.3 }, ... ],
  "featureWeights": [ { "key": "vegas_cup_signal", "name": "Vegas Signal (Implied Odds)",
                        "description": "...", "weight": 22.5 }, ... ],
  "tierSummary": { "Elite": ["COL", "CAR", ...], ... },
  "tierConfig": { "Elite": { "color": "#10b981", ... }, ... },
  "playoffPicture": { "East": [...], "West": [...] },
  "cupFavorites": [...],
  "roundAdvancement": { "COL": { "round1": 100.0, "round2": 55.3, "confFinal": 31.57,
                                  "cupFinal": 16.53, "cupWin": 11.1 }, ... },
  "bracket": {
    "projected": {
      "East": {
        "round1": [ { "higher": "CAR", "lower": "BUF", "higherWinProb": 59.3 }, ... ],
        "round2": [ { "slot": 0, "matchups": [ { "teamA": "MTL", "teamB": "TB",
                       "teamAWinProb": 45.5, "matchupProb": 18.2 }, ... ] }, ... ],
        "confFinal": [ { "teamA": "CAR", "teamB": "TB", "teamAWinProb": 52.0, "matchupProb": 9.8 }, ... ]
      },
      "West": { ... },
      "cupFinal": [ { "teamA": "COL", "teamB": "CAR", "teamAWinProb": 54.3, "matchupProb": 5.1 }, ... ],
      "champion": { "team": "COL", "probability": 11.1 },
      "projectedSeeds": { "East": [ { "team": "CAR", "projectedPts": 112.3 }, ... ], ... }
    },
    "actual": { ... }
  },
  "backtest": { "summary": { ... }, "seasons": [ ... ] },
  "glossary": { ... },
  "recentChanges": [ { "type": "tier_change", "team": "BOS", "from": "Contender", "to": "Elite", ... }, ... ],
  "history": [ ... ]
}
```

---

## PART 3: WEB DASHBOARD

### 3A. index.html — Main Entry Point

Standalone HTML file. Loads:
- Google Fonts: Space Grotesk (400,500,600,700) + JetBrains Mono (400,500)
- css/style.css
- 8 JS modules in order: data.js, app.js, rankings.js, playoff-race.js, betting.js, bracket.js, performance.js, insights.js

**Structure:**
```html
<header class="site-header">
  <!-- Title: "Superhuman NHL Predictions" -->
  <!-- Season label + Last Updated timestamp (clickable for freshness popover) -->
</header>
<nav class="tab-bar">
  <!-- 6 tabs: Rankings, Playoff Race, Betting Value, Bracket, Model Performance, Insights -->
  <!-- Each is <button class="tab" data-tab="..."> -->
</nav>
<main id="tab-content">
  <!-- Dynamically populated by JS -->
</main>
<footer class="site-footer">
  <!-- Glossary link, GitHub link, "Powered by Superhuman v2.1" -->
</footer>
```

### 3B. css/style.css — Complete Design System (~1800 lines)

**Color Palette (CSS Custom Properties):**
```css
--bg-primary: #0a0e17;         /* Main background - very dark blue */
--bg-secondary: #111827;       /* Header/footer */
--bg-card: #1a2234;            /* Card backgrounds */
--bg-hover: #243047;           /* Hover state */
--bg-input: #151d2e;           /* Input fields */
--text-primary: #f0f4f8;       /* Main text - off-white */
--text-secondary: #94a3b8;     /* Secondary text */
--text-muted: #64748b;         /* Muted text */
--tier-elite: #10b981;         /* Green */
--tier-contender: #3b82f6;     /* Blue */
--tier-bubble: #f59e0b;        /* Amber */
--tier-longshot: #ef4444;      /* Red */
--accent: #6366f1;             /* Indigo - interactive elements */
--accent-hover: #818cf8;       /* Lighter indigo */
--border-color: #2d3a4f;       /* Borders */
--shadow-sm/md/lg              /* Graduated shadow system */
--space-xs/sm/md/lg/xl/2xl     /* 4/8/16/24/32/48px spacing scale */
--max-width: 1280px;           /* Container max width */
```

**Typography:** Space Grotesk for body, JetBrains Mono for numbers/stats/probabilities.

**Key Components:**
- **Tier badges:** Semi-transparent colored backgrounds with matching borders/text
- **Data tables:** Sticky headers, sortable columns with triangle indicators, row hover effects, tier-colored left border (inset 3px box-shadow)
- **Filter chips:** Pill-shaped (border-radius: 999px), indigo active state
- **Stat cards:** Vertical layout with label (uppercase, tiny), value (1.75rem mono), delta (color-coded)
- **Progress bars:** 6px height, tier-colored fills
- **Confidence intervals:** Horizontal bar with range bar (indigo) and center point circle
- **Bracket layout:** 3-column grid [East | Cup Final | West], matchup cards with team pairs separated by divider, TBD states with dashed borders, frequency text below matchups
- **Off-season banner:** Amber with transparency, hidden by default

**Responsive:**
- Tablet (≤768px): Single column, reduced spacing, stacked layout
- Mobile (≤480px): Minimal padding, hidden team logos, smaller fonts

### 3C. js/app.js — Application Bootstrap

**init():** Loads data → sets up tabs → updates header → renders initial tab (from URL hash or defaults to rankings).

**loadData():** Fetches `dashboard_data.json` via HTTP. Falls back to `window.DASHBOARD_DATA` (for file:// protocol). Error state if both fail.

**setupTabs():** Click handlers on tab buttons. Manages `data-tab` attributes, URL hash routing (#rankings, #bracket, etc.).

**updateHeader():** Populates season label, formats last-updated timestamp, detects off-season (data >30 days old shows amber banner).

**showFreshnessPopover():** Dynamic popover showing model version, generation time, season info. Positioned below timestamp, closes on click outside.

**Utils object:**
- `tierClass(tier)` → CSS class name
- `tierColor(tier)` → hex color
- `pct(val, decimals=1)` → formatted percentage
- `sortTable(tableId, colIdx, type='number')` → in-place table sort with direction toggle

### 3D. js/rankings.js — Rankings Tab

Top 3 stat cards → full sortable/filterable table → feature weights visualization.

**Table columns:** Rank, Team (with 24x24 logo), Tier badge, Conference, Strength, Playoff%, Conference%, Cup%, Injuries.

**Filters:** All, East, West, Elite, Contender (filter chips).

**Sorting:** Click column headers for ascending/descending toggle. Triangle indicators.

### 3E. js/playoff-race.js — Playoff Race Tab

Two-column grid: Eastern & Western Conference standings.

**Playoff line:** Row 8 has special amber bottom border (playoff cutoff).

**Rows 0-7:** Full opacity (in-playoffs class). Rows 8+: 0.6 opacity (out-playoffs).

**Bubble Watch:** Cards for teams ranked 6-10 per conference with probability bars (green if ≥50%, amber if <50%).

### 3F. js/betting.js — Betting Value Tab

**Manual odds input:** American format (+800, -150). Stored in localStorage (`nhl-betting-odds`).

**Edge calculation:** Model% - Implied%. `oddsToImplied`: if positive: 100/(odds+100)*100, if negative: |odds|/(|odds|+100)*100.

**Signals:** VALUE (5%+ edge), Lean (2-5%), Fade (≤-5%), Fair.

### 3G. js/bracket.js — Bracket Tab

**Projected mode:** Monte Carlo simulation results with win probabilities and "X% of sims" frequency. 3-column layout: [East R1→R2→CF] | [Cup Final + Champion] | [West CF←R2←R1].

**Actual mode:** Current standings-based bracket with seeding (D1, D2, D3, WC1, WC2).

**Round Advancement Table:** Probability of advancing to each round for all teams.

**Matchup card structure:**
```
[Seed] [TeamCode] [TierDot]     [Win%]
[Seed] [TeamCode] [TierDot]     [Win%]
        X% of sims
```

### 3H. js/performance.js — Model Performance Tab

Summary stat cards: Seasons tested, Top pick accuracy, Winner in top 5, Random baseline (3%).

Season-by-season backtest table: Season, Model #1, Model Top 5, Actual Winner, In Top 5? (checkmark/X), Winner Prob.

### 3I. js/insights.js — Insights Tab

Auto-generated insight cards:
1. **Cup Favorite** (highlight): Top team + Cup% + strength
2. **Dark Horse** (upset): Bubble team with high odds
3. **Injury Impact** (injury): Most injured contender
4. **Conference Gap** (analysis): Elite count comparison
5. **Tier Distribution** (analysis): Count per tier
6. **Separation** (analysis): Biggest Cup% gap between adjacent teams
7. **Key Drivers** (model): Top 2 feature weights

Color-coded by type: highlight=green, upset=amber, injury=red, analysis=blue, model=indigo.

---

## PART 4: TESTS

### 4A. tests/conftest.py — Shared Fixtures (session-scoped)

```python
@pytest.fixture(scope="session")
def teams_data():
    """Load data/teams.json"""

@pytest.fixture(scope="session")
def teams_list(teams_data):
    """Return teams_data['teams'] array"""

@pytest.fixture(scope="session")
def dashboard_data():
    """Load dashboard_data.json"""

@pytest.fixture(scope="session")
def dashboard_soup():
    """Parse index.html with BeautifulSoup + lxml"""
```

### 4B. tests/test_dashboard.py — 6 Tests

1. `test_nav_tabs_present` — All 6 tab labels found in HTML
2. `test_tab_buttons_have_data_attributes` — 6 buttons with correct data-tab set {rankings, playoff-race, betting, bracket, performance, insights}
3. `test_tab_content_container_present` — #tab-content element exists
4. `test_page_title_contains_nhl` — Title tag contains "NHL"
5. `test_no_unclosed_tags` — Matching open/close tags for div, section, script, style
6. `test_data_freshness_element` — Has #lastUpdated, .last-updated, or text containing "last updated"/"as of"

### 4C. tests/test_data_pipeline.py — 8 Tests

Required fields: ["team", "name", "conf", "div", "gp", "w", "l", "pts", "weight"]

1. `test_has_32_teams` — Exactly 32 teams
2. `test_required_fields_present` — All required fields per team
3. `test_weight_field_is_numeric` — Weight is int/float, 0-1000 range
4. `test_all_team_abbreviations_present` — Set matches config.ALL_TEAMS
5. `test_conference_division_assignments` — Matches config.TEAM_INFO
6. `test_no_duplicate_teams` — List length == set length
7. `test_metadata_present` — Has _metadata with version, generatedAt, sources (dict)
8. `test_numeric_fields_in_valid_ranges` — Uses config.VALID_RANGES, PDO auto-converts if <2

### 4D. tests/test_superhuman.py — 6 Tests

Valid tiers: {"Elite", "Contender", "Bubble", "Longshot"}
Tier colors: Elite=#10b981, Contender=#3b82f6, Bubble=#f59e0b, Longshot=#ef4444

1. `test_has_32_teams` — 32 teams in dashboard_data
2. `test_cup_probabilities_sum_to_100` — Sum ≈ 100 (within 5 points)
3. `test_playoff_probabilities_in_range` — Each team 0-100%
4. `test_valid_tiers` — Each team.tier in valid set
5. `test_tier_colors_match` — tierColor matches expected per tier
6. `test_meta_section` — Has season, modelVersion, generated

### pytest.ini

```ini
[pytest]
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    visual: Visual/UI tests
```

---

## PART 5: CI/CD — GitHub Actions

### .github/workflows/update-stats.yml

**Trigger:** Daily at 11:00 UTC (6 AM EST) + manual dispatch.

**Runner:** ubuntu-latest, Python 3.11

**19 Steps:**
1. Checkout repository (actions/checkout@v4)
2. **Off-season check** (skip July-September): `if month 7-9 → skip=true`
3. Set up Python 3.11 (actions/setup-python@v5)
4. Install dependencies: `pip install -r scripts/requirements.txt`
5. Fetch NHL API (`continue-on-error: true`)
6. Fetch MoneyPuck (`continue-on-error: true`)
7. Scrape NST (`continue-on-error: true`)
8. Fetch odds (`continue-on-error: true`)
9. Fetch injuries (`continue-on-error: true`)
10. **Merge all data** (NO continue-on-error — fails workflow if merge fails)
11. **Validate data** (NO continue-on-error)
12. Generate superhuman predictions: `python -m superhuman.dashboard_generator` (`continue-on-error: true`)
13. **Create GitHub issue on model failure** (using actions/github-script@v7, checks for existing open issue to avoid duplicates)
14. Install test dependencies
15. **Run tests:** `python -m pytest tests/ -v`
16. **Weekly snapshot (Mondays only):** Copy teams.json + dashboard_data.json to data/snapshots/ with date suffix. Keep only last 4 snapshots.
17. **Check for changes:** `git diff --cached --quiet` on data/ + dashboard_data.json + history/
18. **Commit and push** (if changes): Git user = "GitHub Actions Bot", message = "Update NHL stats - YYYY-MM-DD HH:MM UTC"
19. Report status (team count confirmation)

Steps 3-19 are conditional on `steps.season_check.outputs.skip != 'true'`.

---

## PART 6: DEPENDENCIES

### scripts/requirements.txt
```
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
lxml>=4.9.0
numpy>=1.24.0
scikit-learn>=1.3.0
scipy>=1.11.0
```

### scripts/requirements-test.txt
```
pytest>=7.0
beautifulsoup4
lxml
```

### .gitignore
```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
.idea/
.vscode/
*.swp
*.swo
.DS_Store
Thumbs.db
node_modules/
js/data.js
*.tmp
*.log
```

---

## PART 7: KEY HOCKEY CONCEPTS

- **HDCF% (High-Danger Corsi For %):** Best single predictor of playoff success. Measures quality scoring chances.
- **GSAx (Goals Saved Above Expected):** Goaltending quality. Positive = saves more than expected.
- **CF% (Corsi For %):** Territorial control. Shot attempt differential at 5v5.
- **PDO:** Shooting% + Save%. Regresses toward 100. >102 = likely unsustainable.
- **xGF% (Expected Goals For %):** Possession quality accounting for shot location.
- **NHL Playoff Qualification:** Top 3 per division + 2 best remaining as wildcards per conference. Division winners seed 1-2 by points. Seed 1 vs WC2, Seed 2 vs WC1, 2nd vs 3rd within divisions.

---

## DESIGN PHILOSOPHY

- **Dark theme** (#0a0e17 base) with glass-card aesthetic
- **Tier color coding** consistent across ALL views (green/blue/amber/red)
- **Monospace numbers** (JetBrains Mono) for data precision feel
- **No frontend framework** — vanilla HTML/CSS/JS for zero build step
- **Data refreshes daily** but dashboard is static (reads from JSON files)
- **Graceful degradation** — pipeline continues even if individual sources fail
- **Confidence intervals** shown for Cup probabilities (Beta distribution, 90% CI)
- **Percentile-based tiers** (Top 4/8/8/12) instead of fixed thresholds
- **Monte Carlo with real NHL seeding rules** — not simplified 1-8 matchups

---

## NOTES FOR RECREATION

1. **Always use `python3`** on macOS (not `python`)
2. **MoneyPuck scraping is fragile** — use `continue-on-error` in CI
3. **NST data is PRIMARY** for advanced stats; MoneyPuck is backup
4. **Cup probabilities MUST sum to ~100%** — normalized after ensemble
5. **Synthetic training data** generates independent stats to prevent artificial correlations
6. **js/data.js is auto-generated** — fallback for file:// protocol (no HTTP server)
7. **Dashboard loads dashboard_data.json via fetch()** with fallback to window.DASHBOARD_DATA
8. **Projected R1 matchups use top-4-by-frequency** (no hard threshold) because per-sim noise
9. **R2/CF thresholds: 5% of sims. Cup Final: 1%** due to combinatorial explosion
10. **Round advancement naming:** use what team HAS DONE — e.g., conf_final_appearance = won R2
