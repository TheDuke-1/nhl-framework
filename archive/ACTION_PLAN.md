# NHL Playoff Framework - Action Plan
## Next Steps & Priorities

Generated: January 30, 2026

---

## 🔴 HIGH PRIORITY

### 1. Automate Daily Data Refresh
**Why:** Currently data must be refreshed manually. Stale data = bad predictions.

**Action:**
- Set up a scheduled task (cron job or Task Scheduler) to run `python scripts/refresh_data.py` daily
- Recommended time: Early morning (6 AM) before games start
- Alternative: Use GitHub Actions if hosting on GitHub

**Effort:** Low (30 min)

---

### 2. Add Historical Backtesting Module
**Why:** The framework has weights (HDCF% 25%, CF% 20%, etc.) but no validation these weights actually predict playoff success. Need to prove the model works.

**Action:**
- Gather historical data (past 5-10 seasons)
- Calculate what each team's "weight score" was at regular season end
- Compare against actual playoff results (rounds won)
- Tune weights based on what actually predicts success

**Effort:** High (1-2 weeks)

---

### 3. Add Playoff Probability Calculator
**Why:** Currently shows "tiers" (Elite, Contender, etc.) but not actual probabilities. Users want to know "what are the odds Colorado wins the Cup?"

**Action:**
- Use Monte Carlo simulation based on team weights
- Simulate thousands of playoff brackets
- Output probability for each round (make playoffs, win round 1, conference finals, Cup)

**Effort:** Medium (3-5 days)

---

## 🟡 MEDIUM PRIORITY

### 4. Improve MoneyPuck Data Fetching
**Why:** MoneyPuck blocks Python requests, requiring manual browser fetch. This breaks automation.

**Action:**
- Investigate if MoneyPuck has an API
- Try Selenium/Playwright for headless browser fetching
- Or: Find alternative source for expected goals data

**Effort:** Medium (2-3 days)

---

### 5. Add Player-Level Data
**Why:** Framework tracks "hasStar" and "depth20g" but doesn't use real player stats. Missing injuries, hot streaks, trade impacts.

**Action:**
- Integrate player stats from NHL API
- Track injuries and their impact
- Add "star player" performance to weight calculation
- Consider recent player form (last 10 games)

**Effort:** High (1-2 weeks)

---

### 6. Dashboard Enhancements
**Why:** Current dashboard is functional but could be more actionable.

**Action:**
- Add "what changed" section showing biggest movers week-over-week
- Add head-to-head comparison tool
- Add "schedule strength" for remaining games
- Mobile-responsive improvements

**Effort:** Medium (3-5 days)

---

## 🟢 NICE TO HAVE

### 7. Add Betting Value Calculator
**Why:** If the model predicts better than Vegas, there's value in identifying mispriced odds.

**Action:**
- Integrate odds feeds (OddsAPI or similar)
- Compare model probabilities vs implied odds
- Flag "value bets" where model disagrees with market

**Effort:** Medium (1 week)

---

### 8. Add Alert System
**Why:** Users shouldn't have to check dashboard daily. Push important changes to them.

**Action:**
- Set up email/SMS alerts for:
  - Team moves up/down a tier
  - Significant metric changes (>5% weight change)
  - Data refresh failures
- Could use Twilio/SendGrid

**Effort:** Medium (3-5 days)

---

### 9. Add Conference/Division Breakdowns
**Why:** Playoff seeding is by conference. Would help to see East vs West comparisons.

**Action:**
- Add conference standings view
- Show wildcard race scenarios
- Division leader tracking

**Effort:** Low (1-2 days)

---

## Recommended Order of Execution

| Priority | Task | Why First |
|----------|------|-----------|
| 1 | Automate Daily Refresh | Low effort, immediate reliability win |
| 2 | Historical Backtesting | Validates the entire model - critical for trust |
| 3 | Playoff Probability | Users' #1 requested feature |
| 4 | MoneyPuck Fix | Fixes automation gap |
| 5 | Player Data | Biggest accuracy improvement potential |

---

## Current System Status

✅ **Working:**
- NHL API standings (verified against NHL.com)
- Natural Stat Trick advanced stats
- MoneyPuck expected goals (manual refresh)
- Data merge pipeline
- HTML dashboard with live data loading
- Validation checks

⚠️ **Needs Attention:**
- MoneyPuck requires browser-based fetch
- No backtesting to validate weights
- No playoff probability output

---

*This action plan will be updated as work progresses.*
