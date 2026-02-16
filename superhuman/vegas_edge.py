"""
Strict walk-forward Vegas edge diagnostics.

Builds per-team/per-season model vs Vegas comparisons and computes:
- Brier and log-loss deltas (playoff + Cup)
- Relative Cup Brier edge
- Season-level Cup edge persistence
- Bootstrap confidence intervals over season-level Cup edge
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from sklearn.metrics import brier_score_loss, log_loss

from .betting_odds_loader import load_vegas_odds
from .config import RANDOM_SEED
from .data_models import TeamSeason
from .models import EnsemblePredictor


EPS = 1e-9


@dataclass
class VegasComparisonRow:
    team: str
    season: int
    model_playoff_prob: float
    model_cup_prob: float
    vegas_playoff_prob: float
    vegas_cup_prob: float
    actual_made_playoffs: int
    actual_won_cup: int


def _safe_log_loss(y_true: List[int], probs: List[float]) -> float:
    if not y_true:
        return float("nan")
    clipped = np.clip(np.asarray(probs, dtype=float), EPS, 1.0 - EPS)
    return float(log_loss(y_true, clipped, labels=[0, 1]))


def _relative_edge(model_brier: float, vegas_brier: float) -> Optional[float]:
    if not np.isfinite(model_brier) or not np.isfinite(vegas_brier) or vegas_brier <= 0:
        return None
    return float((vegas_brier - model_brier) / vegas_brier)


def _bootstrap_ci(
    values: List[float],
    confidence_level: float,
    n_bootstrap: int,
    random_seed: int,
) -> tuple[Optional[float], Optional[float]]:
    finite = [v for v in values if np.isfinite(v)]
    if not finite:
        return None, None
    if len(finite) == 1:
        return finite[0], finite[0]

    rng = np.random.default_rng(random_seed)
    arr = np.asarray(finite, dtype=float)
    samples = rng.choice(arr, size=(n_bootstrap, arr.shape[0]), replace=True)
    means = samples.mean(axis=1)
    alpha = 1.0 - confidence_level
    lo = float(np.percentile(means, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(means, 100.0 * (1.0 - alpha / 2.0)))
    return lo, hi


def build_model_vs_vegas_rows(
    historical_data: List[TeamSeason],
    model_overrides: Optional[Dict] = None,
    start_season: int = 2010,
    end_season: int = 2025,
    random_seed: int = RANDOM_SEED,
) -> List[VegasComparisonRow]:
    """
    Build strict walk-forward comparison rows for seasons with Vegas files.
    """
    model_overrides = model_overrides or {}
    by_season: Dict[int, List[TeamSeason]] = defaultdict(list)
    for team in historical_data:
        by_season[team.season].append(team)

    seasons = sorted(s for s in by_season if start_season <= s <= end_season)
    rows: List[VegasComparisonRow] = []

    for held_out in seasons:
        # Keep strict walk-forward vegas diagnostics deterministic across runs.
        np.random.seed(int(random_seed) + int(held_out))
        vegas = load_vegas_odds(held_out)
        if not vegas:
            continue

        train_data = [t for t in historical_data if t.season < held_out]
        test_data = by_season[held_out]
        train_seasons = {t.season for t in train_data}
        if len(train_data) < 64 or len(test_data) < 16:
            continue

        strict_oof_required = bool(
            model_overrides.get("strict_verification")
            and model_overrides.get("require_oof_cup_calibration_in_strict_mode")
        )
        # Strict OOF Cup calibration needs enough historical seasons to create
        # at least two positive held-out folds for calibrator fitting.
        if strict_oof_required and len(train_seasons) < 5:
            continue

        model_kwargs = {"use_neural_network": False}
        model_kwargs.update(model_overrides)
        model = EnsemblePredictor(**model_kwargs)
        try:
            model.fit(train_data)
        except RuntimeError as exc:
            # Early walk-forward windows can be too short for strict OOF Cup
            # calibration. Skip those windows instead of failing all seasons.
            if strict_oof_required and "out-of-fold Cup calibration data" in str(exc):
                continue
            raise
        predictions = model.predict(test_data)
        pred_by_team = {p.team: p for p in predictions}

        for t in test_data:
            pred = pred_by_team.get(t.team)
            odds = vegas.get(t.team)
            if pred is None or odds is None:
                continue
            rows.append(
                VegasComparisonRow(
                    team=t.team,
                    season=held_out,
                    model_playoff_prob=float(pred.playoff_probability),
                    model_cup_prob=float(pred.cup_win_probability),
                    vegas_playoff_prob=float(odds.playoff_implied_prob),
                    vegas_cup_prob=float(odds.cup_implied_prob),
                    actual_made_playoffs=1 if t.made_playoffs else 0,
                    actual_won_cup=1 if t.won_cup else 0,
                )
            )

    return rows


def evaluate_model_vs_vegas_edge(
    historical_data: List[TeamSeason],
    model_overrides: Optional[Dict] = None,
    start_season: int = 2010,
    end_season: int = 2025,
    confidence_level: float = 0.95,
    n_bootstrap: int = 5000,
    random_seed: int = RANDOM_SEED,
) -> Dict:
    """
    Evaluate model-vs-Vegas quality under strict walk-forward splits.
    """
    rows = build_model_vs_vegas_rows(
        historical_data=historical_data,
        model_overrides=model_overrides,
        start_season=start_season,
        end_season=end_season,
        random_seed=random_seed,
    )
    if not rows:
        return {
            "available": False,
            "rows_compared": 0,
            "seasons_compared": [],
            "cup": {},
            "playoff": {},
        }

    y_playoff = [r.actual_made_playoffs for r in rows]
    y_cup = [r.actual_won_cup for r in rows]
    model_playoff = [r.model_playoff_prob for r in rows]
    vegas_playoff = [r.vegas_playoff_prob for r in rows]
    model_cup = [r.model_cup_prob for r in rows]
    vegas_cup = [r.vegas_cup_prob for r in rows]

    model_brier_playoff = float(brier_score_loss(y_playoff, model_playoff))
    vegas_brier_playoff = float(brier_score_loss(y_playoff, vegas_playoff))
    model_brier_cup = float(brier_score_loss(y_cup, model_cup))
    vegas_brier_cup = float(brier_score_loss(y_cup, vegas_cup))

    model_logloss_playoff = _safe_log_loss(y_playoff, model_playoff)
    vegas_logloss_playoff = _safe_log_loss(y_playoff, vegas_playoff)
    model_logloss_cup = _safe_log_loss(y_cup, model_cup)
    vegas_logloss_cup = _safe_log_loss(y_cup, vegas_cup)

    season_groups: Dict[int, List[VegasComparisonRow]] = defaultdict(list)
    for row in rows:
        season_groups[row.season].append(row)

    season_edges = []
    for season in sorted(season_groups):
        season_rows = season_groups[season]
        sy_cup = [r.actual_won_cup for r in season_rows]
        sm_cup = [r.model_cup_prob for r in season_rows]
        sv_cup = [r.vegas_cup_prob for r in season_rows]
        sm_brier = float(brier_score_loss(sy_cup, sm_cup))
        sv_brier = float(brier_score_loss(sy_cup, sv_cup))
        rel = _relative_edge(sm_brier, sv_brier)
        season_edges.append(
            {
                "season": season,
                "model_brier_cup": sm_brier,
                "vegas_brier_cup": sv_brier,
                "relative_brier_edge": rel,
            }
        )

    season_relative_edges = [
        float(s["relative_brier_edge"])
        for s in season_edges
        if s["relative_brier_edge"] is not None and np.isfinite(s["relative_brier_edge"])
    ]
    ci_low, ci_high = _bootstrap_ci(
        values=season_relative_edges,
        confidence_level=confidence_level,
        n_bootstrap=n_bootstrap,
        random_seed=random_seed,
    )
    positive_seasons = sum(1 for v in season_relative_edges if v > 0)
    total_seasons = len(season_relative_edges)

    cup_relative_edge = _relative_edge(model_brier_cup, vegas_brier_cup)
    playoff_relative_edge = _relative_edge(model_brier_playoff, vegas_brier_playoff)

    return {
        "available": True,
        "rows_compared": len(rows),
        "seasons_compared": sorted(season_groups.keys()),
        "playoff": {
            "model_brier": model_brier_playoff,
            "vegas_brier": vegas_brier_playoff,
            "model_log_loss": model_logloss_playoff,
            "vegas_log_loss": vegas_logloss_playoff,
            "model_minus_vegas_brier": model_brier_playoff - vegas_brier_playoff,
            "model_minus_vegas_log_loss": model_logloss_playoff - vegas_logloss_playoff,
            "relative_brier_edge": playoff_relative_edge,
        },
        "cup": {
            "model_brier": model_brier_cup,
            "vegas_brier": vegas_brier_cup,
            "model_log_loss": model_logloss_cup,
            "vegas_log_loss": vegas_logloss_cup,
            "model_minus_vegas_brier": model_brier_cup - vegas_brier_cup,
            "model_minus_vegas_log_loss": model_logloss_cup - vegas_logloss_cup,
            "relative_brier_edge": cup_relative_edge,
            "relative_brier_edge_ci_low": ci_low,
            "relative_brier_edge_ci_high": ci_high,
            "confidence_level": confidence_level,
            "positive_seasons": positive_seasons,
            "total_seasons": total_seasons,
            "positive_season_ratio": (positive_seasons / total_seasons) if total_seasons > 0 else 0.0,
            "season_edges": season_edges,
        },
    }
