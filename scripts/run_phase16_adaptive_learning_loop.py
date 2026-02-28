#!/usr/bin/env python3
"""
Phase 16: adaptive strong-tier edge loop with bounded meta-learning.

This lane learns from prior phase candidate outcomes, proposes a focused next
batch, and evaluates it under strict non-regression and release safety gates.
By default the objective tier is STRONG (>=3% Cup-vs-Vegas relative Brier edge),
not just release-floor pass.
"""

from __future__ import annotations

import copy
import json
import math
import os
import random
import subprocess
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.evaluation_contract import CUP_VEGAS_EDGE_GOAL, DELTA_GUARDRAILS, HARD_GATES
from superhuman.model_profile import DEFAULT_PROFILE_PATH, load_active_model_profile
from superhuman.validation import generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge


OUT_JSON = PROJECT_ROOT / "reports" / "phase16_adaptive_learning_loop.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE16_ADAPTIVE_LEARNING_LOOP.md"
PHASE11_PATH = PROJECT_ROOT / "reports" / "phase11_constrained_edge_batch.json"
PHASE12_PATH = PROJECT_ROOT / "reports" / "phase12_goal_gap_closure.json"
PHASE13_PATH = PROJECT_ROOT / "reports" / "phase13_eligible_feature_push.json"

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
np.seterr(all="ignore")

RNG_SEED = int(os.getenv("PHASE16_RANDOM_SEED", "42"))
EPS = 1e-9

TARGET_TIER_ALIASES = {
    "release": "release_floor",
    "release_floor": "release_floor",
    "floor": "release_floor",
    "strong": "strong",
    "stretch": "stretch",
    "moonshot": "moonshot",
}

STRICT_RELEASE_PATH = PROJECT_ROOT / "reports" / "phase7_release_cycle_strict.json"
DEFAULT_STRICT_GATE_TIMEOUT_SECONDS = 1800
MIN_STRICT_GATE_TIMEOUT_SECONDS = 300
_raw_strict_gate_timeout = int(
    os.getenv("PHASE16_STRICT_GATE_TIMEOUT_SECONDS", str(DEFAULT_STRICT_GATE_TIMEOUT_SECONDS))
)
STRICT_GATE_TIMEOUT_SECONDS = max(MIN_STRICT_GATE_TIMEOUT_SECONDS, _raw_strict_gate_timeout)


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


def _feature_vector(overrides: Dict[str, Any]) -> List[float]:
    mix = _normalize_mix(overrides.get("cup_ensemble_weights"))
    return [
        1.0 if bool(overrides.get("use_cup_calibration", True)) else 0.0,
        1.0 if bool(overrides.get("use_neural_network", True)) else 0.0,
        float(overrides.get("recency_decay_rate", 0.15)),
        float(overrides.get("cup_winner_boost", 2.0)),
        float(overrides.get("cup_market_prior_blend", 0.0)),
        float(mix["gradient_boosting"]),
        float(mix["neural_network"]),
        float(mix["monte_carlo"]),
    ]


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


def _target_tier() -> str:
    raw = str(os.getenv("PHASE16_TARGET_TIER", "strong")).strip().lower()
    return TARGET_TIER_ALIASES.get(raw, "strong")


def _target_edge_for_tier(tier: str) -> float:
    if tier == "moonshot":
        return float(CUP_VEGAS_EDGE_GOAL.get("relative_brier_improvement_moonshot", CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_stretch"]))
    if tier == "stretch":
        return float(CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_stretch"])
    if tier == "strong":
        return float(CUP_VEGAS_EDGE_GOAL.get("relative_brier_improvement_strong", CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_stretch"]))
    return float(CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_min"])


def _goal_distance(edge: Optional[float], target_edge: float) -> float:
    if edge is None:
        return 1.0
    return max(target_edge - float(edge), 0.0)


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _as_float(value: Any) -> Optional[float]:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def _build_learning_rows(path: Path, phase: str) -> List[Dict[str, Any]]:
    payload = _read_json(path)
    if not payload:
        return []
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return []

    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        overrides = row.get("overrides")
        if not isinstance(overrides, dict):
            continue
        vegas = row.get("vegas") or {}
        edge = _as_float(vegas.get("cup_relative_brier_edge"))
        if edge is None:
            continue
        core = row.get("core") if isinstance(row.get("core"), dict) else None
        hard_gates = row.get("hardGatesPass")
        non_reg = row.get("strictNonRegression")
        if core and hard_gates is None:
            hard_gates = _hard_gates_pass(core)
        if core and non_reg is None:
            non_reg = True
        positive_prefilter = row.get("positiveRatioPrefilterPass")
        if positive_prefilter is None:
            positive_prefilter = _passes_positive_ratio_prefilter(
                {
                    "cup_positive_season_ratio": vegas.get("cup_positive_season_ratio"),
                    "cup_positive_seasons": vegas.get("cup_positive_seasons"),
                    "cup_total_seasons": vegas.get("cup_total_seasons"),
                }
            )
        eligible = bool(hard_gates and non_reg and positive_prefilter)
        out.append(
            {
                "phase": phase,
                "name": row.get("name"),
                "overrides": _canonical_overrides(overrides),
                "edge": edge,
                "eligible": eligible,
            }
        )
    return out


def _fit_meta_models(learning_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not learning_rows:
        return {
            "edgeModel": None,
            "feasibleModel": None,
            "mode": "heuristic",
            "edgeSampleCount": 0,
            "feasibleSampleCount": 0,
        }

    X = np.array([_feature_vector(row["overrides"]) for row in learning_rows], dtype=float)
    y_edge = np.array([float(row["edge"]) for row in learning_rows], dtype=float)

    edge_model = None
    mode = "heuristic"
    if len(learning_rows) >= 8 and float(np.std(y_edge)) > 1e-6:
        edge_model = RandomForestRegressor(
            n_estimators=220,
            max_depth=6,
            min_samples_leaf=2,
            random_state=RNG_SEED,
        )
        edge_model.fit(X, y_edge)
        mode = "meta_model"

    feasible_labels = [1 if bool(row.get("eligible")) else 0 for row in learning_rows]
    feasible_model = None
    if len(learning_rows) >= 12 and len(set(feasible_labels)) > 1:
        feasible_model = LogisticRegression(max_iter=500, random_state=RNG_SEED)
        feasible_model.fit(X, np.array(feasible_labels, dtype=int))

    return {
        "edgeModel": edge_model,
        "feasibleModel": feasible_model,
        "mode": mode,
        "edgeSampleCount": len(learning_rows),
        "feasibleSampleCount": len(learning_rows) if feasible_model else 0,
    }


def _heuristic_edge_prediction(
    candidate: Dict[str, Any],
    learning_rows: Sequence[Dict[str, Any]],
    fallback: float,
) -> float:
    if not learning_rows:
        return float(fallback)
    x = np.array(_feature_vector(candidate), dtype=float)
    weighted_edges: List[Tuple[float, float]] = []
    for row in learning_rows:
        r = np.array(_feature_vector(row["overrides"]), dtype=float)
        dist = float(np.linalg.norm(x - r))
        weight = 1.0 / (dist + 0.05)
        weighted_edges.append((weight, float(row["edge"])))
    weighted_edges.sort(key=lambda t: t[0], reverse=True)
    top = weighted_edges[: min(8, len(weighted_edges))]
    total_w = sum(w for w, _ in top)
    if total_w <= 0:
        return float(fallback)
    return float(sum(w * e for w, e in top) / total_w)


def _predict_candidate(
    overrides: Dict[str, Any],
    meta: Dict[str, Any],
    learning_rows: Sequence[Dict[str, Any]],
    baseline_edge: float,
    baseline_overrides: Dict[str, Any],
    target_edge: float,
) -> Dict[str, float]:
    x = np.array([_feature_vector(overrides)], dtype=float)
    edge_model = meta.get("edgeModel")
    feasible_model = meta.get("feasibleModel")
    if edge_model is not None:
        predicted_edge = float(edge_model.predict(x)[0])
    else:
        predicted_edge = _heuristic_edge_prediction(overrides, learning_rows, fallback=baseline_edge)

    if feasible_model is not None:
        predicted_feasible = float(feasible_model.predict_proba(x)[0][1])
    else:
        # Heuristic: down-weight candidates that move too far away from baseline profile.
        baseline_x = np.array(_feature_vector(baseline_overrides), dtype=float)
        dist = float(np.linalg.norm(x[0] - baseline_x))
        predicted_feasible = float(_clamp(1.0 - dist, 0.15, 0.9))

    target_gap = max(target_edge - predicted_edge, 0.0)
    score = predicted_edge - (0.35 * target_gap) + (0.01 * predicted_feasible)
    return {
        "predictedEdge": predicted_edge,
        "predictedFeasibleProb": predicted_feasible,
        "predictedScore": score,
    }


def _mix_mutation(base_mix: Dict[str, float], rng: random.Random, drift: float = 0.04) -> Dict[str, float]:
    gb = _clamp(base_mix["gradient_boosting"] + rng.uniform(-drift, drift), 0.0, 1.0)
    nn = _clamp(base_mix["neural_network"] + rng.uniform(-drift, drift), 0.0, 1.0)
    mc = _clamp(base_mix["monte_carlo"] + rng.uniform(-drift, drift), 0.0, 1.0)
    return _normalize_mix({"gradient_boosting": gb, "neural_network": nn, "monte_carlo": mc})


def _anchor_candidates(
    base: Dict[str, Any],
    learning_rows: Sequence[Dict[str, Any]],
    budget: int,
) -> List[Dict[str, Any]]:
    rng = random.Random(RNG_SEED)
    seen: set[Tuple[Any, ...]] = set()
    pool: List[Dict[str, Any]] = []

    def add(name: str, overrides: Dict[str, Any], source: str, strategy: str) -> None:
        canonical = _canonical_overrides(overrides)
        sig = _signature(canonical)
        if sig in seen:
            return
        seen.add(sig)
        pool.append(
            {
                "name": name,
                "source": source,
                "strategy": strategy,
                "overrides": canonical,
            }
        )

    add("baseline", copy.deepcopy(base), "active_profile", "baseline")

    top_learning = sorted(learning_rows, key=lambda r: float(r.get("edge", -1e9)), reverse=True)[:6]
    for idx, row in enumerate(top_learning, start=1):
        anchor = _canonical_overrides(row["overrides"])
        add(f"anchor-{idx:02d}", anchor, str(row.get("phase", "history")), "anchor")

        stable = copy.deepcopy(anchor)
        stable["recency_decay_rate"] = round(_clamp(stable["recency_decay_rate"] + 0.01, 0.05, 0.30), 4)
        stable["cup_winner_boost"] = round(_clamp(stable["cup_winner_boost"] - 0.12, 1.0, 3.0), 4)
        stable["cup_market_prior_blend"] = round(_clamp(stable["cup_market_prior_blend"] - 0.05, 0.0, 1.0), 4)
        add(f"anchor-{idx:02d}-stability", stable, str(row.get("phase", "history")), "stability")

        diversified = copy.deepcopy(anchor)
        diversified["use_cup_calibration"] = not bool(anchor.get("use_cup_calibration", True))
        diversified["cup_ensemble_weights"] = _mix_mutation(_normalize_mix(anchor.get("cup_ensemble_weights")), rng, drift=0.06)
        add(f"anchor-{idx:02d}-diversified", diversified, str(row.get("phase", "history")), "diversified")

    anchors = [row["overrides"] for row in pool]
    max_attempts = max(60, budget * 15)
    attempts = 0
    while len(pool) < budget and attempts < max_attempts:
        attempts += 1
        base_pick = copy.deepcopy(rng.choice(anchors))
        mix = _normalize_mix(base_pick.get("cup_ensemble_weights"))
        candidate = {
            **base_pick,
            "recency_decay_rate": round(_clamp(base_pick["recency_decay_rate"] + rng.uniform(-0.025, 0.025), 0.05, 0.30), 4),
            "cup_winner_boost": round(_clamp(base_pick["cup_winner_boost"] + rng.uniform(-0.20, 0.20), 1.0, 3.0), 4),
            "cup_market_prior_blend": round(_clamp(base_pick["cup_market_prior_blend"] + rng.uniform(-0.07, 0.07), 0.0, 1.0), 4),
            "cup_ensemble_weights": _mix_mutation(mix, rng, drift=0.05),
            "use_cup_calibration": bool(base_pick.get("use_cup_calibration", True)) if rng.random() > 0.22 else not bool(base_pick.get("use_cup_calibration", True)),
        }
        add(f"explore-{len(pool):02d}", candidate, "randomized", "explore")

    return pool


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


def _target_gap(row: Dict[str, Any], target_edge: float) -> float:
    edge = row.get("vegas", {}).get("cup_relative_brier_edge")
    return _goal_distance(_as_float(edge), target_edge)


def _best_by_target(rows: Iterable[Dict[str, Any]], target_edge: float) -> Optional[Dict[str, Any]]:
    materialized = [row for row in rows]
    if not materialized:
        return None
    return sorted(
        materialized,
        key=lambda row: (_target_gap(row, target_edge), -_edge(row), row.get("name", "")),
    )[0]


def _build_blockers(
    baseline_edge: float,
    target_edge: float,
    best_raw: Optional[Dict[str, Any]],
    best_eligible: Optional[Dict[str, Any]],
    prefilter_pass_count: int,
) -> List[str]:
    blockers: List[str] = []
    if prefilter_pass_count == 0:
        blockers.append("No candidate cleared hard positive-season-ratio prefilter.")
    if best_raw is None:
        blockers.append("No Vegas-evaluable candidate produced a valid Cup edge.")
        return blockers

    best_raw_edge = _edge(best_raw)
    if best_raw_edge < target_edge - EPS:
        blockers.append(
            f"Best raw edge is {best_raw_edge:.4f}; strong-tier target requires {target_edge:.4f}."
        )
    if best_raw_edge <= baseline_edge + EPS:
        blockers.append(
            "No candidate improved Cup edge beyond the active baseline."
        )
    if best_eligible is None:
        blockers.append(
            "No candidate passed strict hard-gate + non-regression eligibility."
        )
    return blockers


def _next_actions(
    blockers: Sequence[str],
    target_tier: str,
    target_edge: float,
    best_raw: Optional[Dict[str, Any]],
    best_eligible: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []
    if best_eligible is None:
        actions.append(
            {
                "owner": "Model Lead",
                "priority": "P0",
                "action": "Run another bounded adaptive cycle; keep strict non-regression and positive-season-ratio floors hard-blocking.",
            }
        )
    else:
        gap = _target_gap(best_eligible, target_edge)
        if gap > 0:
            actions.append(
                {
                    "owner": "Model Lead",
                    "priority": "P0",
                    "action": f"Close remaining {gap:.4f} edge gap to `{target_tier}` target ({target_edge:.4f}).",
                }
            )
        else:
            actions.append(
                {
                    "owner": "Release Sheriff",
                    "priority": "P0",
                    "action": "Candidate meets target tier; run strict release-cycle gate before promotion.",
                }
            )

    if best_raw is not None and best_raw.get("name") != "baseline" and best_eligible is None:
        actions.append(
            {
                "owner": "Research Lead",
                "priority": "P1",
                "action": f"Investigate why `{best_raw.get('name')}` gains edge but fails strict eligibility; capture root cause in the next loop.",
            }
        )

    if blockers:
        actions.append(
            {
                "owner": "Program Lead",
                "priority": "P1",
                "action": "Keep dashboard messaging explicit: model quality and release readiness remain separate until blockers clear.",
            }
        )
    return actions[:4]


def _run_strict_release_gate_for_promotion() -> Dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "run_phase7_release_cycle.py"), "--mode", "strict"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=STRICT_GATE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return {
            "status": "FAIL",
            "returncode": 124,
            "reason": f"strict gate timed out after {STRICT_GATE_TIMEOUT_SECONDS}s",
            "stdout": stdout.strip(),
            "stderr": f"Timed out after {STRICT_GATE_TIMEOUT_SECONDS}s",
            "durationSeconds": round((datetime.now(timezone.utc) - started).total_seconds(), 2),
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "status": "FAIL",
            "returncode": 1,
            "reason": f"strict gate execution failed: {exc}",
            "stdout": "",
            "stderr": str(exc),
            "durationSeconds": round((datetime.now(timezone.utc) - started).total_seconds(), 2),
        }

    strict_payload = _read_json(STRICT_RELEASE_PATH) or {}
    status = str(strict_payload.get("status", "UNKNOWN")).upper() if isinstance(strict_payload, dict) else "UNKNOWN"
    if status not in {"PASS", "FAIL"}:
        status = "PASS" if proc.returncode == 0 else "FAIL"

    return {
        "status": status,
        "returncode": int(proc.returncode),
        "reason": "strict release cycle gate result from same run context",
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
        "durationSeconds": round((datetime.now(timezone.utc) - started).total_seconds(), 2),
    }


def main() -> int:
    target_tier = _target_tier()
    target_edge = _target_edge_for_tier(target_tier)
    profile = load_active_model_profile()
    base = _canonical_overrides(_base_overrides(profile))

    learning_rows: List[Dict[str, Any]] = []
    learning_rows.extend(_build_learning_rows(PHASE11_PATH, "phase11"))
    learning_rows.extend(_build_learning_rows(PHASE12_PATH, "phase12"))
    learning_rows.extend(_build_learning_rows(PHASE13_PATH, "phase13"))

    meta = _fit_meta_models(learning_rows)

    budget = int(os.getenv("PHASE16_CANDIDATE_BUDGET", "24"))
    stage1_top_n = int(os.getenv("PHASE16_STAGE1_TOP_N", "10"))
    max_stage2_evals = int(os.getenv("PHASE16_MAX_STAGE2_EVALS", "5"))
    short_list_n = int(os.getenv("PHASE16_SHORTLIST_N", "4"))
    vegas_bootstrap = int(os.getenv("PHASE16_VEGAS_BOOTSTRAP", "320"))
    high_conf_bootstrap = int(os.getenv("PHASE16_HIGH_CONF_BOOTSTRAP", "1200"))
    auto_deploy = os.getenv("PHASE16_AUTO_DEPLOY", "0") == "1"

    candidate_pool = _anchor_candidates(base, learning_rows, budget=max(6, budget))

    # Use historical top edge as fallback baseline edge for cold-start scoring.
    historical_best = max((float(r["edge"]) for r in learning_rows), default=0.0)
    baseline_prior_edge = historical_best

    scored_candidates: List[Dict[str, Any]] = []
    for cand in candidate_pool:
        pred = _predict_candidate(
            cand["overrides"],
            meta,
            learning_rows,
            baseline_edge=baseline_prior_edge,
            baseline_overrides=base,
            target_edge=target_edge,
        )
        scored_candidates.append({**cand, **pred})

    scored_candidates.sort(key=lambda row: float(row["predictedScore"]), reverse=True)
    stage1_names = {"baseline"}
    for row in scored_candidates[: max(1, stage1_top_n)]:
        stage1_names.add(str(row["name"]))

    data = load_training_data(allow_synthetic_fallback=False)

    rows: List[Dict[str, Any]] = []
    for cand in scored_candidates:
        if cand["name"] not in stage1_names:
            continue
        print(f"[phase16] vegas eval: {cand['name']}", flush=True)
        vegas_diag = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=cand["overrides"],
            confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
            n_bootstrap=vegas_bootstrap,
        )
        vegas = _extract_vegas(vegas_diag)
        rows.append(
            {
                "name": cand["name"],
                "source": cand["source"],
                "strategy": cand["strategy"],
                "overrides": cand["overrides"],
                "predictedEdge": cand["predictedEdge"],
                "predictedFeasibleProb": cand["predictedFeasibleProb"],
                "predictedScore": cand["predictedScore"],
                "vegas": vegas,
                "goalDistance": {
                    "targetTier": target_tier,
                    "targetEdge": target_edge,
                    "edgeGapToTarget": _goal_distance(_as_float(vegas.get("cup_relative_brier_edge")), target_edge),
                },
                "positiveRatioPrefilterPass": _passes_positive_ratio_prefilter(vegas),
                "core": None,
                "hardGatesPass": None,
                "strictNonRegression": None,
                "eligible": False,
                "highConfidenceVegas": None,
            }
        )

    baseline = next((row for row in rows if row["name"] == "baseline"), None)
    if baseline is None:
        raise RuntimeError("Phase16 baseline row missing.")

    baseline_edge = _edge(baseline)

    # Stage-2 core eval: prioritize candidates close to target and stronger edge.
    stage2_order = sorted(rows, key=lambda row: (_target_gap(row, target_edge), -_edge(row)))
    stage2_names: List[str] = ["baseline"]
    for row in stage2_order:
        if row["name"] == "baseline":
            continue
        if len(stage2_names) - 1 >= max_stage2_evals:
            break
        if not bool(row.get("positiveRatioPrefilterPass")):
            continue
        stage2_names.append(str(row["name"]))

    baseline_core: Optional[Dict[str, float]] = None
    for row in rows:
        if row["name"] not in stage2_names:
            continue
        print(f"[phase16] core eval: {row['name']}", flush=True)
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
        raise RuntimeError("Phase16 baseline core metrics missing.")

    for row in rows:
        core = row.get("core")
        if core is None:
            continue
        row["hardGatesPass"] = _hard_gates_pass(core)
        row["strictNonRegression"] = _strict_non_reg(baseline_core, core)
        row["eligible"] = bool(
            row["hardGatesPass"]
            and row["strictNonRegression"]
            and row["positiveRatioPrefilterPass"]
            and (_edge(row) > baseline_edge + EPS)
        )

    shortlist = [row for row in rows if row.get("core") is not None and row.get("positiveRatioPrefilterPass")]
    shortlist.sort(key=lambda row: (_target_gap(row, target_edge), -_edge(row)))
    for row in shortlist[: max(1, short_list_n)]:
        print(f"[phase16] high-conf vegas eval: {row['name']}", flush=True)
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

    best_raw = _best_by_target(rows, target_edge=target_edge)
    eligible_rows = [row for row in rows if row.get("eligible")]
    best_eligible = _best_by_target(eligible_rows, target_edge=target_edge)
    closest_goal = _best_by_target(rows, target_edge=target_edge)

    prefilter_pass_count = len([row for row in rows if row.get("positiveRatioPrefilterPass")])
    blockers = _build_blockers(
        baseline_edge=baseline_edge,
        target_edge=target_edge,
        best_raw=best_raw,
        best_eligible=best_eligible,
        prefilter_pass_count=prefilter_pass_count,
    )
    target_met = bool(best_eligible is not None and _target_gap(best_eligible, target_edge) <= EPS)

    deployed = False
    deploy_reason = "no promotion; target-tier and strict eligibility not both satisfied"
    strict_promotion_gate: Dict[str, Any] = {
        "required": True,
        "executed": False,
        "status": "SKIPPED",
        "returncode": None,
        "reason": "not eligible for promotion attempt",
    }
    if auto_deploy and best_eligible is not None and target_met and best_eligible["name"] != "baseline":
        strict_promotion_gate = _run_strict_release_gate_for_promotion()
        strict_promotion_gate["executed"] = True
        if strict_promotion_gate.get("status") == "PASS":
            new_profile = copy.deepcopy(profile)
            new_profile.update(best_eligible["overrides"])
            new_profile["profileVersion"] = f"phase16-{target_tier}-{datetime.now(timezone.utc).date()}"
            new_profile["optimizationMetadata"] = {
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "source": "scripts/run_phase16_adaptive_learning_loop.py",
                "targetTier": target_tier,
                "targetEdge": target_edge,
                "selectedName": best_eligible["name"],
                "selectedEdge": _edge(best_eligible),
                "strictPromotionGateStatus": strict_promotion_gate.get("status"),
            }
            DEFAULT_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_PROFILE_PATH.write_text(json.dumps(new_profile, indent=2) + "\n")
            deployed = True
            deploy_reason = (
                f"auto-deployed `{best_eligible['name']}` after meeting `{target_tier}` target and strict release gate pass"
            )
        else:
            deploy_reason = (
                f"promotion blocked: target met but strict release gate status={strict_promotion_gate.get('status')}"
            )

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase16_adaptive_learning_loop",
        "target": {
            "tier": target_tier,
            "edge": target_edge,
        },
        "summary": {
            "historicalSamples": len(learning_rows),
            "candidateBudget": len(candidate_pool),
            "stage1EvaluatedCandidates": len(rows),
            "stage2CoreEvaluatedCandidates": len([row for row in rows if row.get("core") is not None]),
            "highConfidenceEvaluatedCandidates": len([row for row in rows if row.get("highConfidenceVegas") is not None]),
            "positiveRatioPrefilterPassCount": prefilter_pass_count,
            "baselineEdge": baseline_edge,
            "bestRawEdgeName": best_raw.get("name") if best_raw else None,
            "bestRawEdge": _edge(best_raw) if best_raw else None,
            "bestEligibleName": best_eligible.get("name") if best_eligible else None,
            "bestEligibleEdge": _edge(best_eligible) if best_eligible else None,
            "closestGoalName": closest_goal.get("name") if closest_goal else None,
            "closestGoalDistance": closest_goal.get("goalDistance") if closest_goal else None,
            "eligibleCount": len(eligible_rows),
            "targetMet": target_met,
            "metaModelMode": meta.get("mode"),
            "metaModelEdgeSamples": meta.get("edgeSampleCount"),
            "metaModelFeasibleSamples": meta.get("feasibleSampleCount"),
            "learningVelocityEdgeDelta": (_edge(best_raw) - baseline_edge) if best_raw else 0.0,
            "deployRecommendation": "PROMOTE_CANDIDATE" if target_met and best_eligible else "ITERATE_WITH_BLOCKERS",
            "autoDeploy": auto_deploy,
            "deployed": deployed,
            "deployReason": deploy_reason,
            "blockerCount": len(blockers),
            "strictPromotionGateStatus": strict_promotion_gate.get("status"),
            "strictPromotionGateExecuted": bool(strict_promotion_gate.get("executed")),
        },
        "strictPromotionGate": strict_promotion_gate,
        "blockers": blockers,
        "nextActions": _next_actions(
            blockers=blockers,
            target_tier=target_tier,
            target_edge=target_edge,
            best_raw=best_raw,
            best_eligible=best_eligible,
        ),
        "rows": sorted(rows, key=lambda row: (_target_gap(row, target_edge), -_edge(row), row["name"])),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 16 Adaptive Learning Loop",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"- Target tier: `{target_tier}` (`{target_edge:.4f}`)",
        f"- Historical samples: `{report['summary']['historicalSamples']}`",
        f"- Stage1 candidates: `{report['summary']['stage1EvaluatedCandidates']}`",
        f"- Stage2 core-evaluated: `{report['summary']['stage2CoreEvaluatedCandidates']}`",
        f"- Baseline edge: `{report['summary']['baselineEdge']:.4f}`",
        f"- Best raw edge: `{report['summary']['bestRawEdgeName']}` (`{report['summary']['bestRawEdge']}`)",
        f"- Best eligible: `{report['summary']['bestEligibleName']}` (`{report['summary']['bestEligibleEdge']}`)",
        f"- Target met: `{report['summary']['targetMet']}`",
        f"- Recommendation: `{report['summary']['deployRecommendation']}`",
        f"- Deploy status: `{report['summary']['deployed']}` ({report['summary']['deployReason']})",
        f"- Strict promotion gate status: `{report['summary']['strictPromotionGateStatus']}`",
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
            "| Candidate | Edge | Gap To Target | Eligible | Core Eval | Positive-Ratio Prefilter |",
            "|---|---:|---:|---|---|---|",
        ]
    )

    for row in report["rows"][:12]:
        edge = row.get("vegas", {}).get("cup_relative_brier_edge")
        gap = row.get("goalDistance", {}).get("edgeGapToTarget")
        lines.append(
            f"| {row.get('name')} | "
            f"{'N/A' if edge is None else f'{float(edge):.4f}'} | "
            f"{'N/A' if gap is None else f'{float(gap):.4f}'} | "
            f"{row.get('eligible')} | "
            f"{row.get('core') is not None} | "
            f"{row.get('positiveRatioPrefilterPass')} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
