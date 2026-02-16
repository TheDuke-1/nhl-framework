#!/usr/bin/env python3
"""
Phase 3: objective-based profile optimization using official benchmark pathway.

Optimizes:
- recency_decay_rate
- cup_winner_boost

Evaluation uses the same strict walk-forward + probability-quality stack used by
benchmark reporting, so candidate decisions are aligned with project scorecards.
"""

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.validation import ValidationFramework, generate_backtest_report
from superhuman.models import EnsemblePredictor
from superhuman.evaluation_contract import HARD_GATES
from superhuman.model_profile import DEFAULT_PROFILE_PATH, load_active_model_profile


OUT_JSON = PROJECT_ROOT / "reports" / "phase3_weight_optimization.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE3_WEIGHT_OPTIMIZATION.md"

# Keep optimization runs readable and deterministic in this environment.
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def _build_model_kwargs(profile: Dict[str, Any], decay: float, boost: float) -> Dict[str, Any]:
    return {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(decay),
        "cup_winner_boost": float(boost),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
    }


def _evaluate_candidate(data: List[Any], profile: Dict[str, Any], decay: float, boost: float) -> Dict[str, Any]:
    model_kwargs = _build_model_kwargs(profile, decay, boost)

    backtest = generate_backtest_report(
        data,
        cache_path=None,
        force_refresh=True,
        model_overrides=model_kwargs,
    )

    validator = ValidationFramework()
    cv = validator.cross_validate(
        data,
        model_factory=lambda: EnsemblePredictor(**model_kwargs),
    )

    summary = backtest.get("summary", {})
    core = {
        "top1_accuracy_pct": float(summary.get("topPickAccuracy", 0.0)),
        "top5_accuracy_pct": float(summary.get("top5Accuracy", 0.0)),
        "average_winner_rank": float(summary.get("averageWinnerRank", 999.0)),
        "playoff_f1": float(summary.get("averagePlayoffF1", 0.0)),
    }
    quality = {
        "brier_playoff": float(cv.brier_score_playoff),
        "brier_cup": float(cv.brier_score_cup),
        "log_loss_playoff": float(cv.log_loss_playoff),
        "calibration_error": float(cv.calibration_error),
    }

    # Lower score is better (all quality metrics are lower-better)
    quality_score = (
        1.0 * quality["brier_playoff"]
        + 0.8 * quality["brier_cup"]
        + 0.35 * quality["log_loss_playoff"]
        + 0.7 * quality["calibration_error"]
    )

    return {
        "decay": float(decay),
        "cup_winner_boost": float(boost),
        "core": core,
        "quality": quality,
        "quality_score": float(quality_score),
    }


def _passes_hard_gates(core: Dict[str, float]) -> bool:
    return (
        core["top1_accuracy_pct"] >= HARD_GATES["top1_accuracy_pct_min"]
        and core["top5_accuracy_pct"] >= HARD_GATES["top5_accuracy_pct_min"]
        and core["playoff_f1"] >= HARD_GATES["playoff_f1_min"]
        and core["average_winner_rank"] <= HARD_GATES["average_winner_rank_max"]
    )


def _core_non_regression(base: Dict[str, float], cand: Dict[str, float]) -> bool:
    return (
        cand["top1_accuracy_pct"] >= base["top1_accuracy_pct"] - 1e-9
        and cand["top5_accuracy_pct"] >= base["top5_accuracy_pct"] - 1e-9
        and cand["playoff_f1"] >= base["playoff_f1"] - 1e-9
        and cand["average_winner_rank"] <= base["average_winner_rank"] + 1e-9
    )


def _candidate_grid(base_decay: float, base_boost: float) -> List[Dict[str, float]]:
    # Keep search compact to avoid excessive runtime while still testing directional shifts.
    decays = sorted({round(max(0.05, base_decay - 0.05), 2), round(base_decay, 2), round(min(0.35, base_decay + 0.05), 2)})
    boosts = sorted({round(base_boost, 2), round(min(4.0, base_boost + 0.5), 2)})
    grid = []
    for decay in decays:
        for boost in boosts:
            grid.append({"decay": decay, "cup_winner_boost": boost})
    return grid


def main() -> int:
    data = load_training_data()
    active_profile = load_active_model_profile()

    base_decay = float(active_profile.get("recency_decay_rate", 0.15))
    base_boost = float(active_profile.get("cup_winner_boost", 2.0))

    baseline = _evaluate_candidate(data, active_profile, base_decay, base_boost)

    candidates = []
    for cell in _candidate_grid(base_decay, base_boost):
        decay = cell["decay"]
        boost = cell["cup_winner_boost"]
        print(f"Evaluating candidate decay={decay} boost={boost}", flush=True)
        result = _evaluate_candidate(data, active_profile, decay, boost)
        result["hard_gates_pass"] = _passes_hard_gates(result["core"])
        result["core_non_regression"] = _core_non_regression(baseline["core"], result["core"])
        candidates.append(result)

    # Sort by lower quality score
    candidates.sort(key=lambda r: r["quality_score"])

    deploy = False
    deploy_reason = "no candidate improved quality under constraints"
    deployed_candidate = baseline

    for cand in candidates:
        if not cand["hard_gates_pass"]:
            continue
        if not cand["core_non_regression"]:
            continue
        if cand["quality_score"] < baseline["quality_score"] - 1e-9:
            deploy = True
            deployed_candidate = cand
            deploy_reason = "candidate improved quality score with hard gates + non-regression"
            break

    if deploy:
        new_profile = dict(active_profile)
        new_profile["profileVersion"] = f"phase3-optimized-{datetime.now(timezone.utc).date()}"
        new_profile["recency_decay_rate"] = deployed_candidate["decay"]
        new_profile["cup_winner_boost"] = deployed_candidate["cup_winner_boost"]
        new_profile["optimizationMetadata"] = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": "scripts/run_phase3_weight_optimization.py",
            "objective": "quality_score_official_pipeline",
        }
        DEFAULT_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_PROFILE_PATH, "w") as f:
            json.dump(new_profile, f, indent=2)

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "phase3_weight_optimization_official_pipeline",
        "baseline": baseline,
        "candidates": candidates,
        "deploymentDecision": {
            "deployed": deploy,
            "reason": deploy_reason,
            "profilePath": str(DEFAULT_PROFILE_PATH),
            "selected": {
                "decay": deployed_candidate["decay"],
                "cup_winner_boost": deployed_candidate["cup_winner_boost"],
                "quality_score": deployed_candidate["quality_score"],
            },
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 3 Weight Optimization (Official Pipeline)",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Baseline",
        "",
        f"- Decay: {baseline['decay']}",
        f"- Cup Winner Boost: {baseline['cup_winner_boost']}",
        f"- Core: `{baseline['core']}`",
        f"- Quality: `{baseline['quality']}`",
        f"- Quality Score: `{baseline['quality_score']:.6f}`",
        "",
        "## Candidate Results",
        "",
        "| Decay | Cup Boost | Hard Gates | Core Non-Regression | Quality Score |",
        "|---:|---:|---|---|---:|",
    ]

    for cand in candidates:
        lines.append(
            f"| {cand['decay']:.2f} | {cand['cup_winner_boost']:.2f} | "
            f"{cand['hard_gates_pass']} | {cand['core_non_regression']} | {cand['quality_score']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Deployment Decision",
            "",
            f"- Deployed: `{deploy}`",
            f"- Reason: {deploy_reason}",
            f"- Selected Decay: `{deployed_candidate['decay']}`",
            f"- Selected Cup Winner Boost: `{deployed_candidate['cup_winner_boost']}`",
        ]
    )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
