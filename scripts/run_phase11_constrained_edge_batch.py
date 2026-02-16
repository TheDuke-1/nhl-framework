#!/usr/bin/env python3
"""
Phase 11: constrained Cup-edge search under strict non-regression.

Focuses on a narrow profile band around the edge-preserving experimental lane,
while enforcing hard gates + strict non-regression vs baseline.
"""

from __future__ import annotations

import copy
import json
import math
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
from superhuman.model_profile import load_active_model_profile
from superhuman.validation import generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge


OUT_JSON = PROJECT_ROOT / "reports" / "phase11_constrained_edge_batch.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE11_CONSTRAINED_EDGE_BATCH.md"
PROFILE_ARTIFACTS = PROJECT_ROOT / "data" / "model_profiles"

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
    rows: List[Dict[str, Any]] = [{"name": "baseline", "overrides": copy.deepcopy(base)}]

    decays = [0.08, 0.10]
    boosts = [1.5, 2.0]
    mixes = [
        {"gradient_boosting": 0.00, "neural_network": 0.00, "monte_carlo": 1.00},
        {"gradient_boosting": 0.05, "neural_network": 0.00, "monte_carlo": 0.95},
    ]

    baseline_blend = float(base.get("cup_market_prior_blend", 0.0))
    blend_grid = sorted({round(min(0.35, baseline_blend), 2), round(baseline_blend, 2)})

    for decay in decays:
        for boost in boosts:
            for mix in mixes:
                for blend in blend_grid:
                    name = (
                        f"constrained-d{decay:.2f}-b{boost:.1f}-"
                        f"m{blend:.2f}-"
                        f"w{mix['gradient_boosting']:.2f}-{mix['neural_network']:.2f}-{mix['monte_carlo']:.2f}"
                    )
                    rows.append(
                        {
                            "name": name,
                            "overrides": {
                                **copy.deepcopy(base),
                                "use_cup_calibration": False,
                                "recency_decay_rate": float(decay),
                                "cup_winner_boost": float(boost),
                                "cup_market_prior_blend": float(blend),
                                "cup_ensemble_weights": mix,
                            },
                        }
                    )

    for blend in blend_grid:
        name = (
            f"constrained-calibrated-mc100-m{blend:.2f}"
        )
        rows.append(
            {
                "name": name,
                "overrides": {
                    **copy.deepcopy(base),
                    "use_cup_calibration": True,
                    "cup_market_prior_blend": float(blend),
                    "cup_ensemble_weights": {"gradient_boosting": 0.0, "neural_network": 0.0, "monte_carlo": 1.0},
                },
            }
        )
        rows.append(
            {
                "name": f"constrained-calibrated-mc95-m{blend:.2f}",
                "overrides": {
                    **copy.deepcopy(base),
                    "use_cup_calibration": True,
                    "cup_market_prior_blend": float(blend),
                    "cup_ensemble_weights": {"gradient_boosting": 0.05, "neural_network": 0.0, "monte_carlo": 0.95},
                },
            }
        )

    return rows


def _extract_core(summary: Dict[str, Any]) -> Dict[str, float]:
    return {
        "top1_accuracy_pct": float(summary.get("topPickAccuracy", 0.0)),
        "top5_accuracy_pct": float(summary.get("top5Accuracy", 0.0)),
        "average_winner_rank": float(summary.get("averageWinnerRank", 999.0)),
        "playoff_f1": float(summary.get("averagePlayoffF1", 0.0)),
    }


def _hard_gates_pass(core: Dict[str, float]) -> bool:
    return (
        core["top1_accuracy_pct"] >= HARD_GATES["top1_accuracy_pct_min"]
        and core["top5_accuracy_pct"] >= HARD_GATES["top5_accuracy_pct_min"]
        and core["playoff_f1"] >= HARD_GATES["playoff_f1_min"]
        and core["average_winner_rank"] <= HARD_GATES["average_winner_rank_max"]
    )


def _strict_non_reg(base: Dict[str, float], cand: Dict[str, float]) -> bool:
    return (
        (base["top1_accuracy_pct"] - cand["top1_accuracy_pct"]) <= DELTA_GUARDRAILS["top1_accuracy_pct_max_drop"]
        and (base["top5_accuracy_pct"] - cand["top5_accuracy_pct"]) <= DELTA_GUARDRAILS["top5_accuracy_pct_max_drop"]
        and (base["playoff_f1"] - cand["playoff_f1"]) <= DELTA_GUARDRAILS["playoff_f1_max_drop"]
        and (cand["average_winner_rank"] - base["average_winner_rank"]) <= DELTA_GUARDRAILS["average_winner_rank_max_increase"]
    )


def _edge(row: Dict[str, Any]) -> float:
    edge = row.get("vegas", {}).get("cup_relative_brier_edge")
    if edge is None:
        return -1e9
    return float(edge)


def _required_positive_seasons(total_seasons: int) -> int:
    return int(math.ceil(float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"]) * float(total_seasons) - 1e-12))


def _passes_positive_ratio_prefilter(vegas: Dict[str, Any]) -> bool:
    ratio = vegas.get("cup_positive_season_ratio")
    pos = vegas.get("cup_positive_seasons")
    total = vegas.get("cup_total_seasons")
    if isinstance(pos, (int, float)) and isinstance(total, (int, float)) and int(total) > 0:
        return int(pos) >= _required_positive_seasons(int(total))
    if ratio is None:
        return False
    return float(ratio) >= float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"])


def _write_profile_artifact(name: str, base_profile: Dict[str, Any], overrides: Dict[str, Any]) -> str:
    PROFILE_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    profile = copy.deepcopy(base_profile)
    profile.update(overrides)
    profile["profileVersion"] = f"phase11-{name}"
    profile["generatedAt"] = datetime.now(timezone.utc).isoformat()
    path = PROFILE_ARTIFACTS / f"phase11_{name}.json"
    path.write_text(json.dumps(profile, indent=2) + "\n")
    return str(path)


def main() -> int:
    profile = load_active_model_profile()
    base = _base_overrides(profile)
    data = load_training_data()
    candidates = _candidate_grid(base)

    rows: List[Dict[str, Any]] = []
    for cand in candidates:
        print(f"[phase11] vegas eval: {cand['name']}", flush=True)
        vegas = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=cand["overrides"],
            confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
            n_bootstrap=300,
        )
        cup = vegas.get("cup", {})
        rows.append(
            {
                "name": cand["name"],
                "overrides": cand["overrides"],
                "vegas": {
                    "cup_relative_brier_edge": cup.get("relative_brier_edge"),
                    "cup_relative_brier_edge_ci_low": cup.get("relative_brier_edge_ci_low"),
                    "cup_relative_brier_edge_ci_high": cup.get("relative_brier_edge_ci_high"),
                    "cup_model_brier": cup.get("model_brier"),
                    "cup_vegas_brier": cup.get("vegas_brier"),
                    "cup_positive_season_ratio": cup.get("positive_season_ratio"),
                    "cup_positive_seasons": cup.get("positive_seasons"),
                    "cup_total_seasons": cup.get("total_seasons"),
                },
                "positiveRatioPrefilterPass": _passes_positive_ratio_prefilter(
                    {
                        "cup_positive_season_ratio": cup.get("positive_season_ratio"),
                        "cup_positive_seasons": cup.get("positive_seasons"),
                        "cup_total_seasons": cup.get("total_seasons"),
                    }
                ),
                "core": None,
                "hardGatesPass": None,
                "strictNonRegression": None,
                "eligible": False,
            }
        )

    rows.sort(key=_edge, reverse=True)
    stage2_names = {"baseline"}
    stage2_names.update(r["name"] for r in rows[:12])
    # Ensure all edge-improvers are core-checked.
    baseline_edge = next(r for r in rows if r["name"] == "baseline")
    baseline_edge_value = _edge(baseline_edge)
    for row in rows:
        if _edge(row) > baseline_edge_value + 1e-9:
            stage2_names.add(row["name"])

    baseline_core: Optional[Dict[str, float]] = None
    for row in rows:
        if row["name"] not in stage2_names:
            continue
        if row["name"] != "baseline" and not bool(row.get("positiveRatioPrefilterPass")):
            continue
        print(f"[phase11] core eval: {row['name']}", flush=True)
        backtest = generate_backtest_report(
            data,
            cache_path=None,
            force_refresh=True,
            model_overrides=row["overrides"],
        )
        row["core"] = _extract_core(backtest.get("summary", {}))
        if row["name"] == "baseline":
            baseline_core = row["core"]

    if baseline_core is None:
        raise RuntimeError("phase11 baseline core metrics missing")

    for row in rows:
        core = row.get("core")
        if not core:
            continue
        row["hardGatesPass"] = _hard_gates_pass(core)
        row["strictNonRegression"] = _strict_non_reg(baseline_core, core)
        row["eligible"] = bool(
            row["hardGatesPass"]
            and row["strictNonRegression"]
            and bool(row.get("positiveRatioPrefilterPass"))
            and (_edge(row) > baseline_edge_value + 1e-9)
        )

    eligible = [r for r in rows if r.get("eligible")]
    best_eligible = eligible[0] if eligible else None

    best_raw_edge = rows[0] if rows else None
    artifacts = {}
    artifacts["baseline"] = _write_profile_artifact("baseline_reference", profile, baseline_edge["overrides"])
    if best_raw_edge:
        artifacts["bestRawEdge"] = _write_profile_artifact("best_raw_edge", profile, best_raw_edge["overrides"])
    if best_eligible:
        artifacts["bestEligible"] = _write_profile_artifact("best_eligible", profile, best_eligible["overrides"])

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase11_constrained_edge_batch",
        "summary": {
            "totalCandidates": len(rows),
            "coreEvaluatedCandidates": len([r for r in rows if r.get("core") is not None]),
            "positiveRatioPrefilterPassCount": len([r for r in rows if r.get("positiveRatioPrefilterPass")]),
            "baselineEdge": baseline_edge_value,
            "bestRawEdge": _edge(best_raw_edge) if best_raw_edge else None,
            "bestRawEdgeName": best_raw_edge["name"] if best_raw_edge else None,
            "eligibleCount": len(eligible),
            "bestEligibleName": best_eligible["name"] if best_eligible else None,
            "bestEligibleEdge": _edge(best_eligible) if best_eligible else None,
            "deployRecommendation": "KEEP_BASELINE" if not best_eligible else "CANDIDATE_READY_FOR_REVIEW",
            "autoDeploy": False,
        },
        "baseline": baseline_edge,
        "bestRawEdge": best_raw_edge,
        "bestEligible": best_eligible,
        "rows": rows,
        "profileArtifacts": artifacts,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 11 Constrained Edge Batch",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        f"- Total candidates: `{report['summary']['totalCandidates']}`",
        f"- Core evaluated: `{report['summary']['coreEvaluatedCandidates']}`",
        f"- Positive-ratio prefilter pass: `{report['summary']['positiveRatioPrefilterPassCount']}`",
        f"- Baseline edge: `{report['summary']['baselineEdge']}`",
        f"- Best raw edge: `{report['summary']['bestRawEdgeName']}` ({report['summary']['bestRawEdge']})",
        f"- Eligible candidates: `{report['summary']['eligibleCount']}`",
        f"- Best eligible: `{report['summary']['bestEligibleName']}` ({report['summary']['bestEligibleEdge']})",
        f"- Recommendation: `{report['summary']['deployRecommendation']}`",
        "",
        "## Candidate Board",
        "",
        "| Candidate | Edge | CI Low | Pos Ratio | Prefilter | Top1 | Top5 | F1 | Avg Rank | Hard Gates | Strict Non-Reg | Eligible |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        edge = row.get("vegas", {}).get("cup_relative_brier_edge")
        ci_low = row.get("vegas", {}).get("cup_relative_brier_edge_ci_low")
        pos_ratio = row.get("vegas", {}).get("cup_positive_season_ratio")
        core = row.get("core")
        top1 = "N/A" if core is None else f"{core['top1_accuracy_pct']:.1f}"
        top5 = "N/A" if core is None else f"{core['top5_accuracy_pct']:.1f}"
        f1 = "N/A" if core is None else f"{core['playoff_f1']:.3f}"
        avg_rank = "N/A" if core is None else f"{core['average_winner_rank']:.2f}"
        lines.append(
            f"| {row['name']} | "
            f"{'N/A' if edge is None else f'{edge:.4f}'} | "
            f"{'N/A' if ci_low is None else f'{ci_low:.4f}'} | "
            f"{'N/A' if pos_ratio is None else f'{pos_ratio:.3f}'} | "
            f"{row.get('positiveRatioPrefilterPass')} | "
            f"{top1} | {top5} | {f1} | {avg_rank} | "
            f"{row.get('hardGatesPass')} | {row.get('strictNonRegression')} | {row.get('eligible')} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
