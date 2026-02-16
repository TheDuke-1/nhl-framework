#!/usr/bin/env python3
"""
Strict walk-forward feature analysis for Cup and playoff prediction signal.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, f1_score
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.feature_engineering import FeatureEngineer, create_feature_matrix
from superhuman.data_models import FeatureVector


OUT_JSON = PROJECT_ROOT / "reports" / "feature_backtest_analysis.json"
OUT_MD = PROJECT_ROOT / "reports" / "FEATURE_BACKTEST_ANALYSIS.md"


def _safe_logloss(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    if len(y_true) == 0:
        return 0.0
    y_prob = np.clip(y_prob, 1e-12, 1 - 1e-12)
    return float(log_loss(y_true, y_prob))


def _fit_single_feature_probs(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
) -> np.ndarray:
    if len(np.unique(y_train)) < 2:
        return np.full(len(x_test), float(np.mean(y_train) if len(y_train) else 0.0))

    scaler = StandardScaler()
    x_train_s = scaler.fit_transform(x_train.reshape(-1, 1))
    x_test_s = scaler.transform(x_test.reshape(-1, 1))

    model = LogisticRegression(
        penalty="l2",
        C=1.0,
        solver="lbfgs",
        max_iter=500,
    )
    model.fit(x_train_s, y_train)
    return model.predict_proba(x_test_s)[:, 1]


def _analyze_univariate(backtest_rows: List[Dict]) -> List[Dict]:
    out = []
    for row in backtest_rows:
        n = max(1, row["n_seasons"])
        out.append(
            {
                "feature": row["feature"],
                "cup_top1_accuracy_pct": round(100.0 * row["cup_top1_correct"] / n, 1),
                "cup_top5_accuracy_pct": round(100.0 * row["cup_top5_correct"] / n, 1),
                "cup_average_winner_rank": round(row["cup_winner_rank_sum"] / n, 2),
                "cup_brier": round(row["cup_brier_sum"] / n, 4),
                "cup_logloss": round(row["cup_logloss_sum"] / n, 4),
                "playoff_f1": round(row["playoff_f1_sum"] / n, 3),
                "playoff_brier": round(row["playoff_brier_sum"] / n, 4),
                "playoff_logloss": round(row["playoff_logloss_sum"] / n, 4),
                "seasons_evaluated": n,
            }
        )
    out.sort(key=lambda r: (-r["cup_top1_accuracy_pct"], r["cup_average_winner_rank"], -r["cup_top5_accuracy_pct"]))
    return out


def _analyze_multivariate(all_data) -> Dict:
    by_season = defaultdict(list)
    for t in all_data:
        by_season[t.season].append(t)
    seasons = sorted(by_season.keys())

    feature_names = FeatureVector.feature_names()
    coef_sum = np.zeros(len(feature_names), dtype=float)
    fold_count = 0

    for held_out in seasons:
        train = [t for t in all_data if t.season < held_out]
        test = by_season[held_out]
        if len(train) < 64 or len(test) < 16:
            continue
        if not any(t.won_cup for t in test):
            continue

        fe = FeatureEngineer().fit(train)
        train_f = fe.transform(train)
        test_f = fe.transform(test)
        X_train, _, _ = create_feature_matrix(train_f)
        X_test, _, _ = create_feature_matrix(test_f)
        y_train = np.array([1 if f.won_cup else 0 for f in train_f], dtype=int)
        if len(np.unique(y_train)) < 2:
            continue

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        model = LogisticRegression(
            penalty="l1",
            C=0.7,
            solver="saga",
            max_iter=2000,
        )
        model.fit(X_train_s, y_train)
        coef_sum += np.abs(model.coef_[0])
        fold_count += 1

    if fold_count == 0:
        return {"weights": []}

    avg_abs = coef_sum / fold_count
    pct = (avg_abs / max(1e-12, float(np.sum(avg_abs)))) * 100.0
    rows = [
        {"feature": name, "relative_weight_pct": round(float(w), 2)}
        for name, w in zip(feature_names, pct)
    ]
    rows.sort(key=lambda r: -r["relative_weight_pct"])
    return {"weights": rows, "folds": fold_count}


def main() -> int:
    all_data = load_training_data()
    by_season = defaultdict(list)
    for t in all_data:
        by_season[t.season].append(t)
    seasons = sorted(by_season.keys())
    feature_names = FeatureVector.feature_names()

    rows = []
    for name in feature_names:
        rows.append(
            {
                "feature": name,
                "n_seasons": 0,
                "cup_top1_correct": 0,
                "cup_top5_correct": 0,
                "cup_winner_rank_sum": 0.0,
                "cup_brier_sum": 0.0,
                "cup_logloss_sum": 0.0,
                "playoff_f1_sum": 0.0,
                "playoff_brier_sum": 0.0,
                "playoff_logloss_sum": 0.0,
            }
        )

    for held_out in seasons:
        train = [t for t in all_data if t.season < held_out]
        test = by_season[held_out]
        if len(train) < 64 or len(test) < 16:
            continue
        if not any(t.won_cup for t in test):
            continue

        fe = FeatureEngineer().fit(train)
        train_f = fe.transform(train)
        test_f = fe.transform(test)
        X_train, _, names = create_feature_matrix(train_f)
        X_test, _, _ = create_feature_matrix(test_f)

        y_train_cup = np.array([1 if f.won_cup else 0 for f in train_f], dtype=int)
        y_test_cup = np.array([1 if f.won_cup else 0 for f in test_f], dtype=int)
        y_train_playoff = np.array([1 if f.made_playoffs else 0 for f in train_f], dtype=int)
        y_test_playoff = np.array([1 if f.made_playoffs else 0 for f in test_f], dtype=int)

        for idx, name in enumerate(names):
            row = rows[idx]

            cup_prob = _fit_single_feature_probs(X_train[:, idx], y_train_cup, X_test[:, idx])
            playoff_prob = _fit_single_feature_probs(X_train[:, idx], y_train_playoff, X_test[:, idx])

            order = np.argsort(-cup_prob)
            top_pick = order[0]
            top5 = set(order[:5].tolist())
            winner_idx = int(np.argmax(y_test_cup))
            winner_rank = int(np.where(order == winner_idx)[0][0]) + 1

            playoff_order = np.argsort(-playoff_prob)
            pred_playoff = np.zeros(len(y_test_playoff), dtype=int)
            pred_playoff[playoff_order[:16]] = 1

            row["n_seasons"] += 1
            row["cup_top1_correct"] += int(top_pick == winner_idx)
            row["cup_top5_correct"] += int(winner_idx in top5)
            row["cup_winner_rank_sum"] += winner_rank
            row["cup_brier_sum"] += float(brier_score_loss(y_test_cup, cup_prob))
            row["cup_logloss_sum"] += _safe_logloss(y_test_cup, cup_prob)
            row["playoff_f1_sum"] += float(f1_score(y_test_playoff, pred_playoff, zero_division=0))
            row["playoff_brier_sum"] += float(brier_score_loss(y_test_playoff, playoff_prob))
            row["playoff_logloss_sum"] += _safe_logloss(y_test_playoff, playoff_prob)

    univariate = _analyze_univariate(rows)
    multivariate = _analyze_multivariate(all_data)

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "evaluationMode": "strict_walk_forward_feature_analysis",
        "univariate": univariate,
        "multivariate_l1_weights": multivariate,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Feature Backtest Analysis",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Univariate Feature Signal",
        "",
        "| Feature | Cup Top1 % | Cup Top5 % | Winner Rank | Cup Brier | Cup LogLoss | Playoff F1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in univariate:
        lines.append(
            f"| {r['feature']} | {r['cup_top1_accuracy_pct']:.1f} | {r['cup_top5_accuracy_pct']:.1f} | "
            f"{r['cup_average_winner_rank']:.2f} | {r['cup_brier']:.4f} | {r['cup_logloss']:.4f} | "
            f"{r['playoff_f1']:.3f} |"
        )

    lines += [
        "",
        "## Multivariate L1 Relative Weights",
        "",
        "| Feature | Relative Weight % |",
        "|---|---:|",
    ]
    for r in multivariate.get("weights", []):
        lines.append(f"| {r['feature']} | {r['relative_weight_pct']:.2f} |")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
