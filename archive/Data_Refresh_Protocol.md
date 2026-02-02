# NHL Framework V7.1 - Data Refresh Protocol

**Version:** 7.1
**Last Updated:** January 25, 2026

---

## Refresh Frequency Recommendations

| Data Type | Frequency | Rationale |
|-----------|-----------|-----------|
| Standings (W-L-OTL, PTS) | Daily | Points race changes nightly |
| GSAx / xG metrics | 3x per week | Sample size stability |
| HDCF% / CF% / PDO | Weekly | Stable over time |
| 30-Day Rolling GSAx | 3x per week | Captures momentum |
| Road splits | Weekly | Accumulates slowly |
| Faceoff stats | Weekly | Stable |
| Injuries | Daily | Rapid changes |
| Futures odds | Before placing bets | Market-dependent |

---

## Data Source Instructions

### 1. NHL API - Standings & Basic Stats

**URL:** `https://api-web.nhle.com/v1/standings/now`

**Data provided:**
- Games played, W, L, OTL, Points
- Goals For, Goals Against
- Home/Road splits
- Recent form (L10)

**Refresh steps:**
1. Navigate to the API endpoint or use existing `fetch_nhl_api.py` script
2. Run: `python scripts/fetch_nhl_api.py`
3. Output saved to: `data/nhl_standings.json`
4. Copy relevant values to "Data Input" tab in spreadsheet

**Fields to update in spreadsheet:**
- GP, W, L, OTL, PTS (columns F-J in Team Rankings)
- GF, GA (for GD calculation)
- Road W, Road L, Road OTL (Road Performance tab)

---

### 2. MoneyPuck - Advanced Metrics

**URL:** `https://moneypuck.com/data.htm`

**Data provided:**
- GSAx (Goals Saved Above Expected)
- xG (Expected Goals For/Against)
- HDCF% (High-Danger Corsi For %)
- Shot quality metrics

**Refresh steps:**
1. Visit MoneyPuck data page
2. Download "Team Stats" CSV for current season
3. Run: `python scripts/fetch_moneypuck.py` (if configured)
4. Or manually extract values from CSV

**CSV columns to extract:**
- `xGoalsFor`, `xGoalsAgainst` → Calculate xGD
- `highDangerxGoalsFor`, `highDangerxGoalsAgainst` → HDCF%
- Goalie data: `GSAx` from goalie table

**Fields to update in spreadsheet:**
- GSAx, 30-Day GSAx, HD SV% (Goaltending Detail tab)
- HDCF%, xGD, xGA (Team Rankings columns K-M)

---

### 3. Natural Stat Trick - Possession Metrics

**URL:** `https://naturalstattrick.com/teamtable.php`

**Data provided:**
- CF% (Corsi For Percentage)
- PDO (Shooting % + Save %)
- Score-adjusted metrics
- Situational breakdowns

**Refresh steps:**
1. Navigate to Natural Stat Trick team table
2. Set filters: 5v5, Score-adjusted (optional)
3. Export or manually record:
   - CF%
   - PDO
   - FF% (Fenwick For %)

**Note:** NST may require manual extraction. The automated scraper (`scrape_nst.py`) may not work without browser automation.

**Fields to update in spreadsheet:**
- CF% (column N)
- PDO (column AI)

---

### 4. DailyFaceoff - Injuries & Lines

**URL:** `https://www.dailyfaceoff.com/teams/`

**Data provided:**
- Current line combinations
- Injury status
- Projected lineups

**Refresh steps:**
1. Navigate to team page for each team of interest
2. Check injury report section
3. Note any significant injuries (starter goalie, top-6 F, top-4 D)
4. Document in notes column or separate tracking

**Manual documentation recommended** - no automated scraping available.

---

### 5. Odds - Manual Entry

**Your sportsbook of choice**

**Data needed:**
- Stanley Cup futures odds (American format)
- Conference winner odds (if betting)
- Division winner odds (if betting)

**Refresh steps:**
1. Log into your sportsbook
2. Navigate to NHL Futures
3. Record current odds for teams of interest
4. Enter in "Betting Dashboard" tab, column C (Odds)

**Timing:** Update odds immediately before making any betting decisions.

---

## Data Validation Checks

After each refresh, verify:

### Completeness Check
- [ ] All 32 teams have data
- [ ] No blank cells in required columns
- [ ] Timestamp updated in "Data Input" tab

### Sanity Checks
- [ ] Points totals reasonable (no team >164 points)
- [ ] Win + Loss + OTL ≤ 82 per team
- [ ] GSAx values between -30 and +30
- [ ] HDCF% values between 40% and 60%
- [ ] PDO values between 95 and 105

### Cross-Reference Verification
Choose 3 random teams and verify:
- [ ] Points match NHL.com standings
- [ ] GSAx matches MoneyPuck
- [ ] Record matches official stats

---

## Troubleshooting Common Issues

### Issue: NHL API returns error
**Solution:** Check if API endpoint has changed. Try:
- `https://api-web.nhle.com/v1/standings/now`
- `https://statsapi.web.nhl.com/api/v1/standings` (legacy)

### Issue: MoneyPuck CSV format changed
**Solution:** Re-map column names in `fetch_moneypuck.py` or manual extraction.

### Issue: GSAx values seem wrong
**Solution:**
- Verify you're looking at 5v5 data (not all situations)
- Check if MoneyPuck has updated their methodology
- Cross-reference with EvolvingHockey if available

### Issue: Spreadsheet formulas show #REF!
**Solution:**
- Check if team rows were added/deleted
- Verify RANK formulas reference correct range ($C$2:$C$33)
- Run formula recalculation (F9 in Excel)

---

## Automation Options

### Option A: Python Scripts (Current)
```bash
# Run all data fetches
cd /path/to/NHL\ Playoff\ Project
python scripts/fetch_nhl_api.py
python scripts/fetch_moneypuck.py
python scripts/merge_data.py
```

### Option B: Scheduled Task
Set up cron job (Linux/Mac) or Task Scheduler (Windows):
```bash
# Daily at 8 AM
0 8 * * * cd /path/to/project && python scripts/fetch_nhl_api.py
```

### Option C: Browser Automation
For sites requiring JavaScript rendering:
1. Install Playwright or Selenium
2. Configure headless browser
3. Add to scraping scripts

---

## Pre-Bet Checklist

Before placing any bet based on model output:

1. [ ] Data refreshed within last 24 hours
2. [ ] Odds entered are current (check timestamp)
3. [ ] No major injuries since last refresh
4. [ ] Edge% exceeds threshold (default 5%)
5. [ ] CLV tracking shows positive historical skill
6. [ ] Bet size within Kelly recommendations
7. [ ] Total exposure within bankroll limits

---

## Weekly Refresh Routine

**Monday:**
- Full data refresh from all sources
- Update spreadsheet
- Review team rankings changes

**Wednesday:**
- Update GSAx / xG metrics
- Check injury updates
- Review any odds movement

**Friday (or before weekend games):**
- Final pre-weekend refresh
- Update odds if placing bets
- Document CLV from any resolved bets

---

## Contact & Resources

**Data Sources:**
- NHL API: api-web.nhle.com
- MoneyPuck: moneypuck.com/data.htm
- Natural Stat Trick: naturalstattrick.com
- DailyFaceoff: dailyfaceoff.com

**Framework Documentation:**
- Methodology: `Framework_Methodology_V7.1.md`
- Quick Reference: `Quick_Reference_V7.1.md`
- Backtest Results: `Backtest_Results_V7.1.md`

---

*Protocol Version: 7.1 | Last Updated: January 25, 2026*
