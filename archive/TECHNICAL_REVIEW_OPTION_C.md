# Option C: Technical Review
## Detailed Diagnosis & Planned Fixes

---

## 1. NST Scraper Diagnosis

### Current Code Analysis (`scrape_nst.py`)

**What the scraper does:**
1. Sends GET request to `https://naturalstattrick.com/teamtable.php` with params
2. Looks for table with `id='teams'`, falls back to `class='sortable'`, then any `<table>`
3. Parses rows using BeautifulSoup's `lxml` parser
4. Maps team names to abbreviations using `TEAM_NAME_MAP`

**Current Output:** `teamCount: 0` (zero teams parsed)

### Likely Failure Points (in priority order):

| # | Hypothesis | Evidence | Likelihood |
|---|------------|----------|------------|
| 1 | **Table selector mismatch** | NST may have changed table ID/class | HIGH |
| 2 | **Bot detection/blocking** | NST may block non-browser requests | MEDIUM |
| 3 | **Season parameter format** | Using `20252026` - may need `2025-2026` | LOW |
| 4 | **JavaScript rendering** | Table may load via JS (BeautifulSoup can't handle) | MEDIUM |
| 5 | **Row parsing logic** | `len(cells) < 5` check may skip valid rows | LOW |

### Key Code Sections:

```python
# Lines 184-191 - Table finding logic
table = soup.find('table', {'id': 'teams'})  # May no longer exist
if not table:
    table = soup.find('table')  # Falls back to first table

# Lines 219-221 - Row parsing
rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]
for row in rows:
    cells = row.find_all('td')
    if len(cells) < 5:  # This may skip rows if structure changed
        continue
```

### Diagnostic Steps Needed:
1. Fetch raw HTML and inspect actual table structure
2. Check if request returns valid HTML or error page
3. Verify column headers match expected format
4. Test if `requests` is being blocked (User-Agent may be insufficient)

---

## 2. MoneyPuck Data Assessment

### Current Fetch Analysis (`fetch_moneypuck.py`)

**What it extracts:**
| Metric | Extracted? | Status |
|--------|------------|--------|
| xGF/xGA | ✅ Yes | Working |
| GSAx | ✅ Yes | Working |
| CF/CA | ⚠️ Attempted | Returns 0 for all teams |
| HDCF% | ❌ **NO** | Not in fetch script |
| SCF% | ❌ No | Not extracted |

### Critical Finding: HDCF% Not Extracted

The MoneyPuck CSV **does contain** High-Danger Corsi data, but `fetch_moneypuck.py` doesn't extract it:

```python
# Lines 107-120 - Current extraction (HDCF% MISSING)
teams[abbrev] = {
    "xgf": round(row.get('xGoalsFor', 0), 2),
    "xga": round(row.get('xGoalsAgainst', 0), 2),
    "gsax": round(row.get('goalsAgainst', 0) - row.get('xGoalsAgainst', 0), 2) * -1,
    "cf": round(row.get('corsiFor', 0), 0),  # Returns 0 - column name mismatch?
    # NO hdcfPct extraction!
}
```

### MoneyPuck CSV Column Names (need verification):
- `highDangerxGoalsFor`, `highDangerxGoalsAgainst` - for HDCF%
- `mediumDangerxGoalsFor`, `mediumDangerxGoalsAgainst` - for MDCF%
- `flurryAdjustedxGoalsFor` - may have different naming

### Why CF = 0 for All Teams:
The CSV column is likely `corsiFor` with different capitalization or naming. Need to check actual CSV headers.

---

## 3. PP%/PK% Parsing Bug

### Current Code (`fetch_nhl_api.py` Lines 64-65):

```python
"ppPct": round(team_data.get("powerPlayPctg", 0) * 100, 1) if team_data.get("powerPlayPctg") else 0,
"pkPct": round(team_data.get("penaltyKillPctg", 0) * 100, 1) if team_data.get("penaltyKillPctg") else 0,
```

### The Bug:
The `if team_data.get("powerPlayPctg")` condition uses **truthiness**.
- If API returns `0.0` (legitimate value), this evaluates to `False`
- If API returns `null` or is missing, this evaluates to `False`
- Result: Always returns `0` for both cases

### Correct Fix:
```python
"ppPct": round(team_data.get("powerPlayPctg", 0) * 100, 1) if team_data.get("powerPlayPctg") is not None else 0,
"pkPct": round(team_data.get("penaltyKillPctg", 0) * 100, 1) if team_data.get("penaltyKillPctg") is not None else 0,
```

### Risk Assessment: **LOW**
- Simple one-line fix
- No side effects
- Easy to verify

---

## 4. NST vs MoneyPuck Comparison

### Data Availability:

| Metric | NST | MoneyPuck | Framework Weight |
|--------|-----|-----------|------------------|
| HDCF% | ✅ Native | ✅ Available (not extracted) | **11%** |
| CF% | ✅ Native | ⚠️ Attempted (broken) | 2% |
| PDO | ✅ Native | ❌ Not available | 1% |
| xGF/xGA | ✅ Available | ✅ **Primary source** | 10% |
| SCF% | ✅ Native | ✅ Available | 0% (not in model) |

### Recommendation: **Fix NST First, MoneyPuck as Fallback**

**Rationale:**
1. NST provides HDCF%, CF%, AND PDO in one source
2. MoneyPuck extraction would need modification to get HDCF%
3. NST is the "gold standard" for process metrics in hockey analytics
4. If NST fails completely, MoneyPuck CAN provide HDCF% with code changes

---

## 5. Planned Code Changes

### Phase 1: Diagnose NST (30 min)

```
1. Fetch raw HTML from NST
2. Dump to file for inspection
3. Identify correct table selectors
4. Check for bot blocking
5. Verify season parameter format
```

### Phase 2: Fix NST Scraper (if fixable)

**Estimated changes:**
- Update table selector (likely 1-2 lines)
- Update column name mapping (5-10 lines)
- Add better error logging (3-5 lines)

### Phase 3: If NST Unfixable → MoneyPuck Enhancement

**Required changes to `fetch_moneypuck.py`:**
```python
# Add HDCF% extraction (lines ~115-120)
"hdcf": round(row.get('highDangerCorsiFor', 0), 0),
"hdca": round(row.get('highDangerCorsiAgainst', 0), 0),
"hdcfPct": calculate_percentage(hdcf, hdca),
```

### Phase 4: Fix PP%/PK% Bug (5 min)

**Single line change in `fetch_nhl_api.py`:**
```python
# Line 64 - change `if X` to `if X is not None`
```

### Phase 5: Create Validation Script (30 min)

**New file: `scripts/validate_data.py`**
```python
# Check all 32 teams have data
# Check HDCF% is not default 50.0 for all teams
# Check PP%/PK% are non-zero
# Check data freshness < 24 hours
# Exit with error code if validation fails
```

---

## 6. Risk Assessment

| Change | Risk | Impact if Failed | Mitigation |
|--------|------|------------------|------------|
| NST selector update | LOW | No data (same as now) | MoneyPuck fallback |
| MoneyPuck HDCF% add | LOW | Script fails | Test locally first |
| PP%/PK% fix | VERY LOW | Could return wrong values | Simple logic, easy test |
| Validation script | NONE | Just reporting | No data changes |

---

## 7. Verification Plan

After each fix, verify:

### NST Fix Verification:
```bash
python scripts/scrape_nst.py
# Check: teamCount should be 32
# Check: hdcfPct values should vary (not all 50.0)
# Check: cfPct values should be in 45-55 range
```

### MoneyPuck Fix Verification (if needed):
```bash
python scripts/fetch_moneypuck.py
# Check: hdcfPct field exists
# Check: values vary by team
```

### PP%/PK% Fix Verification:
```bash
python scripts/fetch_nhl_api.py
cat data/nhl_standings.json | grep ppPct
# Check: values should be 15-30 range, not 0
```

### Full Pipeline Verification:
```bash
python scripts/fetch_nhl_api.py
python scripts/fetch_moneypuck.py
python scripts/scrape_nst.py
python scripts/merge_data.py
# Check teams.json has non-default values for all metrics
```

---

## 8. MoneyPuck Data Currency Check

Before switching to MoneyPuck as fallback, need to verify:

1. **Is the CSV current?** Check headers for season/date
2. **Does it have HDCF data?** Inspect column names
3. **Are values realistic?** Compare to known standings

### Verification Command:
```bash
curl -s "https://moneypuck.com/moneypuck/playerData/seasonSummary/2025/regular/teams.csv" | head -5
```

This will show:
- Column headers (verify HDCF columns exist)
- First few data rows (verify current season data)

---

## Summary: Execution Order

| Step | Action | Time Est. | Dependencies |
|------|--------|-----------|--------------|
| 1 | Diagnose NST (fetch raw HTML, inspect) | 15 min | None |
| 2 | Attempt NST fix based on diagnosis | 30 min | Step 1 |
| 3 | Test NST fix with feedback loop | 15 min | Step 2 |
| 4 | If NST fails: Check MoneyPuck CSV columns | 10 min | Step 3 failed |
| 5 | If needed: Enhance MoneyPuck fetch | 30 min | Step 4 |
| 6 | Fix PP%/PK% bug | 5 min | None (parallel) |
| 7 | Create validation script | 30 min | Steps 2-6 |
| 8 | Run full pipeline and verify | 15 min | All above |

**Total estimated time:** 1.5-2.5 hours depending on NST outcome

---

*Ready to proceed to Option B (NST Scraper Fix with Feedback Loop)?*
