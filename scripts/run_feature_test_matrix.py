#!/usr/bin/env python3
"""
Run full feature test matrix with strict walk-forward validation.

Implements:
- Add-one and leave-one-out tests
- Era stability checks
- Pairwise interaction tests
- Bootstrap confidence intervals on season-level metrics
- Strict no-leakage validation for every split
- Keep/reduce/remove/add recommendations
"""

import itertools
import json
import math
import random
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.feature_engineering import FeatureEngineer
from superhuman.playoff_experience_loader import (
    calculate_playoff_experience_feature,
    calculate_dynasty_feature,
)


OUT_JSON = PROJECT_ROOT / "reports" / "feature_test_matrix.json"
OUT_MD = PROJECT_ROOT / "reports" / "FEATURE_TEST_MATRIX.md"


RANDOM_SEED = 42
BOOTSTRAP_ITERATIONS = 1000
warnings.filterwarnings("ignore", category=RuntimeWarning)


@dataclass
class FoldResult:
    season: int
    cup_top1: float
    cup_top5: float
    cup_winner_rank: float
    playoff_f1: float


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _f1_binary(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    if precision + recall == 0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def _bootstrap_ci(values: List[float], alpha: float = 0.05) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    rng = random.Random(RANDOM_SEED)
    samples = []
    n = len(values)
    for _ in range(BOOTSTRAP_ITERATIONS):
        draw = [values[rng.randrange(n)] for _ in range(n)]
        samples.append(float(np.mean(draw)))
    lo = np.percentile(samples, 100 * (alpha / 2))
    hi = np.percentile(samples, 100 * (1 - alpha / 2))
    return float(lo), float(hi)


def _candidate_feature_value(ts) -> Dict[str, float]:
    gp = max(1, ts.games_played)
    xgf_rate = ts.xgf / gp
    xga_rate = ts.xga / gp
    return {
        # Existing model features (expanded into concrete primitives)
        "goal_differential_rate": ts.gd_per_game,
        "cf_pct": ts.cf_pct,
        "hdcf_pct": ts.hdcf_pct,
        "xgf_pct": ts.xgf_pct,
        "goaltending_quality": ts.gsax / 10.0,
        "pp_pct": ts.pp_pct,
        "pk_pct": ts.pk_pct,
        "road_performance": (ts.away_win_pct / 100.0) - (0.85 * ts.home_win_pct / 100.0),
        "sustainability": -abs(ts.pdo - 100.0) / 5.0,
        # Requested additional datapoints (available now)
        "true_xgf_rate": xgf_rate,
        "true_xga_rate": xga_rate,
        "xg_diff_rate": (ts.xgf - ts.xga) / gp,
        "offense_rate": ts.goals_for / gp,
        "defense_rate": -(ts.goals_against / gp),
        "save_pct": ts.save_pct,
        # Requested but only proxy-available
        "discipline_proxy_special_teams": ((ts.pp_pct - 20.0) * 0.4) + ((ts.pk_pct - 80.0) * 0.6),
        # Pre-season-safe historical playoff signals
        "playoff_experience": calculate_playoff_experience_feature(ts.team, ts.season),
        "dynasty_score": calculate_dynasty_feature(ts.team, ts.season),
    }


def _feature_matrix_for_teams(teams: List, feature_names: List[str]) -> np.ndarray:
    rows = []
    for ts in teams:
        vals = _candidate_feature_value(ts)
        rows.append([vals.get(name, 0.0) for name in feature_names])
    X = np.array(rows, dtype=float)
    X = np.nan_to_num(X, nan=0.0, posinf=1e3, neginf=-1e3)
    X = np.clip(X, -1e3, 1e3)
    return X


def _evaluate_feature_set(
    all_data: List,
    feature_names: List[str],
    era_labels: Dict[int, str],
) -> Dict:
    by_season = defaultdict(list)
    for t in all_data:
        by_season[t.season].append(t)
    seasons = sorted(by_season.keys())

    fold_results: List[FoldResult] = []
    era_buckets: Dict[str, List[FoldResult]] = defaultdict(list)

    for held_out in seasons:
        train = [t for t in all_data if t.season < held_out]
        test = by_season[held_out]

        if len(train) < 64 or len(test) < 16:
            continue
        if not any(t.won_cup for t in test):
            continue

        # Hard no-leakage assertion
        if max(t.season for t in train) >= held_out:
            raise RuntimeError(f"Leakage detected for held-out season {held_out}")

        X_train = _feature_matrix_for_teams(train, feature_names)
        X_test = _feature_matrix_for_teams(test, feature_names)
        y_train_cup = np.array([1 if t.won_cup else 0 for t in train], dtype=int)
        y_test_cup = np.array([1 if t.won_cup else 0 for t in test], dtype=int)
        y_train_playoff = np.array([1 if t.made_playoffs else 0 for t in train], dtype=int)
        y_test_playoff = np.array([1 if t.made_playoffs else 0 for t in test], dtype=int)

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        # Cup model
        cup_model = LogisticRegression(
            penalty="l2",
            C=0.7,
            solver="lbfgs",
            max_iter=1000,
        )
        cup_model.fit(X_train_s, y_train_cup)
        cup_prob = cup_model.predict_proba(X_test_s)[:, 1]

        # Playoff model
        playoff_model = LogisticRegression(
            penalty="l2",
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
        )
        playoff_model.fit(X_train_s, y_train_playoff)
        playoff_prob = playoff_model.predict_proba(X_test_s)[:, 1]

        cup_rank = np.argsort(-cup_prob)
        winner_idx = int(np.argmax(y_test_cup))
        top1 = 1.0 if cup_rank[0] == winner_idx else 0.0
        top5 = 1.0 if winner_idx in set(cup_rank[:5]) else 0.0
        winner_rank = float(np.where(cup_rank == winner_idx)[0][0] + 1)

        playoff_rank = np.argsort(-playoff_prob)
        pred_playoff = np.zeros(len(test), dtype=int)
        pred_playoff[playoff_rank[:16]] = 1
        pf1 = _f1_binary(y_test_playoff, pred_playoff)

        fr = FoldResult(
            season=held_out,
            cup_top1=top1,
            cup_top5=top5,
            cup_winner_rank=winner_rank,
            playoff_f1=pf1,
        )
        fold_results.append(fr)
        era_buckets[era_labels.get(held_out, "unknown")].append(fr)

    if not fold_results:
        return {
            "summary": {},
            "ci95": {},
            "era_stability": {},
            "seasons": [],
        }

    top1_vals = [r.cup_top1 for r in fold_results]
    top5_vals = [r.cup_top5 for r in fold_results]
    rank_vals = [r.cup_winner_rank for r in fold_results]
    pf1_vals = [r.playoff_f1 for r in fold_results]

    era_summary = {}
    for era, rows in era_buckets.items():
        era_summary[era] = {
            "n_seasons": len(rows),
            "cup_top1_accuracy_pct": round(100.0 * np.mean([r.cup_top1 for r in rows]), 1),
            "cup_top5_accuracy_pct": round(100.0 * np.mean([r.cup_top5 for r in rows]), 1),
            "cup_average_winner_rank": round(float(np.mean([r.cup_winner_rank for r in rows])), 2),
            "playoff_f1": round(float(np.mean([r.playoff_f1 for r in rows])), 3),
        }

    return {
        "summary": {
            "n_seasons": len(fold_results),
            "cup_top1_accuracy_pct": round(100.0 * float(np.mean(top1_vals)), 1),
            "cup_top5_accuracy_pct": round(100.0 * float(np.mean(top5_vals)), 1),
            "cup_average_winner_rank": round(float(np.mean(rank_vals)), 2),
            "playoff_f1": round(float(np.mean(pf1_vals)), 3),
        },
        "ci95": {
            "cup_top1_accuracy_pct": [round(100.0 * v, 1) for v in _bootstrap_ci(top1_vals)],
            "cup_top5_accuracy_pct": [round(100.0 * v, 1) for v in _bootstrap_ci(top5_vals)],
            "cup_average_winner_rank": [round(v, 2) for v in _bootstrap_ci(rank_vals)],
            "playoff_f1": [round(v, 3) for v in _bootstrap_ci(pf1_vals)],
        },
        "era_stability": era_summary,
        "seasons": [
            {
                "season": r.season,
                "cup_top1": r.cup_top1,
                "cup_top5": r.cup_top5,
                "cup_winner_rank": r.cup_winner_rank,
                "playoff_f1": r.playoff_f1,
            }
            for r in fold_results
        ],
    }


def _recommendation(baseline: Dict, loo: Dict, add: Dict) -> str:
    b = baseline["summary"]
    l = loo["summary"]
    a = add["summary"]

    if not l:
        return "keep"

    # Removing feature hurts -> keep/increase
    if (
        l["cup_top1_accuracy_pct"] < b["cup_top1_accuracy_pct"]
        or l["cup_top5_accuracy_pct"] < b["cup_top5_accuracy_pct"]
        or l["cup_average_winner_rank"] > b["cup_average_winner_rank"]
        or l["playoff_f1"] < b["playoff_f1"]
    ):
        return "keep_or_increase"

    # Feature alone still carries good signal
    if a and (
        a["cup_top1_accuracy_pct"] >= 15.0
        or a["cup_top5_accuracy_pct"] >= 45.0
        or a["playoff_f1"] >= 0.85
    ):
        return "reduce_but_keep"

    return "reduce_or_remove"


def main() -> int:
    all_data = load_training_data()

    era_labels = {}
    for y in range(2013, 2018):
        era_labels[y] = "era_2013_2017"
    for y in range(2018, 2021):
        era_labels[y] = "era_2018_2020"
    for y in range(2021, 2025):
        era_labels[y] = "era_2021_2024"

    base_features = [
        "goal_differential_rate",
        "cf_pct",
        "hdcf_pct",
        "xgf_pct",
        "goaltending_quality",
        "pp_pct",
        "pk_pct",
        "road_performance",
        "sustainability",
        "true_xgf_rate",
        "true_xga_rate",
        "xg_diff_rate",
        "offense_rate",
        "defense_rate",
        "save_pct",
        "discipline_proxy_special_teams",
        "playoff_experience",
        "dynasty_score",
    ]

    baseline = _evaluate_feature_set(all_data, base_features, era_labels)

    add_one = {}
    leave_one_out = {}
    for feat in base_features:
        add_one[feat] = _evaluate_feature_set(all_data, [feat], era_labels)
        remain = [f for f in base_features if f != feat]
        leave_one_out[feat] = _evaluate_feature_set(all_data, remain, era_labels)

    # Pairwise interactions among top baseline-correlated features.
    # Limit to practical size for repeatable runtime.
    interaction_features = [
        "goal_differential_rate",
        "cf_pct",
        "hdcf_pct",
        "xgf_pct",
        "goaltending_quality",
        "true_xgf_rate",
        "true_xga_rate",
        "xg_diff_rate",
        "save_pct",
    ]
    interaction_results = []
    for a, b in itertools.combinations(interaction_features, 2):
        ev = _evaluate_feature_set(all_data, [a, b], era_labels)
        interaction_results.append(
            {
                "pair": [a, b],
                "summary": ev["summary"],
            }
        )
    interaction_results.sort(
        key=lambda r: (
            -r["summary"].get("cup_top1_accuracy_pct", 0.0),
            -r["summary"].get("cup_top5_accuracy_pct", 0.0),
            r["summary"].get("cup_average_winner_rank", math.inf),
            -r["summary"].get("playoff_f1", 0.0),
        )
    )

    decision_table = []
    for feat in base_features:
        decision_table.append(
            {
                "feature": feat,
                "baseline_summary": baseline["summary"],
                "add_one_summary": add_one[feat]["summary"],
                "leave_one_out_summary": leave_one_out[feat]["summary"],
                "recommendation": _recommendation(baseline, leave_one_out[feat], add_one[feat]),
            }
        )

    # Requested datapoints that remain unavailable in current historical schema.
    unavailable_backlog = [
        "goalie_usage_quality_starter_load",
        "goalie_backup_dropoff",
        "injury_adjusted_strength",
        "score_state_adjusted_5v5_close_game",
        "schedule_travel_rest_load",
        "discipline_taken_drawn_split",
        "trade_deadline_roster_delta",
        "playoff_style_netfront_rush_forecheck",
        "coach_system_continuity",
    ]

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "strict_walk_forward_test_matrix",
        "leakageCheck": "train seasons strictly less than held-out season",
        "baseline": baseline,
        "addOne": add_one,
        "leaveOneOut": leave_one_out,
        "interactionsTop": interaction_results[:25],
        "decisionTable": decision_table,
        "unavailableBacklogDatapoints": unavailable_backlog,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Feature Test Matrix",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Baseline",
        "",
        f"- Cup Top-1: {baseline['summary'].get('cup_top1_accuracy_pct', 0):.1f}%",
        f"- Cup Top-5: {baseline['summary'].get('cup_top5_accuracy_pct', 0):.1f}%",
        f"- Avg Winner Rank: {baseline['summary'].get('cup_average_winner_rank', 0):.2f}",
        f"- Playoff F1: {baseline['summary'].get('playoff_f1', 0):.3f}",
        "",
        "## Decision Table",
        "",
        "| Feature | Add-One Top1 | LOO Top1 | Recommendation |",
        "|---|---:|---:|---|",
    ]
    for row in decision_table:
        add_top1 = row["add_one_summary"].get("cup_top1_accuracy_pct", 0.0)
        loo_top1 = row["leave_one_out_summary"].get("cup_top1_accuracy_pct", 0.0)
        lines.append(f"| {row['feature']} | {add_top1:.1f} | {loo_top1:.1f} | {row['recommendation']} |")

    lines += [
        "",
        "## Top Interactions",
        "",
        "| Pair | Cup Top1 | Cup Top5 | Winner Rank | Playoff F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in interaction_results[:15]:
        s = row["summary"]
        lines.append(
            f"| {row['pair'][0]} + {row['pair'][1]} | {s.get('cup_top1_accuracy_pct', 0):.1f} | "
            f"{s.get('cup_top5_accuracy_pct', 0):.1f} | {s.get('cup_average_winner_rank', 0):.2f} | "
            f"{s.get('playoff_f1', 0):.3f} |"
        )

    lines += [
        "",
        "## Unavailable Backlog Datapoints",
        "",
    ]
    for name in unavailable_backlog:
        lines.append(f"- {name}")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
