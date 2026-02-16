#!/usr/bin/env python3
"""
Phase 13: strict-eligible feature push toward undeniable Cup-vs-Vegas target.

Uses only Phase 12 strict-eligible candidates as anchors, adds targeted
feature-level tweaks, and enforces a hard positive-season-ratio prefilter.
"""

from __future__ import annotations

import copy
import json
import math
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


PHASE12_PATH = PROJECT_ROOT / "reports" / "phase12_goal_gap_closure.json"
OUT_JSON = PROJECT_ROOT / "reports" / "phase13_eligible_feature_push.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE13_ELIGIBLE_FEATURE_PUSH.md"
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


def _ratio(row: Dict[str, Any]) -> float:
    ratio = row.get("vegas", {}).get("cup_positive_season_ratio")
    if ratio is None:
        return -1e9
    return float(ratio)


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


def _load_phase12_eligible_rows() -> Tuple[List[Dict[str, Any]], str]:
    if not PHASE12_PATH.exists():
        raise RuntimeError(f"Missing prerequisite report: {PHASE12_PATH}")
    payload = json.loads(PHASE12_PATH.read_text())
    rows = payload.get("rows") or []
    eligible = [r for r in rows if r.get("eligible")]
    if not eligible:
        feasible = [r for r in rows if r.get("positiveRatioPrefilterPass")]
        if feasible:
            feasible.sort(
                key=lambda r: float((r.get("vegas") or {}).get("cup_relative_brier_edge") or -1e9),
                reverse=True,
            )
            return feasible[:3], "feasible_prefilter_fallback"
        top_rows = sorted(
            rows,
            key=lambda r: float((r.get("vegas") or {}).get("cup_relative_brier_edge") or -1e9),
            reverse=True,
        )
        if not top_rows:
            raise RuntimeError("Phase 13 cannot build anchors because phase12 rows are missing.")
        return top_rows[:2], "raw_edge_fallback"
    eligible.sort(
        key=lambda r: float((r.get("vegas") or {}).get("cup_relative_brier_edge") or -1e9),
        reverse=True,
    )
    max_anchors = int(os.getenv("PHASE13_MAX_ANCHORS", "6"))
    # Keep the strict-eligible frontier focused so phase13 remains tractable
    # under strict walk-forward evaluation while preserving best candidates.
    return eligible[:max_anchors], "strict_eligible"


def _candidate_grid(base: Dict[str, Any], eligible_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: Set[Tuple[Any, ...]] = set()

    def add(name: str, overrides: Dict[str, Any], source: str, tweak: str) -> None:
        sig = _signature(overrides)
        if sig in seen:
            return
        seen.add(sig)
        rows.append(
            {
                "name": name,
                "overrides": overrides,
                "source": source,
                "tweak": tweak,
            }
        )

    add("baseline", copy.deepcopy(base), "baseline", "none")

    for idx, row in enumerate(eligible_rows, start=1):
        source_name = str(row.get("name"))
        anchor = {
            **copy.deepcopy(base),
            **copy.deepcopy(row.get("overrides") or {}),
        }
        mix = anchor.get("cup_ensemble_weights") or {}
        gb = float(mix.get("gradient_boosting", 0.0))
        nn = float(mix.get("neural_network", 0.0))
        mc = float(mix.get("monte_carlo", 1.0))
        blend = float(anchor.get("cup_market_prior_blend", base.get("cup_market_prior_blend", 0.0)))

        add(f"e{idx:02d}-anchor", copy.deepcopy(anchor), source_name, "anchor")

        # Tweak 1: more stable decayed recency + lower Cup boost.
        tweak1 = copy.deepcopy(anchor)
        tweak1["recency_decay_rate"] = round(_clamp(float(anchor.get("recency_decay_rate", 0.10)) + 0.01, 0.05, 0.16), 3)
        tweak1["cup_winner_boost"] = round(_clamp(float(anchor.get("cup_winner_boost", 1.5)) - 0.15, 1.0, 2.5), 3)
        tweak1["cup_market_prior_blend"] = round(_clamp(blend - 0.10, 0.0, 1.0), 3)
        add(f"e{idx:02d}-stability", tweak1, source_name, "stability")

        # Tweak 2: re-introduce calibration and smooth to reduce downside-tail seasons.
        tweak2 = copy.deepcopy(anchor)
        tweak2["use_cup_calibration"] = True
        tweak2["cup_market_prior_blend"] = round(_clamp(blend - 0.15, 0.0, 1.0), 3)
        tweak2["cup_ensemble_weights"] = _normalized_mix(gb + 0.02, nn + 0.02, max(mc - 0.04, 0.0))
        add(f"e{idx:02d}-calibrated", tweak2, source_name, "calibrated")

        # Tweak 3: no-calibration plus slight MC reduction to diversify signals.
        tweak3 = copy.deepcopy(anchor)
        tweak3["use_cup_calibration"] = False
        tweak3["cup_market_prior_blend"] = round(_clamp(blend - 0.20, 0.0, 1.0), 3)
        tweak3["cup_ensemble_weights"] = _normalized_mix(gb + 0.03, nn + 0.01, max(mc - 0.04, 0.0))
        add(f"e{idx:02d}-diversified", tweak3, source_name, "diversified")

    return rows


def _write_profile_artifact(name: str, base_profile: Dict[str, Any], overrides: Dict[str, Any]) -> str:
    PROFILE_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    profile = copy.deepcopy(base_profile)
    profile.update(overrides)
    profile["profileVersion"] = f"phase13-{name}"
    profile["generatedAt"] = datetime.now(timezone.utc).isoformat()
    path = PROFILE_ARTIFACTS / f"phase13_{name}.json"
    path.write_text(json.dumps(profile, indent=2) + "\n")
    return str(path)


def main() -> int:
    profile = load_active_model_profile()
    base = _base_overrides(profile)
    phase12_anchors, phase12_anchor_mode = _load_phase12_eligible_rows()
    candidates = _candidate_grid(base, phase12_anchors)
    data = load_training_data()
    vegas_bootstrap = int(os.getenv("PHASE13_VEGAS_BOOTSTRAP", "600"))
    high_conf_bootstrap = int(os.getenv("PHASE13_HIGH_CONF_BOOTSTRAP", "3000"))
    stage2_top_n = int(os.getenv("PHASE13_STAGE2_TOP_N", "12"))
    max_stage2_evals = int(os.getenv("PHASE13_MAX_STAGE2_EVALS", "0"))
    short_list_n = int(os.getenv("PHASE13_SHORTLIST_N", "8"))
    max_candidates = int(os.getenv("PHASE13_MAX_CANDIDATES", "0"))

    rows: List[Dict[str, Any]] = []
    if max_candidates > 0:
        candidates = candidates[:max_candidates]
    for cand in candidates:
        print(f"[phase13] vegas eval: {cand['name']}", flush=True)
        vegas = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=cand["overrides"],
            confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
            n_bootstrap=vegas_bootstrap,
        )
        cup = vegas.get("cup", {})
        vegas_obj = {
            "cup_relative_brier_edge": cup.get("relative_brier_edge"),
            "cup_relative_brier_edge_ci_low": cup.get("relative_brier_edge_ci_low"),
            "cup_relative_brier_edge_ci_high": cup.get("relative_brier_edge_ci_high"),
            "cup_model_brier": cup.get("model_brier"),
            "cup_vegas_brier": cup.get("vegas_brier"),
            "cup_positive_season_ratio": cup.get("positive_season_ratio"),
            "cup_positive_seasons": cup.get("positive_seasons"),
            "cup_total_seasons": cup.get("total_seasons"),
        }
        rows.append(
            {
                "name": cand["name"],
                "source": cand.get("source"),
                "tweak": cand.get("tweak"),
                "overrides": cand["overrides"],
                "vegas": vegas_obj,
                "goalDistance": _goal_distance(vegas_obj),
                "positiveRatioPrefilterPass": _passes_positive_ratio_prefilter(vegas_obj),
                "core": None,
                "hardGatesPass": None,
                "strictNonRegression": None,
                "eligible": False,
                "highConfidenceVegas": None,
            }
        )

    rows.sort(key=_edge, reverse=True)
    baseline = next(r for r in rows if r["name"] == "baseline")
    baseline_edge = _edge(baseline)

    stage2_names = {"baseline"}
    feasible_rows = [r for r in rows if r.get("positiveRatioPrefilterPass")]
    stage2_names.update(r["name"] for r in feasible_rows[:stage2_top_n])
    stage2_names.update(r["name"] for r in feasible_rows if _edge(r) > baseline_edge + 1e-9)
    adaptive_frontier_active = False
    if len(stage2_names) == 1:
        adaptive_frontier_active = True
        # If hard feasibility is empty, still evaluate a compact frontier to avoid blind spots.
        for pool in (
            sorted(rows, key=_edge, reverse=True)[:6],
            sorted(rows, key=_ratio, reverse=True)[:6],
            sorted(rows, key=lambda r: float((r.get("goalDistance") or {}).get("totalGap", 1e9)))[:6],
        ):
            stage2_names.update(r["name"] for r in pool)

    baseline_core: Optional[Dict[str, float]] = None
    stage2_eval_count = 0
    for row in rows:
        if row["name"] not in stage2_names:
            continue
        if (
            row["name"] != "baseline"
            and not bool(row.get("positiveRatioPrefilterPass"))
            and not adaptive_frontier_active
        ):
            continue
        if max_stage2_evals > 0 and row["name"] != "baseline" and stage2_eval_count >= max_stage2_evals:
            continue
        print(f"[phase13] core eval: {row['name']}", flush=True)
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
        raise RuntimeError("phase13 baseline core metrics missing")

    for row in rows:
        if row.get("core") is None:
            continue
        row["hardGatesPass"] = _hard_gates_pass(row["core"])
        row["strictNonRegression"] = _strict_non_reg(baseline_core, row["core"])
        row["eligible"] = bool(
            row["hardGatesPass"]
            and row["strictNonRegression"]
            and bool(row.get("positiveRatioPrefilterPass"))
            and (_edge(row) > baseline_edge + 1e-9)
        )

    short_names = {r["name"] for r in rows[:short_list_n] if r.get("positiveRatioPrefilterPass")}
    short_names.update(r["name"] for r in rows if r.get("eligible"))
    short_names.add("baseline")
    if short_names == {"baseline"}:
        # Preserve confidence recalculation on the evaluated frontier when strict prefilter is empty.
        frontier = [r for r in rows if r.get("core") is not None]
        frontier.sort(key=lambda r: float((r.get("goalDistance") or {}).get("totalGap", 1e9)))
        short_names.update(r["name"] for r in frontier[:6])

    for row in rows:
        if row["name"] not in short_names:
            continue
        print(f"[phase13] hi-conf eval: {row['name']}", flush=True)
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
            "cup_positive_seasons": cup.get("positive_seasons"),
            "cup_total_seasons": cup.get("total_seasons"),
        }
        row["highConfidenceVegas"] = hi
        row["goalDistance"] = _goal_distance(hi)
        row["positiveRatioPrefilterPass"] = _passes_positive_ratio_prefilter(hi)

    def _goal_gap(row: Dict[str, Any]) -> float:
        return float((row.get("goalDistance") or {}).get("totalGap", 1e9))

    closest_goal = sorted(rows, key=_goal_gap)[0] if rows else None
    feasible_pool = [r for r in rows if r.get("positiveRatioPrefilterPass")]
    eligible_pool = [r for r in rows if r.get("eligible")]
    undeniable_pool = [r for r in rows if (r.get("goalDistance") or {}).get("undeniable")]
    best_raw = rows[0] if rows else None
    best_eligible = eligible_pool[0] if eligible_pool else None
    best_feasible = sorted(feasible_pool, key=_goal_gap)[0] if feasible_pool else None

    artifacts = {"baseline": _write_profile_artifact("baseline_reference", profile, baseline["overrides"])}
    if best_raw:
        artifacts["bestRawEdge"] = _write_profile_artifact("best_raw_edge", profile, best_raw["overrides"])
    if best_eligible:
        artifacts["bestEligible"] = _write_profile_artifact("best_eligible", profile, best_eligible["overrides"])
    if closest_goal:
        artifacts["closestGoal"] = _write_profile_artifact("closest_goal", profile, closest_goal["overrides"])

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase13_eligible_feature_push",
        "phase12AnchorMode": phase12_anchor_mode,
        "summary": {
            "inputStrictEligibleFromPhase12": len(phase12_anchors),
            "totalCandidates": len(rows),
            "coreEvaluatedCandidates": len([r for r in rows if r.get("core") is not None]),
            "highConfidenceEvaluatedCandidates": len([r for r in rows if r.get("highConfidenceVegas") is not None]),
            "positiveRatioPrefilterPassCount": len(feasible_pool),
            "adaptiveFrontierEvaluated": adaptive_frontier_active,
            "baselineEdge": baseline_edge,
            "bestRawEdgeName": best_raw["name"] if best_raw else None,
            "bestRawEdge": _edge(best_raw) if best_raw else None,
            "bestEligibleName": best_eligible["name"] if best_eligible else None,
            "bestEligibleEdge": _edge(best_eligible) if best_eligible else None,
            "closestGoalName": closest_goal["name"] if closest_goal else None,
            "closestGoalDistance": closest_goal.get("goalDistance") if closest_goal else None,
            "closestFeasibleName": best_feasible["name"] if best_feasible else None,
            "closestFeasibleDistance": best_feasible.get("goalDistance") if best_feasible else None,
            "eligibleCount": len(eligible_pool),
            "undeniableCount": len(undeniable_pool),
            "deployRecommendation": (
                "CANDIDATE_READY_FOR_PROMOTION_REVIEW"
                if undeniable_pool
                else "CONTINUE_AB_TRACK"
                if eligible_pool
                else "BLOCKED_BY_POSITIVE_RATIO_FLOOR_FRONTIER_EVALUATED"
                if adaptive_frontier_active
                else "BLOCKED_BY_POSITIVE_RATIO_FLOOR"
            ),
            "hardPositiveRatioPrefilterActive": True,
            "autoDeploy": False,
        },
        "rows": rows,
        "baseline": baseline,
        "bestRawEdge": best_raw,
        "bestEligible": best_eligible,
        "closestGoal": closest_goal,
        "closestFeasible": best_feasible,
        "profileArtifacts": artifacts,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 13 Eligible Feature Push",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        f"- Input strict-eligible (Phase 12): `{report['summary']['inputStrictEligibleFromPhase12']}`",
        f"- Phase 12 anchor mode: `{report['phase12AnchorMode']}`",
        f"- Total candidates: `{report['summary']['totalCandidates']}`",
        f"- Core evaluated: `{report['summary']['coreEvaluatedCandidates']}`",
        f"- High-confidence checked: `{report['summary']['highConfidenceEvaluatedCandidates']}`",
        f"- Positive-ratio prefilter pass: `{report['summary']['positiveRatioPrefilterPassCount']}`",
        f"- Adaptive frontier fallback: `{report['summary']['adaptiveFrontierEvaluated']}`",
        f"- Best raw edge: `{report['summary']['bestRawEdgeName']}` ({report['summary']['bestRawEdge']})",
        f"- Best eligible: `{report['summary']['bestEligibleName']}` ({report['summary']['bestEligibleEdge']})",
        f"- Closest-to-goal: `{report['summary']['closestGoalName']}`",
        f"- Closest feasible: `{report['summary']['closestFeasibleName']}`",
        f"- Undeniable candidates: `{report['summary']['undeniableCount']}`",
        f"- Recommendation: `{report['summary']['deployRecommendation']}`",
        "",
        "## Candidate Board",
        "",
        "| Candidate | Source | Tweak | Edge | CI Low | Pos Ratio | Prefilter | Goal Gap | Top1 | Top5 | F1 | Avg Rank | Hard Gates | Strict Non-Reg | Eligible |",
        "|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|---|",
    ]

    for row in rows:
        vegas = row.get("highConfidenceVegas") or row.get("vegas") or {}
        core = row.get("core")
        gd = row.get("goalDistance") or {}
        edge = vegas.get("cup_relative_brier_edge")
        ci_low = vegas.get("cup_relative_brier_edge_ci_low")
        ratio = vegas.get("cup_positive_season_ratio")
        edge_txt = "N/A" if edge is None else f"{float(edge):.4f}"
        ci_txt = "N/A" if ci_low is None else f"{float(ci_low):.4f}"
        ratio_txt = "N/A" if ratio is None else f"{float(ratio):.3f}"
        gap_txt = "N/A" if gd.get("totalGap") is None else f"{float(gd['totalGap']):.4f}"
        top1 = "N/A" if core is None else f"{core['top1_accuracy_pct']:.1f}"
        top5 = "N/A" if core is None else f"{core['top5_accuracy_pct']:.1f}"
        f1 = "N/A" if core is None else f"{core['playoff_f1']:.3f}"
        rank = "N/A" if core is None else f"{core['average_winner_rank']:.2f}"
        lines.append(
            f"| {row['name']} | {row.get('source')} | {row.get('tweak')} | "
            f"{edge_txt} | {ci_txt} | {ratio_txt} | {row.get('positiveRatioPrefilterPass')} | {gap_txt} | "
            f"{top1} | {top5} | {f1} | {rank} | "
            f"{row.get('hardGatesPass')} | {row.get('strictNonRegression')} | {row.get('eligible')} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
