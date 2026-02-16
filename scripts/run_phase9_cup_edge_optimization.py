#!/usr/bin/env python3
"""
Phase 9: candidate search at full compute budget for Cup-vs-Vegas edge.

Searches profile candidates using strict walk-forward Vegas diagnostics, then
applies core hard-gate + non-regression checks before optional deployment.
"""

from __future__ import annotations

import copy
import json
import math
import os
import subprocess
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.evaluation_contract import CUP_VEGAS_EDGE_GOAL, DELTA_GUARDRAILS, HARD_GATES
from superhuman.model_profile import DEFAULT_PROFILE_PATH, load_active_model_profile
from superhuman.validation import generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge


OUT_JSON = PROJECT_ROOT / "reports" / "phase9_cup_edge_optimization.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE9_CUP_EDGE_OPTIMIZATION.md"

# Keep search output readable; strict warning failures are handled in release gates.
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
np.seterr(all="ignore")


def _base_overrides(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
        "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
        "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
        "monte_carlo_simulations": 2000,
        "strict_verification": True,
        "require_series_data_in_strict_mode": True,
        "require_oof_cup_calibration_in_strict_mode": True,
    }


def _candidate_grid(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = [
        {"name": "baseline", "overrides": copy.deepcopy(base)},
        {"name": "decay-022-boost15", "overrides": {**copy.deepcopy(base), "recency_decay_rate": 0.22, "cup_winner_boost": 1.5}},
        {"name": "decay-025-boost15", "overrides": {**copy.deepcopy(base), "recency_decay_rate": 0.25, "cup_winner_boost": 1.5}},
        {"name": "decay-025-boost20", "overrides": {**copy.deepcopy(base), "recency_decay_rate": 0.25, "cup_winner_boost": 2.0}},
        {"name": "decay-018-boost20", "overrides": {**copy.deepcopy(base), "recency_decay_rate": 0.18, "cup_winner_boost": 2.0}},
        {"name": "decay-008-boost20", "overrides": {**copy.deepcopy(base), "recency_decay_rate": 0.08, "cup_winner_boost": 2.0}},
        {
            "name": "nn-nocal-w020-020-060",
            "overrides": {
                **copy.deepcopy(base),
                "use_neural_network": True,
                "use_cup_calibration": False,
                "recency_decay_rate": 0.25,
                "cup_winner_boost": 1.5,
                "cup_ensemble_weights": {
                    "gradient_boosting": 0.2,
                    "neural_network": 0.2,
                    "monte_carlo": 0.6,
                },
            },
        },
        {
            "name": "nn-nocal-w020-000-080",
            "overrides": {
                **copy.deepcopy(base),
                "use_neural_network": True,
                "use_cup_calibration": False,
                "recency_decay_rate": 0.25,
                "cup_winner_boost": 1.5,
                "cup_ensemble_weights": {
                    "gradient_boosting": 0.2,
                    "neural_network": 0.0,
                    "monte_carlo": 0.8,
                },
            },
        },
        {
            "name": "nn-nocal-w040-020-040",
            "overrides": {
                **copy.deepcopy(base),
                "use_neural_network": True,
                "use_cup_calibration": False,
                "recency_decay_rate": 0.25,
                "cup_winner_boost": 1.5,
                "cup_ensemble_weights": {
                    "gradient_boosting": 0.4,
                    "neural_network": 0.2,
                    "monte_carlo": 0.4,
                },
            },
        },
        {
            "name": "nn-nocal-w000-000-100",
            "overrides": {
                **copy.deepcopy(base),
                "use_neural_network": True,
                "use_cup_calibration": False,
                "recency_decay_rate": 0.25,
                "cup_winner_boost": 1.5,
                "cup_ensemble_weights": {
                    "gradient_boosting": 0.0,
                    "neural_network": 0.0,
                    "monte_carlo": 1.0,
                },
            },
        },
        {
            "name": "nn-cal-w020-020-060",
            "overrides": {
                **copy.deepcopy(base),
                "use_neural_network": True,
                "use_cup_calibration": True,
                "recency_decay_rate": 0.25,
                "cup_winner_boost": 1.5,
                "cup_ensemble_weights": {
                    "gradient_boosting": 0.2,
                    "neural_network": 0.2,
                    "monte_carlo": 0.6,
                },
            },
        },
    ]
    return rows


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


def _extract_core(summary: Dict[str, Any]) -> Dict[str, float]:
    return {
        "top1_accuracy_pct": float(summary.get("topPickAccuracy", 0.0)),
        "top5_accuracy_pct": float(summary.get("top5Accuracy", 0.0)),
        "average_winner_rank": float(summary.get("averageWinnerRank", 999.0)),
        "playoff_f1": float(summary.get("averagePlayoffF1", 0.0)),
    }


def _extract_vegas(vegas_diag: Dict[str, Any]) -> Dict[str, Any]:
    cup = vegas_diag.get("cup", {})
    return {
        "available": bool(vegas_diag.get("available", False)),
        "cup_relative_brier_edge": cup.get("relative_brier_edge"),
        "cup_relative_brier_edge_ci_low": cup.get("relative_brier_edge_ci_low"),
        "cup_relative_brier_edge_ci_high": cup.get("relative_brier_edge_ci_high"),
        "cup_model_brier": cup.get("model_brier"),
        "cup_vegas_brier": cup.get("vegas_brier"),
        "cup_positive_season_ratio": cup.get("positive_season_ratio"),
        "cup_positive_seasons": cup.get("positive_seasons"),
        "cup_total_seasons": cup.get("total_seasons"),
    }


def _required_positive_seasons(total_seasons: int) -> int:
    return int(math.ceil(float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"]) * float(total_seasons) - 1e-12))


def _passes_positive_ratio_prefilter(vegas: Dict[str, Any]) -> bool:
    pos = vegas.get("cup_positive_seasons")
    total = vegas.get("cup_total_seasons")
    ratio = vegas.get("cup_positive_season_ratio")
    if isinstance(pos, (int, float)) and isinstance(total, (int, float)) and int(total) > 0:
        return int(pos) >= _required_positive_seasons(int(total))
    if ratio is None:
        return False
    return float(ratio) >= float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"])


def _passes_strong_promotion_gate(vegas: Dict[str, Any]) -> bool:
    edge = vegas.get("cup_relative_brier_edge")
    strong_min = CUP_VEGAS_EDGE_GOAL.get("relative_brier_improvement_strong")
    return (
        isinstance(edge, (int, float))
        and isinstance(strong_min, (int, float))
        and float(edge) >= float(strong_min)
    )


def _run_benchmark_refresh() -> Dict[str, Any]:
    if os.getenv("PHASE9_SKIP_BENCHMARK_REFRESH", "0") == "1":
        return {
            "cmd": "python3 scripts/update_benchmark_metrics.py",
            "returncode": 0,
            "stdout": "Skipped benchmark refresh (PHASE9_SKIP_BENCHMARK_REFRESH=1)",
            "stderr": "",
            "skipped": True,
        }

    timeout_seconds = int(os.getenv("PHASE9_BENCHMARK_TIMEOUT_SECONDS", "900"))
    try:
        proc = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "update_benchmark_metrics.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return {
            "cmd": "python3 scripts/update_benchmark_metrics.py",
            "returncode": 124,
            "stdout": stdout.strip(),
            "stderr": f"Timed out after {timeout_seconds}s",
            "skipped": False,
        }

    return {
        "cmd": "python3 scripts/update_benchmark_metrics.py",
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "skipped": False,
    }


def main() -> int:
    profile = load_active_model_profile()
    baseline_overrides = _base_overrides(profile)
    data = load_training_data()
    candidates = _candidate_grid(baseline_overrides)

    rows: List[Dict[str, Any]] = []

    # Stage 1: evaluate Vegas edge objective for all candidates.
    for cand in candidates:
        name = cand["name"]
        overrides = cand["overrides"]
        print(f"[phase9] stage1 vegas edge: {name}", flush=True)
        try:
            vegas_diag = evaluate_model_vs_vegas_edge(
                historical_data=data,
                model_overrides=overrides,
                confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
                n_bootstrap=300,
            )
            vegas = _extract_vegas(vegas_diag)
            rows.append(
                {
                    "name": name,
                    "overrides": overrides,
                    "vegas": vegas,
                    "positiveRatioPrefilterPass": _passes_positive_ratio_prefilter(vegas),
                    "core": None,
                    "hardGatesPass": None,
                    "coreNonRegression": None,
                    "eligibleForDeploy": False,
                    "error": None,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "name": name,
                    "overrides": overrides,
                    "vegas": {},
                    "positiveRatioPrefilterPass": False,
                    "core": None,
                    "hardGatesPass": False,
                    "coreNonRegression": False,
                    "eligibleForDeploy": False,
                    "error": str(exc),
                }
            )

    def _edge_value(row: Dict[str, Any]) -> float:
        edge = row.get("vegas", {}).get("cup_relative_brier_edge")
        if edge is None:
            return -1e9
        return float(edge)

    rows_sorted = sorted(rows, key=_edge_value, reverse=True)
    stage2_names = {rows_sorted[0]["name"]} if rows_sorted else set()
    for row in rows_sorted[:6]:
        stage2_names.add(row["name"])
    stage2_names.add("baseline")

    # Stage 2: run full core-gate evaluation only for top edge candidates.
    baseline_core: Optional[Dict[str, float]] = None
    for row in rows:
        if row["name"] not in stage2_names:
            continue
        if row.get("error"):
            continue
        if row["name"] != "baseline" and not bool(row.get("positiveRatioPrefilterPass")):
            continue
        print(f"[phase9] stage2 core gates: {row['name']}", flush=True)
        backtest = generate_backtest_report(
            data,
            cache_path=None,
            force_refresh=True,
            model_overrides=row["overrides"],
        )
        core = _extract_core(backtest.get("summary", {}))
        row["core"] = core
        if row["name"] == "baseline":
            baseline_core = core

    if baseline_core is None:
        raise RuntimeError("Phase 9 failed: baseline core metrics unavailable")

    for row in rows:
        core = row.get("core")
        if not core:
            continue
        row["hardGatesPass"] = _hard_gates_pass(core)
        row["coreNonRegression"] = _core_non_regression(baseline_core, core)
        row["eligibleForDeploy"] = bool(row["hardGatesPass"] and row["coreNonRegression"])
        row["strongPromotionGatePass"] = _passes_strong_promotion_gate(row.get("vegas", {}))
        row["eligibleForPromotion"] = bool(row["eligibleForDeploy"] and row["strongPromotionGatePass"])
        if row["name"] != "baseline" and not bool(row.get("positiveRatioPrefilterPass")):
            row["eligibleForDeploy"] = False
            row["eligibleForPromotion"] = False

    baseline_row = next((r for r in rows if r["name"] == "baseline"), None)
    if baseline_row is None:
        raise RuntimeError("Phase 9 failed: missing baseline row")

    best = baseline_row
    for row in rows:
        if not row.get("eligibleForDeploy"):
            continue
        if _edge_value(row) > _edge_value(best) + 1e-9:
            best = row
            continue
        if abs(_edge_value(row) - _edge_value(best)) <= 1e-9:
            row_brier = row.get("vegas", {}).get("cup_model_brier")
            best_brier = best.get("vegas", {}).get("cup_model_brier")
            if row_brier is not None and best_brier is not None and row_brier < best_brier - 1e-12:
                best = row

    best_improves_baseline = _edge_value(best) > _edge_value(baseline_row) + 1e-9
    strong_threshold = float(CUP_VEGAS_EDGE_GOAL.get("relative_brier_improvement_strong", 0.0))
    selected_edge = best.get("vegas", {}).get("cup_relative_brier_edge")
    selected_clears_strong = bool(best.get("strongPromotionGatePass"))
    deployed = best["name"] != "baseline" and best_improves_baseline and selected_clears_strong

    if deployed:
        deploy_reason = (
            f"deployed `{best['name']}` with improved Cup-vs-Vegas relative edge and "
            f"strong-tier promotion gate pass ({selected_edge:.4f} >= {strong_threshold:.4f})"
        )
    elif best["name"] == "baseline":
        deploy_reason = "no eligible candidate improved Cup-vs-Vegas edge over baseline"
    elif not best_improves_baseline:
        deploy_reason = "selected candidate did not improve Cup-vs-Vegas edge over baseline"
    else:
        deploy_reason = (
            f"selected `{best['name']}` improved edge but failed strong-tier promotion gate "
            f"({selected_edge if isinstance(selected_edge, (int, float)) else 'N/A'} < {strong_threshold:.4f})"
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
        new_profile["profileVersion"] = f"phase9-cup-edge-{datetime.now(timezone.utc).date()}"
        new_profile["optimizationMetadata"] = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "source": "scripts/run_phase9_cup_edge_optimization.py",
            "objective": "maximize_cup_relative_brier_edge_vs_vegas",
            "baselineEdge": baseline_row.get("vegas", {}).get("cup_relative_brier_edge"),
            "selectedEdge": best.get("vegas", {}).get("cup_relative_brier_edge"),
        }
        DEFAULT_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_PROFILE_PATH.write_text(json.dumps(new_profile, indent=2) + "\n")

    benchmark_refresh = _run_benchmark_refresh()

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase9_cup_edge_optimization",
        "baseline": {
            "name": baseline_row["name"],
            "core": baseline_row.get("core"),
            "vegas": baseline_row.get("vegas"),
        },
        "candidates": rows,
        "decision": {
            "deployed": deployed,
            "selected": best["name"],
            "reason": deploy_reason,
            "goalTarget": CUP_VEGAS_EDGE_GOAL,
            "selectedEdge": selected_edge,
            "selectedEdgeCiLow": best.get("vegas", {}).get("cup_relative_brier_edge_ci_low"),
            "selectedPositiveSeasonRatio": best.get("vegas", {}).get("cup_positive_season_ratio"),
            "selectedImprovesBaseline": best_improves_baseline,
            "promotionEdgeThresholdStrong": strong_threshold,
            "selectedClearsStrongPromotionGate": selected_clears_strong,
            "positiveRatioPrefilterPassCount": len([r for r in rows if r.get("positiveRatioPrefilterPass")]),
        },
        "benchmarkRefresh": benchmark_refresh,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 9 Cup Edge Optimization",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        f"- Deployed: `{deployed}`",
        f"- Selected: `{best['name']}`",
        f"- Reason: {deploy_reason}",
        f"- Promotion strong-tier edge threshold: `{strong_threshold:.4f}`",
        f"- Selected clears strong-tier gate: `{selected_clears_strong}`",
        f"- Positive-ratio prefilter pass count: `{report['decision']['positiveRatioPrefilterPassCount']}`",
        "",
        "## Candidate Results",
        "",
        "| Candidate | Edge | CI Low | Pos Season Ratio | Prefilter | Hard Gates | Non-Regression | Eligible | Strong Gate | Promotion Eligible |",
        "|---|---:|---:|---:|---|---|---|---|---|---|",
    ]
    rows_for_table = sorted(rows, key=_edge_value, reverse=True)
    for row in rows_for_table:
        vegas = row.get("vegas", {})
        edge = vegas.get("cup_relative_brier_edge")
        ci_low = vegas.get("cup_relative_brier_edge_ci_low")
        pos = vegas.get("cup_positive_season_ratio")
        edge_s = "N/A" if edge is None else f"{edge:.4f}"
        ci_s = "N/A" if ci_low is None else f"{ci_low:.4f}"
        pos_s = "N/A" if pos is None else f"{pos:.3f}"
        lines.append(
            f"| {row['name']} | {edge_s} | {ci_s} | {pos_s} | "
            f"{row.get('positiveRatioPrefilterPass')} | {row.get('hardGatesPass')} | "
            f"{row.get('coreNonRegression')} | {row.get('eligibleForDeploy')} | "
            f"{row.get('strongPromotionGatePass')} | {row.get('eligibleForPromotion')} |"
        )

    lines.extend(
        [
            "",
            "## Benchmark Refresh",
            "",
            f"- Command: `{benchmark_refresh['cmd']}`",
            f"- Status: `{'PASS' if benchmark_refresh['returncode'] == 0 else 'FAIL'}`",
        ]
    )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0 if benchmark_refresh["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
