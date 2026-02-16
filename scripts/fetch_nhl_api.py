#!/usr/bin/env python3
"""
Fetch NHL standings and team stats from the official NHL API.
Outputs: data/nhl_standings.json

Uses two API endpoints:
  - api-web.nhle.com/v1/standings — W/L/OTL/PTS/GF/GA, streaks, rankings
  - api.nhle.com/stats/rest — PP% and PK% (removed from standings endpoint)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from config import NHL_API_TEAM_MAP as TEAM_ABBREV_MAP, NST_TEAM_MAP as TEAM_NAME_MAP, SEASON_ID, NHL_API
from utils import fetch_json
from utils import FetchError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from league_calendar import get_data_activity_context

# NHL API endpoints (built from config)
STANDINGS_URL = NHL_API["standings"]
BACKUP_STANDINGS_URLS = [
    "https://api-web.nhl.com/v1/standings/now",
]
PP_STATS_URL = f"https://api.nhle.com/stats/rest/en/team/powerplay?cayenneExp=seasonId={SEASON_ID}"
PK_STATS_URL = f"https://api.nhle.com/stats/rest/en/team/penaltykill?cayenneExp=seasonId={SEASON_ID}"
CACHE_PATH = Path(__file__).parent.parent / "data" / "nhl_standings.json"

def _load_cached_teams() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if not CACHE_PATH.exists():
        return None, None
    try:
        payload = json.loads(CACHE_PATH.read_text())
    except Exception:
        return None, None
    teams = payload.get("teams")
    if not isinstance(teams, dict) or len(teams) < 30:
        return None, None
    return teams, payload.get("_metadata") if isinstance(payload.get("_metadata"), dict) else None


def fetch_standings() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Fetch current NHL standings with provider fallback chain."""
    transport_errors: List[str] = []

    print("Fetching NHL standings (primary)...")
    try:
        return fetch_json(STANDINGS_URL), {
            "provider": "nhl_primary_api_web",
            "url": STANDINGS_URL,
            "transportErrors": transport_errors,
            "usedCacheFallback": False,
        }
    except Exception as exc:
        transport_errors.append(f"{STANDINGS_URL}: {exc}")
        print(f"Primary standings endpoint failed: {exc}")

    for url in BACKUP_STANDINGS_URLS:
        print(f"Fetching NHL standings (backup): {url}")
        try:
            return fetch_json(url), {
                "provider": "nhl_backup_api_web",
                "url": url,
                "transportErrors": transport_errors,
                "usedCacheFallback": False,
            }
        except Exception as exc:
            transport_errors.append(f"{url}: {exc}")
            print(f"Backup standings endpoint failed: {exc}")

    calendar = get_data_activity_context()
    cached_teams, cached_meta = _load_cached_teams()
    if calendar.get("activityState") == "scheduled_break" and cached_teams:
        cached_at = str((cached_meta or {}).get("fetchedAt", "unknown"))
        print(f"EXPECTED_STATIC_FALLBACK: cache_snapshot ({cached_at})")
        return {
            "_cachedTeams": cached_teams,
            "_cachedMeta": cached_meta or {},
        }, {
            "provider": "cache_snapshot",
            "url": str(CACHE_PATH),
            "transportErrors": transport_errors,
            "usedCacheFallback": True,
            "cachedAt": cached_at,
        }

    raise FetchError("All NHL standings providers failed: " + " | ".join(transport_errors))

def fetch_pp_pk_stats():
    """Fetch PP% and PK% from the NHL stats API (separate from standings)."""
    pp_by_team = {}
    pk_by_team = {}

    # Fetch power play stats
    print("Fetching PP% from NHL stats API...")
    try:
        data = fetch_json(PP_STATS_URL)
        for row in data.get("data", []):
            name = row.get("teamFullName", "")
            abbrev = TEAM_NAME_MAP.get(name)
            if abbrev and "powerPlayPct" in row:
                raw = row["powerPlayPct"]
                pct = raw * 100 if raw < 1 else raw  # Handle both 0.225 and 22.5 formats
                if 5 <= pct <= 40:  # Sanity check: NHL PP% is always 5-40%
                    pp_by_team[abbrev] = round(pct, 1)
    except Exception as e:
        print("Warning: Could not fetch PP stats: %s" % e)

    # Fetch penalty kill stats
    print("Fetching PK% from NHL stats API...")
    try:
        data = fetch_json(PK_STATS_URL)
        for row in data.get("data", []):
            name = row.get("teamFullName", "")
            abbrev = TEAM_NAME_MAP.get(name)
            if abbrev and "penaltyKillPct" in row:
                raw = row["penaltyKillPct"]
                pct = raw * 100 if raw < 1 else raw  # Handle both 0.815 and 81.5 formats
                if 60 <= pct <= 95:  # Sanity check: NHL PK% is always 60-95%
                    pk_by_team[abbrev] = round(pct, 1)
    except Exception as e:
        print("Warning: Could not fetch PK stats: %s" % e)

    print("PP stats: %d teams, PK stats: %d teams" % (len(pp_by_team), len(pk_by_team)))
    return pp_by_team, pk_by_team

def parse_standings(data):
    """Parse standings data into our format."""
    if "_cachedTeams" in data and isinstance(data["_cachedTeams"], dict):
        return data["_cachedTeams"]

    teams = {}

    for team_data in data.get("standings", []):
        # Get team abbreviation
        api_abbrev = team_data.get("teamAbbrev", {}).get("default", "")
        abbrev = TEAM_ABBREV_MAP.get(api_abbrev, api_abbrev)

        if not abbrev:
            continue

        # Extract stats
        teams[abbrev] = {
            "team": abbrev,
            "teamName": team_data.get("teamName", {}).get("default", ""),
            "conf": "East" if team_data.get("conferenceName") == "Eastern" else "West",
            "div": team_data.get("divisionName", ""),
            "gp": team_data.get("gamesPlayed", 0),
            "w": team_data.get("wins", 0),
            "l": team_data.get("losses", 0),
            "otl": team_data.get("otLosses", 0),
            "pts": team_data.get("points", 0),
            "gf": team_data.get("goalFor", 0),
            "ga": team_data.get("goalAgainst", 0),
            "streak": team_data.get("streakCode", ""),
            "l10": f"{team_data.get('l10Wins', 0)}-{team_data.get('l10Losses', 0)}-{team_data.get('l10OtLosses', 0)}",
            "home": f"{team_data.get('homeWins', 0)}-{team_data.get('homeLosses', 0)}-{team_data.get('homeOtLosses', 0)}",
            "away": f"{team_data.get('roadWins', 0)}-{team_data.get('roadLosses', 0)}-{team_data.get('roadOtLosses', 0)}",
            # Note: powerPlayPctg and penaltyKillPctg were removed from the
            # standings endpoint. PP% and PK% now come from NST or other sources.
            "divRank": team_data.get("divisionSequence", 0),
            "confRank": team_data.get("conferenceSequence", 0),
            "leagueRank": team_data.get("leagueSequence", 0),
        }

        # Calculate recent form from L10
        l10_wins = team_data.get("l10Wins", 0)
        l10_losses = team_data.get("l10Losses", 0)
        l10_otl = team_data.get("l10OtLosses", 0)
        l10_total = l10_wins + l10_losses + l10_otl
        if l10_total > 0:
            teams[abbrev]["recentPts"] = (l10_wins * 2 + l10_otl) / (l10_total * 2) * 100
        else:
            teams[abbrev]["recentPts"] = 50.0

    return teams

def main():
    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Fetch and parse standings
    raw_data, provider_meta = fetch_standings()
    teams = parse_standings(raw_data)
    cached_teams, cached_meta = _load_cached_teams()

    # Fetch PP% and PK% from separate stats API
    pp_stats, pk_stats = fetch_pp_pk_stats()

    # Merge PP%/PK% into team data
    for abbrev, team in teams.items():
        if abbrev in pp_stats:
            team["ppPct"] = pp_stats[abbrev]
        if abbrev in pk_stats:
            team["pkPct"] = pk_stats[abbrev]
        # If PP/PK fetch failed for a team, carry forward known-good values from cache.
        if cached_teams and abbrev in cached_teams:
            if "ppPct" not in team and "ppPct" in cached_teams[abbrev]:
                team["ppPct"] = cached_teams[abbrev]["ppPct"]
            if "pkPct" not in team and "pkPct" in cached_teams[abbrev]:
                team["pkPct"] = cached_teams[abbrev]["pkPct"]

    now_iso = datetime.utcnow().isoformat() + "Z"
    fetched_at = now_iso
    if provider_meta.get("provider") == "cache_snapshot":
        fetched_at = str((cached_meta or {}).get("fetchedAt", now_iso))

    endpoints = [STANDINGS_URL, PP_STATS_URL, PK_STATS_URL]
    for backup_url in BACKUP_STANDINGS_URLS:
        if backup_url not in endpoints:
            endpoints.append(backup_url)

    calendar = get_data_activity_context()

    # Add metadata
    output = {
        "_metadata": {
            "source": "NHL API",
            "provider": provider_meta.get("provider"),
            "fallbackUsed": bool(provider_meta.get("provider") != "nhl_primary_api_web"),
            "activityState": calendar.get("activityState"),
            "checkedAt": now_iso,
            "fetchedAt": fetched_at,
            "teamCount": len(teams),
            "endpoints": endpoints,
            "transportErrors": provider_meta.get("transportErrors", []),
        },
        "teams": teams
    }

    # Write to file
    output_path = data_dir / "nhl_standings.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    if provider_meta.get("provider") == "nhl_backup_api_web":
        print(f"BACKUP_PROVIDER_USED: {provider_meta.get('url')}")
    if provider_meta.get("provider") == "cache_snapshot":
        print(f"BACKUP_PROVIDER_USED: cache_snapshot ({provider_meta.get('cachedAt')})")

    print(f"Saved {len(teams)} teams to {output_path}")
    return teams

if __name__ == "__main__":
    main()
