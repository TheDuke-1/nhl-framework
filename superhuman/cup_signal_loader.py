"""
Cup Signal Loader - supplemental Cup prediction signals
=======================================================
Builds additional Cup-oriented signals from historical series results,
market context, and goalie/injury pressure.
"""

from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

from .betting_odds_loader import american_to_probability
from .config import CURRENT_SEASON, DATA_DIR, HISTORICAL_DIR, normalize_team_abbrev


_MIN_SEASON = 2010
_MAX_ABS_SIGNAL = 3.0


def _clip_signal(value: float, low: float = -_MAX_ABS_SIGNAL, high: float = _MAX_ABS_SIGNAL) -> float:
    return float(np.clip(value, low, high))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_team(team: str) -> str:
    return normalize_team_abbrev(str(team or "").strip().upper())


@lru_cache(maxsize=None)
def _load_verified_season_rows(season: int) -> Dict[str, Dict[str, Any]]:
    path = HISTORICAL_DIR / f"season_{season}.json"
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text())
    except Exception:
        return {}

    teams = payload.get("teams", {})
    if not isinstance(teams, dict):
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    for raw_team, row in teams.items():
        if not isinstance(row, dict):
            continue
        code = _normalize_team(row.get("team", raw_team))
        if not code:
            continue
        out[code] = row
    return out


def _estimate_gsax_from_row(row: Dict[str, Any]) -> float:
    sv_raw = _safe_float(row.get("svPct"), 91.0)
    sv_pct = sv_raw / 100.0 if sv_raw > 1.0 else sv_raw
    gp = _safe_int(row.get("gp"), 82)
    ca = _safe_float(row.get("ca"), 0.0)

    shots_against_est = (ca * 0.55) if ca > 0 else (gp * 30.0)
    shots_against_est = max(1000.0, shots_against_est)

    gsax = (sv_pct - 0.910) * shots_against_est
    return float(np.clip(gsax, -40.0, 40.0))


def _weighted_mean(values: Iterable[float], weights: Iterable[float]) -> Optional[float]:
    vals = list(values)
    wts = list(weights)
    if not vals or not wts:
        return None
    total = sum(wts)
    if total <= 0:
        return None
    return float(sum(v * w for v, w in zip(vals, wts)) / total)


def calculate_series_history_signal(team: str, season: int, lookback_years: int = 5) -> float:
    """
    Series-level prior-performance signal based on past playoff rounds won.
    Uses only seasons prior to the prediction season (no leakage).
    """
    code = _normalize_team(team)
    if not code or season <= _MIN_SEASON:
        return 0.0

    scores: List[float] = []
    weights: List[float] = []
    start = max(_MIN_SEASON, season - lookback_years)

    for prev in range(start, season):
        row = _load_verified_season_rows(prev).get(code)
        if not row:
            continue

        rounds = _safe_int(row.get("playoffRoundsWon"), 0)
        made = bool(row.get("madePlayoffs", False))
        won_cup = bool(row.get("wonCup", False))

        # Base scale from rounds won, centered slightly below 0 so
        # non-playoff teams carry a mild penalty.
        score = (rounds / 4.0) - 0.18
        if made:
            score += 0.08
        if won_cup:
            score += 0.30

        recency_weight = 1.0 / float(season - prev)
        scores.append(score)
        weights.append(recency_weight)

    mean_score = _weighted_mean(scores, weights)
    if mean_score is None:
        return 0.0

    return _clip_signal(mean_score * 2.0, -2.0, 2.5)


def _parse_prob_from_row(row: Dict[str, Any], prob_keys: List[str], odds_keys: List[str]) -> Optional[float]:
    for key in prob_keys:
        if key in row and str(row[key]).strip():
            val = _safe_float(row[key], default=-1.0)
            if val >= 0:
                return float(np.clip(val, 0.0, 1.0))

    for key in odds_keys:
        if key in row and str(row[key]).strip():
            raw = str(row[key]).strip().replace("+", "")
            odds = _safe_int(raw, default=0)
            if odds != 0:
                return float(np.clip(american_to_probability(odds), 0.0, 1.0))
    return None


@lru_cache(maxsize=None)
def _market_signal_map_for_season(season: int) -> Dict[str, float]:
    path = HISTORICAL_DIR / f"vegas_odds_{season}.csv"
    if not path.exists():
        return {}

    rows: Dict[str, Dict[str, float]] = {}
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = _normalize_team(row.get("team", ""))
                if not code:
                    continue

                cup_prob = _parse_prob_from_row(
                    row,
                    prob_keys=["cup_implied_prob", "cup_close_implied_prob", "cup_prob", "cup_close_prob"],
                    odds_keys=["cup_odds_american", "cup_close_odds_american", "cup_odds"],
                )
                playoff_prob = _parse_prob_from_row(
                    row,
                    prob_keys=["playoff_implied_prob", "playoff_close_implied_prob", "playoff_prob", "playoff_close_prob"],
                    odds_keys=["playoff_odds_american", "playoff_close_odds_american", "playoff_odds"],
                )
                open_cup_prob = _parse_prob_from_row(
                    row,
                    prob_keys=["cup_open_implied_prob", "cup_open_prob"],
                    odds_keys=["cup_open_odds_american", "cup_open_odds"],
                )
                close_cup_prob = _parse_prob_from_row(
                    row,
                    prob_keys=["cup_close_implied_prob", "cup_close_prob", "cup_implied_prob"],
                    odds_keys=["cup_close_odds_american", "cup_odds_american"],
                )

                if cup_prob is None or playoff_prob is None:
                    continue
                rows[code] = {
                    "cup_prob": cup_prob,
                    "playoff_prob": playoff_prob,
                    "open_cup_prob": open_cup_prob if open_cup_prob is not None else np.nan,
                    "close_cup_prob": close_cup_prob if close_cup_prob is not None else np.nan,
                }
    except Exception:
        return {}

    if not rows:
        return {}

    cup_probs = np.asarray([r["cup_prob"] for r in rows.values()], dtype=float)
    cond_probs = np.asarray(
        [r["cup_prob"] / max(r["playoff_prob"], 0.03) for r in rows.values()],
        dtype=float,
    )

    mean_cup = float(np.mean(cup_probs))
    mean_cond = float(np.mean(cond_probs))

    out: Dict[str, float] = {}
    for team, vals in rows.items():
        cup_prob = vals["cup_prob"]
        playoff_prob = vals["playoff_prob"]
        cond = cup_prob / max(playoff_prob, 0.03)

        # Prefer real open->close movement when available.
        open_prob = vals["open_cup_prob"]
        close_prob = vals["close_cup_prob"]
        if np.isfinite(open_prob) and np.isfinite(close_prob):
            movement = float(close_prob - open_prob)
        else:
            # Fallback movement proxy from conditional Cup confidence.
            movement = float(cond - mean_cond)

        conviction = float(cup_prob - mean_cup)
        signal = (movement * 10.0) + (conviction * 6.0)
        out[team] = _clip_signal(signal, -2.5, 2.5)
    return out


def _market_signal_from_current_snapshots(team: str) -> float:
    odds_dir = DATA_DIR / "historical" / "odds"
    if not odds_dir.exists():
        return 0.0

    snapshots = sorted(odds_dir.glob("odds_*.json"))
    if len(snapshots) < 2:
        return 0.0

    try:
        first = json.loads(snapshots[0].read_text()).get("teams", {})
        latest = json.loads(snapshots[-1].read_text()).get("teams", {})
    except Exception:
        return 0.0

    team_code = _normalize_team(team)
    start_prob = _safe_float(first.get(team_code, {}).get("cupPct"), 0.0) / 100.0
    end_prob = _safe_float(latest.get(team_code, {}).get("cupPct"), 0.0) / 100.0
    movement = (end_prob - start_prob) * 12.0
    return _clip_signal(movement, -2.5, 2.5)


def calculate_market_close_movement_signal(team: str, season: int) -> float:
    """
    Market movement / conviction signal.
    Uses real open->close deltas when present, otherwise a robust proxy.
    """
    code = _normalize_team(team)
    if not code:
        return 0.0

    if season >= CURRENT_SEASON:
        # For the current season, use available intra-season odds snapshots.
        snap_signal = _market_signal_from_current_snapshots(code)
        if abs(snap_signal) > 1e-9:
            return snap_signal

    season_map = _market_signal_map_for_season(season)
    return float(season_map.get(code, 0.0))


@lru_cache(maxsize=1)
def _load_current_injuries() -> Dict[str, Dict[str, Any]]:
    path = DATA_DIR / "injuries.json"
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text())
    except Exception:
        return {}

    teams = payload.get("teams", {})
    if not isinstance(teams, dict):
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    for team, row in teams.items():
        if isinstance(row, dict):
            out[_normalize_team(team)] = row
    return out


def _is_goalie_injury(row: Dict[str, Any]) -> bool:
    position = str(row.get("position", "")).strip().upper()
    note = str(row.get("note", "")).upper()
    return (
        position.startswith("G")
        or "PLACED G " in note
        or " GOALIE " in note
        or "(G)" in note
    )


def calculate_goalie_injury_playoff_impact(team: str, season: int, current_gsax: float = 0.0) -> float:
    """
    Goalie/injury pressure signal.
    Positive values indicate healthier/stabler goalie context.
    """
    code = _normalize_team(team)
    if not code:
        return 0.0

    if season >= CURRENT_SEASON:
        injuries = _load_current_injuries().get(code, {})
        total_war_lost = _safe_float(injuries.get("totalWarLost"), 0.0)
        injured_count = _safe_int(injuries.get("injuredCount"), 0)
        goalie_injuries = 0
        for row in injuries.get("injuries", []):
            if isinstance(row, dict) and _is_goalie_injury(row):
                goalie_injuries += 1

        penalty = (total_war_lost / 4.5) + (injured_count * 0.06) + (goalie_injuries * 0.45)
        goalie_support = current_gsax / 12.0
        return _clip_signal(goalie_support - penalty, -3.0, 2.5)

    # Historical fallback: infer stability from recent goalie performance trend.
    gsax_history: List[float] = []
    for prev in range(max(_MIN_SEASON, season - 3), season):
        row = _load_verified_season_rows(prev).get(code)
        if not row:
            continue
        gsax_history.append(_estimate_gsax_from_row(row))

    if gsax_history:
        mean_gsax = float(np.mean(gsax_history))
        std_gsax = float(np.std(gsax_history))
        return _clip_signal((mean_gsax / 12.0) - (std_gsax / 20.0), -2.5, 2.5)

    return _clip_signal(current_gsax / 12.0, -2.0, 2.0)

