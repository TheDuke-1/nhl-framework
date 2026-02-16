"""
Real Data Loader - Load verified historical NHL data from JSON files
====================================================================
Reads from data/historical/verified/season_YYYY.json files produced
by scripts/fetch_historical.py. Each file contains standings, advanced
stats (NST), special teams (PP%/PK%), and playoff results.
"""

import json
import logging
import csv
from typing import List, Optional, Dict, Any
import numpy as np
from pathlib import Path

from .data_models import TeamSeason
from .config import HISTORICAL_DIR, normalize_team_abbrev as _normalize_team

logger = logging.getLogger(__name__)
_advanced_override_cache: Dict[int, Dict[str, Dict[str, float]]] = {}
MIN_OVERRIDE_TEAM_COVERAGE = 24


def _advanced_override_paths_for_season(season: int) -> tuple[Path, Path]:
    advanced_dir = HISTORICAL_DIR / "advanced"
    return (
        advanced_dir / f"season_{season}.json",
        advanced_dir / f"season_{season}.csv",
    )


def _estimate_expected_goal_profile(
    goals_for: int,
    goals_against: int,
    cf_pct: float,
    hdcf_pct: float
) -> tuple[float, float, float]:
    """
    Estimate xGF/xGA/xGF% when historical expected-goals feeds are unavailable.

    This proxy preserves signal and avoids all-zero xG features in historical
    training data. It is intentionally conservative and only used as fallback.
    """
    # Blend broad possession and high-danger share into an xG share proxy.
    xgf_pct_proxy = np.clip((0.65 * cf_pct) + (0.35 * hdcf_pct), 35.0, 65.0)

    # Convert the share into rough expected goals totals.
    # Values are scale-compatible and preserve team ordering.
    xgf_proxy = float(max(0.0, goals_for * (xgf_pct_proxy / 50.0)))
    xga_proxy = float(max(0.0, goals_against * ((100.0 - xgf_pct_proxy) / 50.0)))

    return xgf_proxy, xga_proxy, float(xgf_pct_proxy)


def _estimate_gsax_proxy(
    save_pct: float,
    games_played: int,
    ca: int
) -> float:
    """
    Estimate team-level GSAx proxy from save percentage and shot-volume proxy.
    """
    # League-average team save percentage baseline.
    league_sv = 0.910

    # Estimate shots against from Corsi Against where available.
    # If unavailable, use a conservative per-game shot estimate.
    shots_against_est = (ca * 0.55) if ca > 0 else (games_played * 30.0)
    shots_against_est = max(1000.0, shots_against_est)

    gsax_proxy = (save_pct - league_sv) * shots_against_est
    return float(np.clip(gsax_proxy, -40.0, 40.0))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_advanced_overrides_for_season(season: int) -> Dict[str, Dict[str, float]]:
    """
    Load optional season-level advanced metrics overrides.

    Supported files (under data/historical/verified/advanced):
    - season_YYYY.json: {"TEAM": {"xgf": ..., "xga": ..., "xgfPct": ..., "gsax": ...}, ...}
    - season_YYYY.csv: columns team,xgf,xga,xgfPct,gsax (case-insensitive aliases accepted)
    """
    if season in _advanced_override_cache:
        return _advanced_override_cache[season]

    json_path, csv_path = _advanced_override_paths_for_season(season)

    overrides: Dict[str, Dict[str, float]] = {}

    if json_path.exists():
        try:
            raw = json.loads(json_path.read_text())
            for team, vals in raw.items():
                if not isinstance(vals, dict):
                    continue
                team_code = _normalize_team(str(team).strip().upper())
                team_override: Dict[str, float] = {}
                if "xgf" in vals:
                    team_override["xgf"] = _safe_float(vals.get("xgf"), 0.0)
                if "xga" in vals:
                    team_override["xga"] = _safe_float(vals.get("xga"), 0.0)
                if "xgfPct" in vals or "xgf_pct" in vals:
                    team_override["xgfPct"] = _safe_float(vals.get("xgfPct", vals.get("xgf_pct")), 50.0)
                if "gsax" in vals:
                    team_override["gsax"] = _safe_float(vals.get("gsax"), 0.0)
                if team_override:
                    overrides[team_code] = team_override
        except Exception as e:
            logger.warning(f"Failed reading advanced override JSON for {season}: {e}")

    elif csv_path.exists():
        try:
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    team_raw = (
                        row.get("team")
                        or row.get("TEAM")
                        or row.get("teamAbbrev")
                        or row.get("team_abbrev")
                    )
                    if not team_raw:
                        continue
                    team_code = _normalize_team(str(team_raw).strip().upper())
                    team_override: Dict[str, float] = {}
                    if any(k in row and row.get(k) not in (None, "") for k in ("xgf", "XGF")):
                        team_override["xgf"] = _safe_float(row.get("xgf", row.get("XGF")), 0.0)
                    if any(k in row and row.get(k) not in (None, "") for k in ("xga", "XGA")):
                        team_override["xga"] = _safe_float(row.get("xga", row.get("XGA")), 0.0)
                    if any(k in row and row.get(k) not in (None, "") for k in ("xgfPct", "xgf_pct", "XGFPct")):
                        team_override["xgfPct"] = _safe_float(
                            row.get("xgfPct", row.get("xgf_pct", row.get("XGFPct", 50.0))),
                            50.0,
                        )
                    if any(k in row and row.get(k) not in (None, "") for k in ("gsax", "GSAx")):
                        team_override["gsax"] = _safe_float(row.get("gsax", row.get("GSAx")), 0.0)
                    if team_override:
                        overrides[team_code] = team_override
        except Exception as e:
            logger.warning(f"Failed reading advanced override CSV for {season}: {e}")

    _advanced_override_cache[season] = overrides
    if not overrides:
        return overrides

    if len(overrides) < MIN_OVERRIDE_TEAM_COVERAGE:
        logger.warning(
            f"Ignoring advanced overrides for {season}: "
            f"only {len(overrides)} teams (minimum {MIN_OVERRIDE_TEAM_COVERAGE})"
        )
        _advanced_override_cache[season] = {}
        return {}

    logger.info(f"Loaded advanced metric overrides for {season}: {len(overrides)} teams")
    return overrides


def load_real_historical_data(
    start_season: int = 2010,
    end_season: int = 2025
) -> List[TeamSeason]:
    """
    Load real historical NHL data from verified JSON files.

    Args:
        start_season: First season to load (e.g., 2010 for 2009-10)
        end_season: Last season to load (e.g., 2025 for 2024-25)

    Returns:
        List of TeamSeason objects with real NHL data
    """
    all_teams = []

    for season in range(start_season, end_season + 1):
        season_teams = _load_verified_json(season)
        if season_teams:
            all_teams.extend(season_teams)
            logger.info(f"Loaded {len(season_teams)} teams for season {season}")
        else:
            logger.warning(f"No verified data available for season {season}")

    logger.info(f"Total loaded: {len(all_teams)} team-seasons")
    return all_teams


def _load_verified_json(season: int) -> List[TeamSeason]:
    """Load and parse a single verified season JSON file into TeamSeason objects."""
    json_path = HISTORICAL_DIR / f"season_{season}.json"

    if not json_path.exists():
        logger.debug(f"Verified file not found: {json_path}")
        return []

    with open(json_path) as f:
        data = json.load(f)

    teams_data = data.get("teams", {})
    if not teams_data:
        logger.warning(f"No teams in {json_path}")
        return []

    teams = []
    for abbrev, t in teams_data.items():
        team = _json_to_team_season(abbrev, t, season)
        if team:
            teams.append(team)

    return teams


def _json_to_team_season(abbrev: str, t: dict, season: int) -> Optional[TeamSeason]:
    """Convert a single team's JSON record into a TeamSeason object."""
    try:
        team_abbr = _normalize_team(abbrev)

        gp = t.get("gp", 0)
        wins = t.get("w", 0)
        losses = t.get("l", 0)
        ot_losses = t.get("otl", 0)
        points = t.get("pts", 0)
        goals_for = t.get("gf", 0)
        goals_against = t.get("ga", 0)

        # Home/away splits
        home_wins = t.get("homeW", 0)
        home_losses = t.get("homeL", 0)
        home_ot_losses = t.get("homeOTL", 0)
        road_wins = t.get("roadW", 0)
        road_losses = t.get("roadL", 0)
        road_ot_losses = t.get("roadOTL", 0)

        # Special teams — stored as percentages (e.g., 22.4 for 22.4%)
        # Default to league average if missing so the model doesn't see 0
        pp_pct = t.get("ppPct") or 0
        pk_pct = t.get("pkPct") or 0
        if pp_pct == 0:
            logger.warning(f"{abbrev} {season}: PP% missing, imputing league avg 20.0")
            pp_pct = 20.0
        if pk_pct == 0:
            logger.warning(f"{abbrev} {season}: PK% missing, imputing league avg 80.0")
            pk_pct = 80.0

        # Advanced stats from NST (5v5) — default to 50.0 (league average)
        cf_pct = t.get("cfPct") or 50.0
        hdcf_pct = t.get("hdcfPct") or 50.0

        # NST PDO comes as decimal (0.95-1.05 range) or 100-scale (95-105).
        # TeamSeason expects PDO on 100-scale (95-105 range).
        pdo_raw = t.get("pdo") or 1.0
        if pdo_raw < 2.0:
            # Decimal format (e.g., 1.005) — convert to 100-scale
            pdo = pdo_raw * 100
        elif 80 <= pdo_raw <= 120:
            # Already on 100-scale (e.g., 100.5)
            pdo = pdo_raw
        else:
            logger.warning(f"{abbrev} {season}: PDO value {pdo_raw} outside expected range, defaulting to 100.0")
            pdo = 100.0

        # NST SH% is already a percentage (e.g., 8.41)
        shooting_pct = t.get("shPct") or 10.0

        # NST SV% comes as percentage-like (e.g., 91.45 for 91.45%) or
        # decimal (e.g., 0.9145). TeamSeason expects decimal (e.g., 0.9145).
        sv_raw = t.get("svPct") or 91.0
        if sv_raw > 1.0:
            # Percentage format (e.g., 91.45) — convert to decimal
            save_pct = sv_raw / 100.0
        elif 0.8 <= sv_raw <= 1.0:
            # Already decimal (e.g., 0.9145)
            save_pct = sv_raw
        else:
            logger.warning(f"{abbrev} {season}: SV% value {sv_raw} outside expected range, defaulting to 0.910")
            save_pct = 0.910

        # Raw Corsi/HD counts (for feature engineering)
        ca = t.get("ca") or 0
        hdcf = t.get("hdcf") or 0
        hdca = t.get("hdca") or 0

        # xG/GSAx are not present in current verified historical files.
        # Use conservative proxies to retain informative variance.
        xgf, xga, xgf_pct_proxy = _estimate_expected_goal_profile(
            goals_for=goals_for,
            goals_against=goals_against,
            cf_pct=cf_pct,
            hdcf_pct=hdcf_pct
        )
        gsax = _estimate_gsax_proxy(save_pct=save_pct, games_played=gp, ca=ca)

        # If true advanced overrides exist for this season/team, use them.
        advanced_overrides = _load_advanced_overrides_for_season(season)
        override = advanced_overrides.get(team_abbr)
        if override:
            if "xgf" in override:
                xgf = override["xgf"]
            if "xga" in override:
                xga = override["xga"]
            if "xgfPct" in override:
                xgf_pct_proxy = override["xgfPct"]
            if "gsax" in override:
                gsax = override["gsax"]

        # Playoff outcomes
        made_playoffs = t.get("madePlayoffs", False)
        won_cup = t.get("wonCup", False)
        playoff_rounds_won = t.get("playoffRoundsWon", 0)

        # Sanity: Cup winner must have 4 rounds
        if won_cup:
            playoff_rounds_won = 4

        return TeamSeason(
            team=team_abbr,
            season=season,
            games_played=gp,
            wins=wins,
            losses=losses,
            ot_losses=ot_losses,
            points=points,
            goals_for=goals_for,
            goals_against=goals_against,

            cf_pct=cf_pct,
            ff_pct=cf_pct,  # Approximation: FF% not in NST team table, using CF% (correlated but excludes blocked shots)
            sf_pct=cf_pct,  # Approximation: SF% not in NST team table, using CF%

            xgf=xgf,
            xga=xga,
            xgf_pct=xgf_pct_proxy,
            expected_goals_diff=xgf - xga,

            hdcf=hdcf,
            hdca=hdca,
            hdcf_pct=hdcf_pct,

            save_pct=save_pct,
            gsax=gsax,

            shooting_pct=shooting_pct,
            pdo=pdo,

            pp_pct=pp_pct,
            pk_pct=pk_pct,

            home_wins=home_wins,
            home_losses=home_losses,
            home_ot_losses=home_ot_losses,
            away_wins=road_wins,
            away_losses=road_losses,
            away_ot_losses=road_ot_losses,

            made_playoffs=made_playoffs,
            won_cup=won_cup,
            playoff_rounds_won=playoff_rounds_won,

            recent_form=0.0,
            star_ppg=0.0,
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse team data for {abbrev}: {e}")
        return None


def load_real_training_data() -> List[TeamSeason]:
    """
    Load real training data from verified historical JSON files.
    Falls back to synthetic data if insufficient real data is found.
    """
    real_data = load_real_historical_data(start_season=2010, end_season=2024)

    if len(real_data) >= 100:
        logger.info(f"Using {len(real_data)} real historical team-seasons for training")
        return real_data

    logger.warning("Insufficient real data, falling back to synthetic generation")
    from .data_loader import synthesize_training_data
    return synthesize_training_data()


def get_available_seasons() -> List[int]:
    """Get list of seasons with available verified data."""
    available = []
    for path in sorted(HISTORICAL_DIR.glob("season_*.json")):
        try:
            year = int(path.stem.split("_")[1])
            available.append(year)
        except (ValueError, IndexError):
            continue
    return available


def get_advanced_override_coverage(
    start_season: int = 2010,
    end_season: int = 2024,
) -> Dict[str, Any]:
    """
    Report historical advanced override coverage by season.

    Returns counts for:
    - fileExists: raw override file exists (JSON/CSV)
    - teamCountRaw: number of teams found in override file before minimum gate
    - accepted: whether override passed minimum-team threshold
    - teamCountAccepted: number of teams accepted for modeling (0 if rejected)
    """
    season_rows: List[Dict[str, Any]] = []
    accepted_seasons = 0
    total_raw_teams = 0
    total_accepted_teams = 0
    total_possible = max(0, (end_season - start_season + 1) * 32)

    for season in range(start_season, end_season + 1):
        json_path, csv_path = _advanced_override_paths_for_season(season)
        raw_exists = json_path.exists() or csv_path.exists()

        raw_overrides: Dict[str, Dict[str, float]] = {}
        if raw_exists:
            # Read raw directly without mutating the cached accepted view.
            try:
                if json_path.exists():
                    raw = json.loads(json_path.read_text())
                    if isinstance(raw, dict):
                        for team, vals in raw.items():
                            if isinstance(vals, dict):
                                raw_overrides[_normalize_team(str(team).strip().upper())] = vals
                elif csv_path.exists():
                    with open(csv_path, newline="") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            team_raw = (
                                row.get("team")
                                or row.get("TEAM")
                                or row.get("teamAbbrev")
                                or row.get("team_abbrev")
                            )
                            if team_raw:
                                raw_overrides[_normalize_team(str(team_raw).strip().upper())] = row
            except Exception:
                raw_overrides = {}

        raw_count = len(raw_overrides)
        accepted = raw_count >= MIN_OVERRIDE_TEAM_COVERAGE
        accepted_count = raw_count if accepted else 0

        total_raw_teams += raw_count
        total_accepted_teams += accepted_count
        if accepted:
            accepted_seasons += 1

        season_rows.append(
            {
                "season": season,
                "fileExists": raw_exists,
                "teamCountRaw": raw_count,
                "accepted": accepted,
                "teamCountAccepted": accepted_count,
            }
        )

    return {
        "startSeason": start_season,
        "endSeason": end_season,
        "minTeamCoverage": MIN_OVERRIDE_TEAM_COVERAGE,
        "acceptedSeasons": accepted_seasons,
        "totalSeasons": max(0, end_season - start_season + 1),
        "acceptedSeasonRatio": (
            accepted_seasons / max(1, (end_season - start_season + 1))
        ),
        "rawTeamCoverageRatio": total_raw_teams / max(1, total_possible),
        "acceptedTeamCoverageRatio": total_accepted_teams / max(1, total_possible),
        "seasons": season_rows,
    }
