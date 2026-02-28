#!/usr/bin/env python3
"""
Phase 17: downside-stability feature lane for positive-season resilience.

Focuses on improving season-level downside behavior (min/p10 season edge,
negative-season ratio, positive-season ratio) while preserving strict core
gates and keeping Cup-vs-Vegas edge near or above the current champion.
"""

from __future__ import annotations

import copy
import json
import math
import os
import random
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.evaluation_contract import CUP_VEGAS_EDGE_GOAL, DELTA_GUARDRAILS, HARD_GATES
from superhuman.model_profile import DEFAULT_PROFILE_PATH, load_active_model_profile
from superhuman.validation import generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge


OUT_JSON = PROJECT_ROOT / "reports" / "phase17_downside_stability_lane.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE17_DOWNSIDE_STABILITY_LANE.md"
PHASE16_PATH = PROJECT_ROOT / "reports" / "phase16_adaptive_learning_loop.json"

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
np.seterr(all="ignore")

RNG_SEED = int(os.getenv("PHASE17_RANDOM_SEED", "42"))
EPS = 1e-9


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


def _normalize_mix(raw: Optional[Dict[str, Any]]) -> Dict[str, float]:
    defaults = {"gradient_boosting": 0.30, "neural_network": 0.30, "monte_carlo": 0.40}
    mix = defaults.copy()
    if isinstance(raw, dict):
        for key in defaults:
            if key in raw:
                try:
                    mix[key] = max(0.0, float(raw[key]))
                except (TypeError, ValueError):
                    pass
    total = sum(mix.values())
    if total <= 0:
        return defaults
    return {k: v / total for k, v in mix.items()}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


def _canonical_overrides(overrides: Dict[str, Any]) -> Dict[str, Any]:
    mix = _normalize_mix(overrides.get("cup_ensemble_weights"))
    return {
        "use_neural_network": bool(overrides.get("use_neural_network", True)),
        "use_recency_weighting": bool(overrides.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(overrides.get("use_cup_calibration", True)),
        "recency_decay_rate": round(_clamp(overrides.get("recency_decay_rate", 0.15), 0.05, 0.30), 4),
        "cup_winner_boost": round(_clamp(overrides.get("cup_winner_boost", 2.0), 1.0, 3.0), 4),
        "cup_market_prior_blend": round(_clamp(overrides.get("cup_market_prior_blend", 0.0), 0.0, 1.0), 4),
        "cup_ensemble_weights": {
            "gradient_boosting": round(mix["gradient_boosting"], 4),
            "neural_network": round(mix["neural_network"], 4),
            "monte_carlo": round(mix["monte_carlo"], 4),
        },
        "monte_carlo_simulations": int(max(500, int(overrides.get("monte_carlo_simulations", 2000)))),
        "strict_verification": True,
        "require_series_data_in_strict_mode": True,
        "require_oof_cup_calibration_in_strict_mode": True,
    }


def _signature(overrides: Dict[str, Any]) -> Tuple[Any, ...]:
    mix = _normalize_mix(overrides.get("cup_ensemble_weights"))
    return (
        bool(overrides.get("use_cup_calibration", True)),
        bool(overrides.get("use_neural_network", True)),
        round(float(overrides.get("recency_decay_rate", 0.15)), 4),
        round(float(overrides.get("cup_winner_boost", 2.0)), 4),
        round(float(overrides.get("cup_market_prior_blend", 0.0)), 4),
        round(float(mix["gradient_boosting"]), 4),
        round(float(mix["neural_network"]), 4),
        round(float(mix["monte_carlo"]), 4),
    )


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


def _goal_tier_target() -> float:
    return float(
        CUP_VEGAS_EDGE_GOAL.get(
            "relative_brier_improvement_strong",
            CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_stretch"],
        )
    )


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _load_phase16_anchor_rows() -> List[Dict[str, Any]]:
    payload = _read_json(PHASE16_PATH)
    if not payload:
        return []
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return []
    valid: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if not isinstance(row.get("overrides"), dict):
            continue
        valid.append(row)
    return valid


def _extract_stability_metrics(vegas_diag: Dict[str, Any]) -> Dict[str, Any]:
    cup = vegas_diag.get("cup", {}) if isinstance(vegas_diag, dict) else {}
    season_edges = cup.get("season_edges") or []
    values = []
    for row in season_edges:
        if not isinstance(row, dict):
            continue
        val = row.get("relative_brier_edge")
        if isinstance(val, (int, float)) and math.isfinite(float(val)):
            values.append(float(val))

    if values:
        min_edge = float(np.min(values))
        p10_edge = float(np.percentile(values, 10))
        median_edge = float(np.median(values))
        negative_count = int(sum(1 for v in values if v < 0))
        total = int(len(values))
    else:
        min_edge = -1.0
        p10_edge = -1.0
        median_edge = -1.0
        negative_count = 0
        total = 0

    positive_ratio = cup.get("positive_season_ratio")
    if not isinstance(positive_ratio, (int, float)):
        positive_ratio = 0.0

    return {
        "minSeasonEdge": min_edge,
        "p10SeasonEdge": p10_edge,
        "medianSeasonEdge": median_edge,
        "negativeSeasonCount": negative_count,
        "totalSeasonCount": total,
        "negativeSeasonRatio": (negative_count / total) if total > 0 else 0.0,
        "downsidePenalty": max(0.0, -min_edge),
        "positiveSeasonRatio": float(positive_ratio),
    }


def _extract_vegas(vegas_diag: Dict[str, Any]) -> Dict[str, Any]:
    cup = vegas_diag.get("cup", {})
    return {
        "cup_relative_brier_edge": cup.get("relative_brier_edge"),
        "cup_relative_brier_edge_ci_low": cup.get("relative_brier_edge_ci_low"),
        "cup_relative_brier_edge_ci_high": cup.get("relative_brier_edge_ci_high"),
        "cup_model_brier": cup.get("model_brier"),
        "cup_vegas_brier": cup.get("vegas_brier"),
        "cup_positive_season_ratio": cup.get("positive_season_ratio"),
        "cup_positive_seasons": cup.get("positive_seasons"),
        "cup_total_seasons": cup.get("total_seasons"),
    }


def _edge(row: Dict[str, Any]) -> float:
    edge = row.get("vegas", {}).get("cup_relative_brier_edge")
    if edge is None:
        return -1e9
    return float(edge)


def _downside_score(row: Dict[str, Any], target_edge: float) -> float:
    edge = _edge(row)
    stability = row.get("stability") or {}
    min_edge = float(stability.get("minSeasonEdge", -1.0))
    p10_edge = float(stability.get("p10SeasonEdge", -1.0))
    pos_ratio = float(stability.get("positiveSeasonRatio", 0.0))
    downside_penalty = float(stability.get("downsidePenalty", 1.0))
    target_gap = max(target_edge - edge, 0.0)
    return edge - (0.35 * target_gap) - (0.20 * downside_penalty) + (0.08 * pos_ratio) + (0.06 * p10_edge) + (0.04 * min_edge)


def _mix_mutation(base_mix: Dict[str, float], rng: random.Random, drift: float = 0.03) -> Dict[str, float]:
    gb = _clamp(base_mix["gradient_boosting"] + rng.uniform(-drift, drift), 0.0, 1.0)
    nn = _clamp(base_mix["neural_network"] + rng.uniform(-drift, drift), 0.0, 1.0)
    mc = _clamp(base_mix["monte_carlo"] + rng.uniform(-drift, drift), 0.0, 1.0)
    return _normalize_mix({"gradient_boosting": gb, "neural_network": nn, "monte_carlo": mc})


def _candidate_pool(base: Dict[str, Any], budget: int) -> List[Dict[str, Any]]:
    rng = random.Random(RNG_SEED)
    phase16_rows = _load_phase16_anchor_rows()
    seen: set[Tuple[Any, ...]] = set()
    rows: List[Dict[str, Any]] = []

    def add(name: str, overrides: Dict[str, Any], source: str, strategy: str) -> None:
        canonical = _canonical_overrides(overrides)
        sig = _signature(canonical)
        if sig in seen:
            return
        seen.add(sig)
        rows.append({"name": name, "source": source, "strategy": strategy, "overrides": canonical})

    add("baseline", copy.deepcopy(base), "active_profile", "baseline")

    anchor_rows = sorted(
        phase16_rows,
        key=lambda row: float((row.get("vegas") or {}).get("cup_relative_brier_edge") or -1e9),
        reverse=True,
    )[:4]
    if not anchor_rows:
        anchor_rows = [{"name": "baseline", "overrides": base}]

    for idx, row in enumerate(anchor_rows, start=1):
        source_name = str(row.get("name", f"anchor{idx}"))
        anchor = _canonical_overrides({**copy.deepcopy(base), **copy.deepcopy(row.get("overrides") or {})})
        mix = _normalize_mix(anchor.get("cup_ensemble_weights"))

        add(f"anchor-{idx:02d}", anchor, source_name, "anchor")

        stability = copy.deepcopy(anchor)
        stability["use_cup_calibration"] = True
        stability["cup_winner_boost"] = round(_clamp(stability["cup_winner_boost"] - 0.20, 1.0, 3.0), 4)
        stability["cup_market_prior_blend"] = round(_clamp(stability["cup_market_prior_blend"] + 0.06, 0.0, 1.0), 4)
        stability["recency_decay_rate"] = round(_clamp(stability["recency_decay_rate"] + 0.01, 0.05, 0.30), 4)
        add(f"anchor-{idx:02d}-stability", stability, source_name, "stability")

        downside = copy.deepcopy(anchor)
        downside["use_cup_calibration"] = True
        downside["cup_market_prior_blend"] = round(_clamp(downside["cup_market_prior_blend"] + 0.10, 0.0, 1.0), 4)
        downside["cup_ensemble_weights"] = _normalize_mix(
            {
                "gradient_boosting": max(0.0, mix["gradient_boosting"] - 0.02),
                "neural_network": max(0.0, mix["neural_network"] - 0.02),
                "monte_carlo": min(1.0, mix["monte_carlo"] + 0.04),
            }
        )
        add(f"anchor-{idx:02d}-downside-shield", downside, source_name, "downside_shield")

        diversified = copy.deepcopy(anchor)
        diversified["recency_decay_rate"] = round(_clamp(diversified["recency_decay_rate"] - 0.01, 0.05, 0.30), 4)
        diversified["cup_ensemble_weights"] = _mix_mutation(mix, rng, drift=0.05)
        add(f"anchor-{idx:02d}-diversified", diversified, source_name, "diversified")

    anchors = [row["overrides"] for row in rows]
    max_attempts = max(60, budget * 12)
    attempts = 0
    while len(rows) < budget and attempts < max_attempts:
        attempts += 1
        base_pick = copy.deepcopy(rng.choice(anchors))
        mix = _normalize_mix(base_pick.get("cup_ensemble_weights"))
        candidate = {
            **base_pick,
            "use_cup_calibration": True if rng.random() < 0.70 else bool(base_pick.get("use_cup_calibration", True)),
            "recency_decay_rate": round(_clamp(base_pick["recency_decay_rate"] + rng.uniform(-0.02, 0.02), 0.05, 0.30), 4),
            "cup_winner_boost": round(_clamp(base_pick["cup_winner_boost"] + rng.uniform(-0.20, 0.10), 1.0, 3.0), 4),
            "cup_market_prior_blend": round(_clamp(base_pick["cup_market_prior_blend"] + rng.uniform(-0.03, 0.12), 0.0, 1.0), 4),
            "cup_ensemble_weights": _mix_mutation(mix, rng, drift=0.04),
        }
        add(f"explore-{len(rows):02d}", candidate, "randomized", "explore")

    return rows


def _build_blockers(
    baseline: Dict[str, Any],
    best: Optional[Dict[str, Any]],
    eligible_count: int,
    target_edge: float,
) -> List[str]:
    blockers: List[str] = []
    if eligible_count == 0:
        blockers.append("No candidate satisfied strict core + downside stability eligibility.")
    if best is None:
        blockers.append("No candidate produced valid Vegas diagnostics.")
        return blockers
    if _edge(best) < target_edge - EPS:
        blockers.append(f"Best downside-stability candidate edge is {_edge(best):.4f}; strong-tier target is {target_edge:.4f}.")
    base_min = float((baseline.get("stability") or {}).get("minSeasonEdge", -1.0))
    cand_min = float((best.get("stability") or {}).get("minSeasonEdge", -1.0))
    if cand_min < base_min - EPS:
        blockers.append("Downside floor regressed (min season edge worsened vs baseline).")
    return blockers


def _next_actions(best: Optional[Dict[str, Any]], blockers: List[str], target_edge: float) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []
    if best:
        gap = max(target_edge - _edge(best), 0.0)
        actions.append(
            {
                "owner": "Model Lead",
                "priority": "P0",
                "action": f"Combine phase16 champion with phase17 downside shielding and close remaining strong-tier gap ({gap:.4f}).",
            }
        )
    if blockers:
        actions.append(
            {
                "owner": "Quant Skeptic",
                "priority": "P1",
                "action": f"Root-cause top blocker: {blockers[0]}",
            }
        )
    actions.append(
        {
            "owner": "Release Sheriff",
            "priority": "P1",
            "action": "Keep promotion blocked unless strong-tier target and strict release cycle both pass in the same execution context.",
        }
    )
    return actions[:4]


def main() -> int:
    target_edge = _goal_tier_target()
    profile = load_active_model_profile()
    base = _canonical_overrides(_base_overrides(profile))

    budget = int(os.getenv("PHASE17_CANDIDATE_BUDGET", "18"))
    stage2_limit = int(os.getenv("PHASE17_STAGE2_EVALS", "4"))
    vegas_bootstrap = int(os.getenv("PHASE17_VEGAS_BOOTSTRAP", "280"))
    high_conf_bootstrap = int(os.getenv("PHASE17_HIGH_CONF_BOOTSTRAP", "1000"))
    shortlist_n = int(os.getenv("PHASE17_SHORTLIST_N", "3"))
    min_positive_ratio = float(os.getenv("PHASE17_MIN_POSITIVE_RATIO", str(max(float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"]), 0.8))))
    min_season_edge_floor = float(os.getenv("PHASE17_MIN_SEASON_EDGE_FLOOR", "-0.030"))
    max_negative_ratio = float(os.getenv("PHASE17_MAX_NEGATIVE_SEASON_RATIO", "0.35"))
    max_edge_drop_vs_baseline = float(os.getenv("PHASE17_MAX_EDGE_DROP_VS_BASELINE", "0.001"))

    candidates = _candidate_pool(base, budget=max(6, budget))
    data = load_training_data(allow_synthetic_fallback=False)

    rows: List[Dict[str, Any]] = []
    for cand in candidates:
        print(f"[phase17] vegas eval: {cand['name']}", flush=True)
        vegas_diag = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=cand["overrides"],
            confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
            n_bootstrap=vegas_bootstrap,
        )
        vegas = _extract_vegas(vegas_diag)
        stability = _extract_stability_metrics(vegas_diag)
        rows.append(
            {
                "name": cand["name"],
                "source": cand["source"],
                "strategy": cand["strategy"],
                "overrides": cand["overrides"],
                "vegas": vegas,
                "stability": stability,
                "core": None,
                "hardGatesPass": None,
                "strictNonRegression": None,
                "positiveRatioPrefilterPass": bool(stability["positiveSeasonRatio"] >= min_positive_ratio),
                "downsidePrefilterPass": bool(
                    stability["minSeasonEdge"] >= min_season_edge_floor
                    and stability["negativeSeasonRatio"] <= max_negative_ratio
                ),
                "edgeNonRegressionPass": None,
                "eligible": False,
                "downsideScore": None,
                "highConfidenceVegas": None,
            }
        )

    baseline = next((row for row in rows if row["name"] == "baseline"), None)
    if baseline is None:
        raise RuntimeError("Phase17 baseline row missing.")

    baseline_edge = _edge(baseline)
    baseline["downsideScore"] = _downside_score(baseline, target_edge)

    stage1_ranked = sorted(rows, key=lambda row: _downside_score(row, target_edge), reverse=True)
    stage2_names = {"baseline"}
    for row in stage1_ranked:
        if row["name"] == "baseline":
            continue
        if len(stage2_names) - 1 >= stage2_limit:
            break
        if not row.get("positiveRatioPrefilterPass"):
            continue
        stage2_names.add(row["name"])

    baseline_core: Optional[Dict[str, float]] = None
    for row in rows:
        row["downsideScore"] = _downside_score(row, target_edge)
        if row["name"] not in stage2_names:
            continue
        print(f"[phase17] core eval: {row['name']}", flush=True)
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
        raise RuntimeError("Phase17 baseline core metrics missing.")

    for row in rows:
        if row.get("core") is None:
            continue
        row["hardGatesPass"] = _hard_gates_pass(row["core"])
        row["strictNonRegression"] = _strict_non_reg(baseline_core, row["core"])
        row["edgeNonRegressionPass"] = bool(_edge(row) >= baseline_edge - max_edge_drop_vs_baseline - EPS)
        row["eligible"] = bool(
            row["hardGatesPass"]
            and row["strictNonRegression"]
            and row["positiveRatioPrefilterPass"]
            and row["downsidePrefilterPass"]
            and row["edgeNonRegressionPass"]
        )

    shortlist = [row for row in rows if row.get("core") is not None]
    shortlist.sort(key=lambda row: float(row.get("downsideScore") or -1e9), reverse=True)
    for row in shortlist[: max(1, shortlist_n)]:
        print(f"[phase17] high-conf vegas eval: {row['name']}", flush=True)
        vegas_diag = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=row["overrides"],
            confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
            n_bootstrap=high_conf_bootstrap,
        )
        cup = vegas_diag.get("cup", {})
        row["highConfidenceVegas"] = {
            "cup_relative_brier_edge": cup.get("relative_brier_edge"),
            "cup_relative_brier_edge_ci_low": cup.get("relative_brier_edge_ci_low"),
            "cup_relative_brier_edge_ci_high": cup.get("relative_brier_edge_ci_high"),
            "cup_positive_season_ratio": cup.get("positive_season_ratio"),
            "cup_positive_seasons": cup.get("positive_seasons"),
            "cup_total_seasons": cup.get("total_seasons"),
        }

    eligible_rows = [row for row in rows if row.get("eligible")]
    best = (
        sorted(eligible_rows, key=lambda row: float(row.get("downsideScore") or -1e9), reverse=True)[0]
        if eligible_rows
        else None
    )
    best_raw = sorted(rows, key=lambda row: float(row.get("downsideScore") or -1e9), reverse=True)[0] if rows else None

    blockers = _build_blockers(
        baseline=baseline,
        best=best or best_raw,
        eligible_count=len(eligible_rows),
        target_edge=target_edge,
    )

    baseline_min = float((baseline.get("stability") or {}).get("minSeasonEdge", -1.0))
    baseline_ratio = float((baseline.get("stability") or {}).get("positiveSeasonRatio", 0.0))
    best_min = float(((best or best_raw or {}).get("stability") or {}).get("minSeasonEdge", -1.0))
    best_ratio = float(((best or best_raw or {}).get("stability") or {}).get("positiveSeasonRatio", 0.0))
    best_edge = _edge(best or best_raw or {"vegas": {}})

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase17_downside_stability_lane",
        "target": {
            "tier": "strong",
            "edge": target_edge,
            "minPositiveSeasonRatio": min_positive_ratio,
            "minSeasonEdgeFloor": min_season_edge_floor,
            "maxNegativeSeasonRatio": max_negative_ratio,
        },
        "summary": {
            "candidateBudget": len(candidates),
            "evaluatedCandidates": len(rows),
            "coreEvaluatedCandidates": len([row for row in rows if row.get("core") is not None]),
            "highConfidenceEvaluatedCandidates": len([row for row in rows if row.get("highConfidenceVegas") is not None]),
            "eligibleCount": len(eligible_rows),
            "baselineEdge": baseline_edge,
            "baselinePositiveSeasonRatio": baseline_ratio,
            "baselineMinSeasonEdge": baseline_min,
            "bestDownsideName": (best or best_raw or {}).get("name"),
            "bestDownsideEdge": best_edge if best_edge > -1e8 else None,
            "bestDownsidePositiveSeasonRatio": best_ratio,
            "bestDownsideMinSeasonEdge": best_min,
            "downsideMinSeasonEdgeDelta": best_min - baseline_min,
            "positiveSeasonRatioDelta": best_ratio - baseline_ratio,
            "edgeDeltaVsBaseline": (best_edge - baseline_edge) if best_edge > -1e8 else None,
            "strongTierGap": max(target_edge - best_edge, 0.0) if best_edge > -1e8 else None,
            "recommendation": "USE_PHASE17_CANDIDATE" if best is not None else "NO_STRICT_STABILITY_WINNER",
            "blockerCount": len(blockers),
        },
        "blockers": blockers,
        "nextActions": _next_actions(best or best_raw, blockers, target_edge),
        "baseline": baseline,
        "bestEligible": best,
        "bestRawByDownsideScore": best_raw,
        "rows": sorted(rows, key=lambda row: float(row.get("downsideScore") or -1e9), reverse=True),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 17 Downside Stability Lane",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"- Candidate budget: `{report['summary']['candidateBudget']}`",
        f"- Evaluated candidates: `{report['summary']['evaluatedCandidates']}`",
        f"- Core evaluated: `{report['summary']['coreEvaluatedCandidates']}`",
        f"- Eligible: `{report['summary']['eligibleCount']}`",
        f"- Baseline edge: `{baseline_edge:.4f}`",
        f"- Baseline min season edge: `{baseline_min:.4f}`",
        f"- Best downside candidate: `{report['summary']['bestDownsideName']}`",
        f"- Best downside edge: `{report['summary']['bestDownsideEdge']}`",
        f"- Min season edge delta: `{report['summary']['downsideMinSeasonEdgeDelta']}`",
        f"- Positive-season-ratio delta: `{report['summary']['positiveSeasonRatioDelta']}`",
        f"- Recommendation: `{report['summary']['recommendation']}`",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        lines.extend([f"- {item}" for item in blockers])
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Candidate Snapshot",
            "",
            "| Candidate | Edge | Positive Ratio | Min Season Edge | Downside Score | Eligible |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in report["rows"][:12]:
        lines.append(
            f"| {row.get('name')} | "
            f"{'N/A' if _edge(row) <= -1e8 else f'{_edge(row):.4f}'} | "
            f"{float((row.get('stability') or {}).get('positiveSeasonRatio', 0.0)):.3f} | "
            f"{float((row.get('stability') or {}).get('minSeasonEdge', -1.0)):.4f} | "
            f"{float(row.get('downsideScore') or -1e9):.4f} | "
            f"{row.get('eligible')} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
