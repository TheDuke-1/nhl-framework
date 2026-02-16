#!/usr/bin/env python3
"""
Phase 15: targeted probability-quality uplift lane.

Searches a bounded candidate set focused on improving probability-quality behavior
(Brier/log-loss/calibration) while preserving core hard gates, non-regression,
and Cup-vs-Vegas release-floor safety.
"""

from __future__ import annotations

import copy
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.config import RANDOM_SEED
from superhuman.data_loader import load_training_data
from superhuman.evaluation_contract import CUP_VEGAS_EDGE_GOAL, DELTA_GUARDRAILS, HARD_GATES
from superhuman.model_profile import DEFAULT_PROFILE_PATH, load_active_model_profile
from superhuman.models import EnsemblePredictor
from superhuman.validation import ValidationFramework, generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge


OUT_JSON = PROJECT_ROOT / "reports" / "phase15_probability_quality_uplift.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE15_PROBABILITY_QUALITY_UPLIFT.md"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _probability_quality_score(quality: Dict[str, float]) -> float:
    brier_p = float(quality.get("brier_playoff", 1.0))
    brier_c = float(quality.get("brier_cup", 1.0))
    log_loss = float(quality.get("log_loss_playoff", 10.0))
    ece = float(quality.get("calibration_error", 1.0))
    s_bp = _clamp01((0.12 - brier_p) / 0.06)
    s_bc = _clamp01((0.06 - brier_c) / 0.04)
    s_ll = _clamp01((0.35 - log_loss) / 0.20)
    s_ece = _clamp01((0.05 - ece) / 0.04)
    return round(100.0 * (0.35 * s_bp + 0.25 * s_bc + 0.20 * s_ll + 0.20 * s_ece), 2)


def _extract_core(summary: Dict[str, Any]) -> Dict[str, float]:
    return {
        "top1_accuracy_pct": float(summary.get("topPickAccuracy", 0.0)),
        "top5_accuracy_pct": float(summary.get("top5Accuracy", 0.0)),
        "average_winner_rank": float(summary.get("averageWinnerRank", 999.0)),
        "playoff_f1": float(summary.get("averagePlayoffF1", 0.0)),
    }


def _hard_gates_pass(core: Dict[str, float]) -> bool:
    return (
        core.get("top1_accuracy_pct", 0.0) >= HARD_GATES["top1_accuracy_pct_min"]
        and core.get("top5_accuracy_pct", 0.0) >= HARD_GATES["top5_accuracy_pct_min"]
        and core.get("playoff_f1", 0.0) >= HARD_GATES["playoff_f1_min"]
        and core.get("average_winner_rank", 999.0) <= HARD_GATES["average_winner_rank_max"]
    )


def _core_non_regression(base: Dict[str, float], cand: Dict[str, float]) -> bool:
    return (
        (base["top1_accuracy_pct"] - cand["top1_accuracy_pct"]) <= DELTA_GUARDRAILS["top1_accuracy_pct_max_drop"]
        and (base["top5_accuracy_pct"] - cand["top5_accuracy_pct"]) <= DELTA_GUARDRAILS["top5_accuracy_pct_max_drop"]
        and (base["playoff_f1"] - cand["playoff_f1"]) <= DELTA_GUARDRAILS["playoff_f1_max_drop"]
        and (cand["average_winner_rank"] - base["average_winner_rank"]) <= DELTA_GUARDRAILS["average_winner_rank_max_increase"]
    )


def _candidate_grid(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    full = [
        {"name": "baseline", "overrides": copy.deepcopy(base)},
        {"name": "market-blend-005", "overrides": {**copy.deepcopy(base), "cup_market_prior_blend": 0.05}},
        {"name": "market-blend-010", "overrides": {**copy.deepcopy(base), "cup_market_prior_blend": 0.10}},
        {"name": "market-blend-015", "overrides": {**copy.deepcopy(base), "cup_market_prior_blend": 0.15}},
        {"name": "decay-020", "overrides": {**copy.deepcopy(base), "recency_decay_rate": 0.20}},
        {"name": "decay-018", "overrides": {**copy.deepcopy(base), "recency_decay_rate": 0.18}},
        {"name": "boost-13", "overrides": {**copy.deepcopy(base), "cup_winner_boost": 1.3}},
    ]
    if os.getenv("PHASE15_FAST_MODE", "0") == "1":
        return [row for row in full if row["name"] in {"baseline", "market-blend-005", "market-blend-010"}]
    return full


def _vegas_release_floor_pass(vegas_diag: Dict[str, Any]) -> bool:
    cup = vegas_diag.get("cup", {})
    rel = cup.get("relative_brier_edge")
    ci_low = cup.get("relative_brier_edge_ci_low")
    pos_ratio = cup.get("positive_season_ratio")
    total = cup.get("total_seasons")
    if rel is None or ci_low is None or pos_ratio is None or total is None:
        return False
    return (
        float(rel) >= float(CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_min"])
        and float(ci_low) > float(CUP_VEGAS_EDGE_GOAL["ci_lower_bound_min"])
        and int(total) >= int(CUP_VEGAS_EDGE_GOAL["min_seasons_compared"])
        and float(pos_ratio) >= float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"])
    )


def main() -> int:
    profile = load_active_model_profile()
    data = load_training_data(allow_synthetic_fallback=False)
    validator = ValidationFramework()

    base = {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
        "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
        "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
        "strict_verification": True,
        "require_series_data_in_strict_mode": True,
        "require_oof_cup_calibration_in_strict_mode": True,
    }

    rows: List[Dict[str, Any]] = []
    for candidate in _candidate_grid(base):
        name = candidate["name"]
        overrides = candidate["overrides"]
        print(f"[phase15] evaluating {name}", flush=True)

        try:
            backtest = generate_backtest_report(
                data,
                cache_path=None,
                force_refresh=True,
                model_overrides=overrides,
            )
            core = _extract_core(backtest.get("summary", {}))

            cv = validator.cross_validate(
                data,
                model_factory=lambda: EnsemblePredictor(
                    use_neural_network=bool(overrides.get("use_neural_network", True)),
                    use_recency_weighting=bool(overrides.get("use_recency_weighting", True)),
                    use_cup_calibration=bool(overrides.get("use_cup_calibration", True)),
                    recency_decay_rate=float(overrides.get("recency_decay_rate", 0.15)),
                    cup_winner_boost=float(overrides.get("cup_winner_boost", 2.0)),
                    cup_market_prior_blend=float(overrides.get("cup_market_prior_blend", 0.0)),
                    cup_ensemble_weights=overrides.get("cup_ensemble_weights"),
                    strict_verification=False,
                    require_series_data_in_strict_mode=True,
                    require_oof_cup_calibration_in_strict_mode=True,
                ),
            )
            quality = {
                "brier_playoff": float(cv.brier_score_playoff),
                "brier_cup": float(cv.brier_score_cup),
                "log_loss_playoff": float(cv.log_loss_playoff),
                "calibration_error": float(cv.calibration_error),
            }
            row = {
                "name": name,
                "overrides": overrides,
                "core": core,
                "hardGatesPass": _hard_gates_pass(core),
                "quality": quality,
                "probabilityQualityScore": _probability_quality_score(quality),
            }
        except Exception as exc:  # pragma: no cover - defensive
            row = {
                "name": name,
                "overrides": overrides,
                "error": str(exc),
                "hardGatesPass": False,
                "probabilityQualityScore": -math.inf,
            }

        rows.append(row)

    baseline = next((r for r in rows if r["name"] == "baseline"), None)
    if baseline is None or not baseline.get("core"):
        raise RuntimeError("Phase 15 failed: baseline row missing or invalid")

    for row in rows:
        if row.get("core"):
            row["coreNonRegression"] = _core_non_regression(baseline["core"], row["core"])
            row["eligible"] = bool(row.get("hardGatesPass") and row.get("coreNonRegression"))
        else:
            row["coreNonRegression"] = False
            row["eligible"] = False

    best = baseline
    for row in rows:
        if not row.get("eligible"):
            continue
        if float(row.get("probabilityQualityScore", -math.inf)) > float(best.get("probabilityQualityScore", -math.inf)) + 1e-9:
            best = row

    selected_name = best["name"]
    selected_score = float(best.get("probabilityQualityScore", -math.inf))
    baseline_score = float(baseline.get("probabilityQualityScore", -math.inf))
    improved = selected_score > baseline_score + 1e-9

    vegas_diag = evaluate_model_vs_vegas_edge(
        historical_data=data,
        model_overrides=best.get("overrides", base),
        confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
        n_bootstrap=160,
        random_seed=RANDOM_SEED,
    )
    vegas_floor_pass = _vegas_release_floor_pass(vegas_diag)

    deployed = bool(selected_name != "baseline" and improved and vegas_floor_pass)
    reason = (
        f"deployed {selected_name}: probability quality improved {baseline_score:.2f} -> {selected_score:.2f} with release-floor-safe Vegas diagnostics"
        if deployed
        else "no safe probability-quality improvement candidate found"
    )

    if deployed:
        new_profile = copy.deepcopy(profile)
        selected = best["overrides"]
        for key in (
            "use_neural_network",
            "use_recency_weighting",
            "use_cup_calibration",
            "recency_decay_rate",
            "cup_winner_boost",
            "cup_market_prior_blend",
            "cup_ensemble_weights",
            "strict_verification",
            "require_series_data_in_strict_mode",
            "require_oof_cup_calibration_in_strict_mode",
        ):
            if key in selected:
                new_profile[key] = selected[key]
        new_profile["profileVersion"] = f"phase15-prob-quality-{datetime.now(timezone.utc).date()}"
        new_profile["optimizationMetadata"] = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": "scripts/run_phase15_probability_quality_uplift.py",
            "objective": "maximize_probability_quality_score",
            "baselineProbabilityQualityScore": baseline_score,
            "selectedProbabilityQualityScore": selected_score,
            "selectedName": selected_name,
        }
        DEFAULT_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_PROFILE_PATH.write_text(json.dumps(new_profile, indent=2) + "\n")

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase15_probability_quality_uplift",
        "baseline": baseline,
        "candidates": rows,
        "decision": {
            "deployed": deployed,
            "selected": selected_name,
            "reason": reason,
            "baselineProbabilityQualityScore": baseline_score,
            "selectedProbabilityQualityScore": selected_score,
            "improved": improved,
            "vegasReleaseFloorPass": vegas_floor_pass,
            "vegasCup": vegas_diag.get("cup", {}),
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 15 Probability Quality Uplift",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"- Deployed: `{deployed}`",
        f"- Selected: `{selected_name}`",
        f"- Reason: {reason}",
        f"- Baseline probability-quality score: `{baseline_score:.2f}`",
        f"- Selected probability-quality score: `{selected_score:.2f}`",
        f"- Vegas release-floor pass: `{vegas_floor_pass}`",
        "",
        "## Candidate Results",
        "",
        "| Candidate | Prob Quality Score | Hard Gates | Non-Regression | Eligible | Brier Playoff | Brier Cup | Log Loss Playoff | ECE |",
        "|---|---:|---|---|---|---:|---:|---:|---:|",
    ]

    rows_sorted = sorted(rows, key=lambda r: float(r.get("probabilityQualityScore", -math.inf)), reverse=True)
    for row in rows_sorted:
        q = row.get("quality", {})
        score = row.get("probabilityQualityScore")
        score_s = "N/A" if not isinstance(score, (int, float)) or not math.isfinite(score) else f"{float(score):.2f}"
        lines.append(
            f"| {row.get('name')} | {score_s} | {row.get('hardGatesPass')} | {row.get('coreNonRegression')} | {row.get('eligible')} | "
            f"{q.get('brier_playoff', 'N/A')} | {q.get('brier_cup', 'N/A')} | {q.get('log_loss_playoff', 'N/A')} | {q.get('calibration_error', 'N/A')} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
