#!/usr/bin/env python3
"""
Phase 12: goal-gap closure search toward the "undeniable" Cup-vs-Vegas target.

Builds on Phase 11 candidate outcomes and runs a tighter, anchor-based search
with strict non-regression requirements and stronger confidence checks.
"""

from __future__ import annotations

import copy
import json
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.evaluation_contract import CUP_VEGAS_EDGE_GOAL, DELTA_GUARDRAILS, HARD_GATES
from superhuman.model_profile import load_active_model_profile
from superhuman.validation import generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge


PHASE11_PATH = PROJECT_ROOT / "reports" / "phase11_constrained_edge_batch.json"
OUT_JSON = PROJECT_ROOT / "reports" / "phase12_goal_gap_closure.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE12_GOAL_GAP_CLOSURE.md"
PROFILE_ARTIFACTS = PROJECT_ROOT / "data" / "model_profiles"

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
np.seterr(all="ignore")


def _base_overrides(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(profile.get("recency_decay_rate", 0.10)),
        "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
        "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
        "monte_carlo_simulations": 2000,
        "strict_verification": True,
        "require_series_data_in_strict_mode": True,
        "require_oof_cup_calibration_in_strict_mode": True,
    }


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


def _goal_distance(vegas: Dict[str, Any]) -> Dict[str, float]:
    edge = vegas.get("cup_relative_brier_edge")
    ci_low = vegas.get("cup_relative_brier_edge_ci_low")
    ratio = vegas.get("cup_positive_season_ratio")
    target_edge = float(CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_min"])
    target_ci_low = float(CUP_VEGAS_EDGE_GOAL["ci_lower_bound_min"])
    target_ratio = float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"])

    edge_gap = max(target_edge - float(edge), 0.0) if edge is not None else 1.0
    ci_low_gap = max(target_ci_low - float(ci_low), 0.0) if ci_low is not None else 1.0
    ratio_gap = max(target_ratio - float(ratio), 0.0) if ratio is not None else 1.0
    total_gap = edge_gap + ci_low_gap + ratio_gap

    return {
        "edgeGapToMin": edge_gap,
        "ciLowGapToZero": ci_low_gap,
        "positiveRatioGap": ratio_gap,
        "totalGap": total_gap,
        "undeniable": edge_gap <= 0 and ci_low_gap <= 0 and ratio_gap <= 0,
    }


def _required_positive_seasons(total_seasons: int) -> int:
    return int(np.ceil(float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"]) * float(total_seasons) - 1e-12))


def _passes_positive_ratio_prefilter(vegas: Dict[str, Any]) -> bool:
    pos = vegas.get("cup_positive_seasons")
    total = vegas.get("cup_total_seasons")
    ratio = vegas.get("cup_positive_season_ratio")
    if isinstance(pos, (int, float)) and isinstance(total, (int, float)) and int(total) > 0:
        return int(pos) >= _required_positive_seasons(int(total))
    if ratio is None:
        return False
    return float(ratio) >= float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"])


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _normalized_mix(gb: float, nn: float, mc: float) -> Dict[str, float]:
    gb = max(0.0, gb)
    nn = max(0.0, nn)
    mc = max(0.0, mc)
    total = gb + nn + mc
    if total <= 0:
        return {"gradient_boosting": 0.0, "neural_network": 0.0, "monte_carlo": 1.0}
    return {
        "gradient_boosting": round(gb / total, 4),
        "neural_network": round(nn / total, 4),
        "monte_carlo": round(mc / total, 4),
    }


def _signature(overrides: Dict[str, Any]) -> Tuple[Any, ...]:
    mix = overrides.get("cup_ensemble_weights") or {}
    return (
        bool(overrides.get("use_cup_calibration", False)),
        round(float(overrides.get("recency_decay_rate", 0.0)), 3),
        round(float(overrides.get("cup_winner_boost", 0.0)), 3),
        round(float(overrides.get("cup_market_prior_blend", 0.0)), 3),
        round(float(mix.get("gradient_boosting", 0.0)), 4),
        round(float(mix.get("neural_network", 0.0)), 4),
        round(float(mix.get("monte_carlo", 0.0)), 4),
    )


def _phase11_anchors(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    anchors: List[Dict[str, Any]] = [copy.deepcopy(base)]
    if not PHASE11_PATH.exists():
        return anchors

    payload = json.loads(PHASE11_PATH.read_text())
    rows = payload.get("rows") or []

    # Prefer best raw edge and all strict-eligible rows.
    if payload.get("bestRawEdge", {}).get("overrides"):
        anchors.append(payload["bestRawEdge"]["overrides"])
    eligible_rows = [r for r in rows if r.get("eligible") and r.get("overrides")]
    eligible_rows.sort(key=lambda r: float((r.get("vegas") or {}).get("cup_relative_brier_edge") or -1e9), reverse=True)
    for row in eligible_rows[:2]:
        anchors.append(row["overrides"])
    return anchors


def _candidate_grid(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    anchors = _phase11_anchors(base)
    rows: List[Dict[str, Any]] = []
    seen: Set[Tuple[Any, ...]] = set()

    def add(name: str, overrides: Dict[str, Any]) -> None:
        sig = _signature(overrides)
        if sig in seen:
            return
        seen.add(sig)
        rows.append({"name": name, "overrides": overrides})

    add("baseline", copy.deepcopy(base))

    for idx, anchor in enumerate(anchors):
        mix = anchor.get("cup_ensemble_weights") or {}
        gb = float(mix.get("gradient_boosting", 0.0))
        nn = float(mix.get("neural_network", 0.0))
        mc = float(mix.get("monte_carlo", 1.0))
        anchor_blend = float(anchor.get("cup_market_prior_blend", base.get("cup_market_prior_blend", 0.0)))

        anchor_decays = sorted(
            {
                round(_clamp(float(anchor.get("recency_decay_rate", 0.10)) + delta, 0.05, 0.16), 3)
                for delta in (-0.01, 0.01)
            }
        )
        anchor_boosts = sorted(
            {
                round(_clamp(float(anchor.get("cup_winner_boost", 1.5)) + delta, 1.0, 2.5), 2)
                for delta in (-0.15, 0.0)
            }
        )
        anchor_blends = sorted(
            {
                round(_clamp(anchor_blend + delta, 0.0, 1.0), 3)
                for delta in (-0.10, 0.0)
            }
        )
        mixes = [
            _normalized_mix(gb, nn, mc),
            _normalized_mix(gb + 0.02, nn, max(mc - 0.02, 0.0)),
        ]

        for decay in anchor_decays:
            for boost in anchor_boosts:
                for blend in anchor_blends:
                    for mix_choice in mixes:
                        name = (
                            f"anchor{idx+1}-d{decay:.2f}-b{boost:.2f}-m{blend:.2f}-"
                            f"w{mix_choice['gradient_boosting']:.2f}-{mix_choice['neural_network']:.2f}-{mix_choice['monte_carlo']:.2f}"
                        )
                        add(
                            name,
                            {
                                **copy.deepcopy(base),
                                "use_cup_calibration": False,
                                "recency_decay_rate": float(decay),
                                "cup_winner_boost": float(boost),
                                "cup_market_prior_blend": float(blend),
                                "cup_ensemble_weights": mix_choice,
                            },
                        )

    return rows


def _write_profile_artifact(name: str, base_profile: Dict[str, Any], overrides: Dict[str, Any]) -> str:
    PROFILE_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    profile = copy.deepcopy(base_profile)
    profile.update(overrides)
    profile["profileVersion"] = f"phase12-{name}"
    profile["generatedAt"] = datetime.now(timezone.utc).isoformat()
    path = PROFILE_ARTIFACTS / f"phase12_{name}.json"
    path.write_text(json.dumps(profile, indent=2) + "\n")
    return str(path)


def main() -> int:
    profile = load_active_model_profile()
    base = _base_overrides(profile)
    data = load_training_data()
    vegas_bootstrap = int(os.getenv("PHASE12_VEGAS_BOOTSTRAP", "400"))
    high_conf_bootstrap = int(os.getenv("PHASE12_HIGH_CONF_BOOTSTRAP", "2000"))
    stage2_top_n = int(os.getenv("PHASE12_STAGE2_TOP_N", "14"))
    max_stage2_evals = int(os.getenv("PHASE12_MAX_STAGE2_EVALS", "0"))
    short_list_n = int(os.getenv("PHASE12_SHORTLIST_N", "6"))
    max_candidates = int(os.getenv("PHASE12_MAX_CANDIDATES", "0"))
    candidates = _candidate_grid(base)
    if max_candidates > 0:
        candidates = candidates[:max_candidates]

    rows: List[Dict[str, Any]] = []
    for cand in candidates:
        print(f"[phase12] vegas eval: {cand['name']}", flush=True)
        vegas = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=cand["overrides"],
            confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
            n_bootstrap=vegas_bootstrap,
        )
        cup = vegas.get("cup", {})
        row = {
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
            "goalDistance": _goal_distance(
                {
                    "cup_relative_brier_edge": cup.get("relative_brier_edge"),
                    "cup_relative_brier_edge_ci_low": cup.get("relative_brier_edge_ci_low"),
                    "cup_positive_season_ratio": cup.get("positive_season_ratio"),
                }
            ),
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
            "highConfidenceVegas": None,
        }
        rows.append(row)

    rows.sort(key=_edge, reverse=True)
    baseline = next(r for r in rows if r["name"] == "baseline")
    baseline_edge_value = _edge(baseline)

    # Stage-2 core evaluation for likely useful candidates.
    stage2_names = {"baseline"}
    stage2_names.update(r["name"] for r in rows[:stage2_top_n])
    for row in rows:
        if _edge(row) > baseline_edge_value + 1e-9:
            stage2_names.add(row["name"])

    baseline_core: Optional[Dict[str, float]] = None
    stage2_eval_count = 0
    for row in rows:
        if row["name"] not in stage2_names:
            continue
        if row["name"] != "baseline" and not bool(row.get("positiveRatioPrefilterPass")):
            continue
        if max_stage2_evals > 0 and row["name"] != "baseline" and stage2_eval_count >= max_stage2_evals:
            continue
        print(f"[phase12] core eval: {row['name']}", flush=True)
        backtest = generate_backtest_report(
            data,
            cache_path=None,
            force_refresh=True,
            model_overrides=row["overrides"],
        )
        row["core"] = _extract_core(backtest.get("summary", {}))
        if row["name"] != "baseline":
            stage2_eval_count += 1
        if row["name"] == "baseline":
            baseline_core = row["core"]

    if baseline_core is None:
        raise RuntimeError("phase12 baseline core metrics missing")

    for row in rows:
        core = row.get("core")
        if core is None:
            continue
        row["hardGatesPass"] = _hard_gates_pass(core)
        row["strictNonRegression"] = _strict_non_reg(baseline_core, core)
        row["eligible"] = bool(
            row["hardGatesPass"]
            and row["strictNonRegression"]
            and bool(row.get("positiveRatioPrefilterPass"))
            and (_edge(row) > baseline_edge_value + 1e-9)
        )

    # Stronger confidence checks on the short list.
    short_names = {r["name"] for r in rows[:short_list_n] if r.get("positiveRatioPrefilterPass")}
    short_names.update(r["name"] for r in rows if r.get("eligible") and r.get("positiveRatioPrefilterPass"))
    short_names.add("baseline")
    for row in rows:
        if row["name"] not in short_names:
            continue
        print(f"[phase12] hi-conf eval: {row['name']}", flush=True)
        vegas = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=row["overrides"],
            confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
            n_bootstrap=high_conf_bootstrap,
        )
        cup = vegas.get("cup", {})
        hi = {
            "cup_relative_brier_edge": cup.get("relative_brier_edge"),
            "cup_relative_brier_edge_ci_low": cup.get("relative_brier_edge_ci_low"),
            "cup_relative_brier_edge_ci_high": cup.get("relative_brier_edge_ci_high"),
            "cup_positive_season_ratio": cup.get("positive_season_ratio"),
        }
        row["highConfidenceVegas"] = hi
        row["goalDistance"] = _goal_distance(hi)

    def goal_total(r: Dict[str, Any]) -> float:
        return float((r.get("goalDistance") or {}).get("totalGap", 1e9))

    sorted_by_goal = sorted(rows, key=goal_total)
    closest_goal = sorted_by_goal[0] if sorted_by_goal else None
    eligible = [r for r in rows if r.get("eligible")]
    best_eligible = eligible[0] if eligible else None
    undeniable_candidates = [r for r in rows if (r.get("goalDistance") or {}).get("undeniable")]
    best_raw_edge = rows[0] if rows else None

    artifacts = {
        "baseline": _write_profile_artifact("baseline_reference", profile, baseline["overrides"]),
    }
    if best_raw_edge:
        artifacts["bestRawEdge"] = _write_profile_artifact("best_raw_edge", profile, best_raw_edge["overrides"])
    if best_eligible:
        artifacts["bestEligible"] = _write_profile_artifact("best_eligible", profile, best_eligible["overrides"])
    if closest_goal:
        artifacts["closestGoal"] = _write_profile_artifact("closest_goal", profile, closest_goal["overrides"])

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase12_goal_gap_closure",
        "summary": {
            "totalCandidates": len(rows),
            "coreEvaluatedCandidates": len([r for r in rows if r.get("core") is not None]),
            "highConfidenceEvaluatedCandidates": len([r for r in rows if r.get("highConfidenceVegas") is not None]),
            "positiveRatioPrefilterPassCount": len([r for r in rows if r.get("positiveRatioPrefilterPass")]),
            "baselineEdge": baseline_edge_value,
            "bestRawEdgeName": best_raw_edge["name"] if best_raw_edge else None,
            "bestRawEdge": _edge(best_raw_edge) if best_raw_edge else None,
            "eligibleCount": len(eligible),
            "bestEligibleName": best_eligible["name"] if best_eligible else None,
            "bestEligibleEdge": _edge(best_eligible) if best_eligible else None,
            "closestGoalName": closest_goal["name"] if closest_goal else None,
            "closestGoalDistance": (closest_goal.get("goalDistance") if closest_goal else None),
            "undeniableCount": len(undeniable_candidates),
            "deployRecommendation": (
                "CANDIDATE_READY_FOR_PROMOTION_REVIEW"
                if undeniable_candidates
                else "CONTINUE_AB_TRACK" if eligible else "KEEP_BASELINE_RESEARCH"
            ),
            "autoDeploy": False,
        },
        "baseline": baseline,
        "bestRawEdge": best_raw_edge,
        "bestEligible": best_eligible,
        "closestGoal": closest_goal,
        "rows": rows,
        "profileArtifacts": artifacts,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    target = CUP_VEGAS_EDGE_GOAL
    lines = [
        "# Phase 12 Goal Gap Closure",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        f"- Total candidates: `{report['summary']['totalCandidates']}`",
        f"- Core evaluated: `{report['summary']['coreEvaluatedCandidates']}`",
        f"- High-confidence checked: `{report['summary']['highConfidenceEvaluatedCandidates']}`",
        f"- Positive-ratio prefilter pass: `{report['summary']['positiveRatioPrefilterPassCount']}`",
        f"- Baseline edge: `{report['summary']['baselineEdge']}`",
        f"- Best raw edge: `{report['summary']['bestRawEdgeName']}` ({report['summary']['bestRawEdge']})",
        f"- Best eligible: `{report['summary']['bestEligibleName']}` ({report['summary']['bestEligibleEdge']})",
        f"- Closest-to-goal candidate: `{report['summary']['closestGoalName']}`",
        f"- Undeniable candidates: `{report['summary']['undeniableCount']}`",
        f"- Target floor: `{target['relative_brier_improvement_min']}` | CI-low floor: `{target['ci_lower_bound_min']}` | Positive-season floor: `{target['min_positive_season_ratio']}`",
        f"- Recommendation: `{report['summary']['deployRecommendation']}`",
        "",
        "## Candidate Board",
        "",
        "| Candidate | Edge | CI Low | Pos Ratio | Prefilter | Goal Gap | Top1 | Top5 | F1 | Avg Rank | Hard Gates | Strict Non-Reg | Eligible |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|---|",
    ]

    for row in rows:
        vegas = row.get("highConfidenceVegas") or row.get("vegas") or {}
        core = row.get("core")
        gd = row.get("goalDistance") or {}
        edge_txt = "N/A" if vegas.get("cup_relative_brier_edge") is None else f"{vegas['cup_relative_brier_edge']:.4f}"
        ci_low_txt = "N/A" if vegas.get("cup_relative_brier_edge_ci_low") is None else f"{vegas['cup_relative_brier_edge_ci_low']:.4f}"
        ratio_txt = "N/A" if vegas.get("cup_positive_season_ratio") is None else f"{vegas['cup_positive_season_ratio']:.3f}"
        gap_txt = "N/A" if gd.get("totalGap") is None else f"{gd['totalGap']:.4f}"
        top1 = "N/A" if core is None else f"{core['top1_accuracy_pct']:.1f}"
        top5 = "N/A" if core is None else f"{core['top5_accuracy_pct']:.1f}"
        f1 = "N/A" if core is None else f"{core['playoff_f1']:.3f}"
        avg_rank = "N/A" if core is None else f"{core['average_winner_rank']:.2f}"
        lines.append(
            f"| {row['name']} | "
            f"{edge_txt} | "
            f"{ci_low_txt} | "
            f"{ratio_txt} | "
            f"{row.get('positiveRatioPrefilterPass')} | "
            f"{gap_txt} | "
            f"{top1} | {top5} | {f1} | {avg_rank} | "
            f"{row.get('hardGatesPass')} | {row.get('strictNonRegression')} | {row.get('eligible')} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
