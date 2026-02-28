#!/usr/bin/env python3
"""
Phase 18: closed-loop feedback control for edge and downside stability.

This lane turns latest benchmark + phase16/phase17 outcomes into deterministic
control decisions for the next cycle. It keeps a small state file so the loop
can react to stagnation and downside-regression streaks instead of repeating
the same search behavior every run.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"

BENCHMARK_PATH = REPORTS_DIR / "benchmark_latest.json"
PHASE16_PATH = REPORTS_DIR / "phase16_adaptive_learning_loop.json"
PHASE17_PATH = REPORTS_DIR / "phase17_downside_stability_lane.json"

OUT_JSON = REPORTS_DIR / "phase18_feedback_control_loop.json"
OUT_MD = REPORTS_DIR / "PHASE18_FEEDBACK_CONTROL_LOOP.md"
STATE_PATH = DATA_DIR / "phase18_feedback_state.json"

EPS = 1e-9
DEFAULT_RECOMMENDED_STEP_TIMEOUT_SECONDS = 1800
MIN_RECOMMENDED_STEP_TIMEOUT_SECONDS = 60
_raw_recommended_timeout = int(
    os.getenv("PHASE18_RECOMMENDED_STEP_TIMEOUT_SECONDS", str(DEFAULT_RECOMMENDED_STEP_TIMEOUT_SECONDS))
)
RECOMMENDED_STEP_TIMEOUT_SECONDS = max(MIN_RECOMMENDED_STEP_TIMEOUT_SECONDS, _raw_recommended_timeout)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _as_float(value: Any) -> Optional[float]:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not (out == out) or out in (float("inf"), float("-inf")):
        return None
    return out


def _default_state() -> Dict[str, Any]:
    return {
        "iteration": 0,
        "stagnationStreak": 0,
        "downsideRegressionStreak": 0,
        "strongGapStreak": 0,
        "lastBestEdge": None,
        "lastStrongGap": None,
        "lastDownsideMinSeasonEdgeDelta": None,
        "updatedAt": None,
    }


def _load_state() -> Dict[str, Any]:
    payload = _read_json(STATE_PATH)
    state = _default_state()
    if isinstance(payload, dict):
        state.update(payload)
    return state


def _strong_target_edge(benchmark: Dict[str, Any], phase16: Dict[str, Any]) -> float:
    vegas = benchmark.get("current", {}).get("vegas", {}) if isinstance(benchmark, dict) else {}
    target = vegas.get("cup_target", {}) if isinstance(vegas, dict) else {}
    strong = _as_float(target.get("relative_brier_improvement_strong"))
    if strong is not None:
        return strong
    phase16_target = _as_float((phase16.get("target") or {}).get("edge"))
    if phase16_target is not None:
        return phase16_target
    return 0.03


def _extract_metrics(benchmark: Dict[str, Any], phase16: Dict[str, Any], phase17: Dict[str, Any]) -> Dict[str, Any]:
    vegas = benchmark.get("current", {}).get("vegas", {}) if isinstance(benchmark, dict) else {}
    target = vegas.get("cup_target", {}) if isinstance(vegas, dict) else {}
    phase16_summary = phase16.get("summary", {}) if isinstance(phase16, dict) else {}
    phase17_summary = phase17.get("summary", {}) if isinstance(phase17, dict) else {}

    target_edge = _strong_target_edge(benchmark, phase16)
    benchmark_edge = _as_float(vegas.get("cup_relative_brier_edge"))
    best_eligible = _as_float(phase16_summary.get("bestEligibleEdge"))
    best_raw = _as_float(phase16_summary.get("bestRawEdge"))
    best_edge = best_eligible if best_eligible is not None else best_raw
    if best_edge is None:
        best_edge = benchmark_edge

    strong_gap = _as_float((phase16_summary.get("closestGoalDistance") or {}).get("edgeGapToTarget"))
    if strong_gap is None and best_edge is not None:
        strong_gap = max(target_edge - best_edge, 0.0)

    baseline_min = _as_float(phase17_summary.get("baselineMinSeasonEdge"))
    downside_min_delta = _as_float(phase17_summary.get("downsideMinSeasonEdgeDelta"))
    target_met = bool(phase16_summary.get("targetMet"))
    strict_status = str(phase16_summary.get("strictPromotionGateStatus", "UNKNOWN")).upper()
    release_floor_met = bool(target.get("release_floor_met") or target.get("goal_met"))

    return {
        "targetEdge": target_edge,
        "benchmarkEdge": benchmark_edge,
        "phase16BestEdge": best_edge,
        "phase16StrongGap": strong_gap,
        "phase16TargetMet": target_met,
        "phase16StrictPromotionGateStatus": strict_status,
        "phase17BaselineMinSeasonEdge": baseline_min,
        "phase17DownsideMinSeasonEdgeDelta": downside_min_delta,
        "phase17Recommendation": phase17_summary.get("recommendation"),
        "releaseFloorMet": release_floor_met,
    }


def _update_state(state_before: Dict[str, Any], metrics: Dict[str, Any], min_edge_improvement: float) -> Dict[str, Any]:
    state_after = dict(state_before)
    state_after["iteration"] = int(state_before.get("iteration", 0) or 0) + 1

    prev_best = _as_float(state_before.get("lastBestEdge"))
    curr_best = _as_float(metrics.get("phase16BestEdge"))
    if prev_best is None or curr_best is None or (curr_best - prev_best) > min_edge_improvement:
        state_after["stagnationStreak"] = 0
    else:
        state_after["stagnationStreak"] = int(state_before.get("stagnationStreak", 0) or 0) + 1

    curr_downside_delta = _as_float(metrics.get("phase17DownsideMinSeasonEdgeDelta"))
    if curr_downside_delta is not None and curr_downside_delta < -EPS:
        state_after["downsideRegressionStreak"] = int(state_before.get("downsideRegressionStreak", 0) or 0) + 1
    else:
        state_after["downsideRegressionStreak"] = 0

    strong_gap = _as_float(metrics.get("phase16StrongGap"))
    if strong_gap is not None and strong_gap > EPS:
        state_after["strongGapStreak"] = int(state_before.get("strongGapStreak", 0) or 0) + 1
    else:
        state_after["strongGapStreak"] = 0

    state_after["lastBestEdge"] = curr_best
    state_after["lastStrongGap"] = strong_gap
    state_after["lastDownsideMinSeasonEdgeDelta"] = curr_downside_delta
    state_after["updatedAt"] = datetime.now(timezone.utc).isoformat()
    return state_after


def _infer_control_mode(strong_gap: Optional[float], stagnation_streak: int, downside_regression_streak: int) -> str:
    if downside_regression_streak >= 2:
        return "DOWNSIDE_RECOVERY"
    if strong_gap is not None and strong_gap > EPS and stagnation_streak >= 2:
        return "ESCALATE_EXPLORATION"
    if strong_gap is not None and strong_gap > EPS:
        return "TARGET_CLOSURE"
    return "PROMOTION_READINESS"


def _recommend_phase16_params(control_mode: str, strong_gap: Optional[float], stagnation_streak: int) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "PHASE16_CANDIDATE_BUDGET": 26,
        "PHASE16_STAGE1_TOP_N": 12,
        "PHASE16_MAX_STAGE2_EVALS": 6,
        "PHASE16_SHORTLIST_N": 4,
        "PHASE16_VEGAS_BOOTSTRAP": 360,
        "PHASE16_HIGH_CONF_BOOTSTRAP": 1400,
    }

    if control_mode == "ESCALATE_EXPLORATION":
        params.update(
            {
                "PHASE16_CANDIDATE_BUDGET": 32,
                "PHASE16_STAGE1_TOP_N": 16,
                "PHASE16_MAX_STAGE2_EVALS": 8,
                "PHASE16_SHORTLIST_N": 5,
                "PHASE16_VEGAS_BOOTSTRAP": 420,
                "PHASE16_HIGH_CONF_BOOTSTRAP": 1600,
            }
        )
    elif control_mode == "DOWNSIDE_RECOVERY":
        params.update(
            {
                "PHASE16_CANDIDATE_BUDGET": 24,
                "PHASE16_STAGE1_TOP_N": 10,
                "PHASE16_MAX_STAGE2_EVALS": 5,
            }
        )

    if strong_gap is not None and strong_gap > 0.012:
        params["PHASE16_CANDIDATE_BUDGET"] = max(int(params["PHASE16_CANDIDATE_BUDGET"]), 30)
    if stagnation_streak >= 3:
        params["PHASE16_CANDIDATE_BUDGET"] = int(params["PHASE16_CANDIDATE_BUDGET"]) + 2
    return params


def _recommend_phase17_params(
    control_mode: str,
    downside_regression_streak: int,
    baseline_min_season_edge: Optional[float],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "PHASE17_CANDIDATE_BUDGET": 20,
        "PHASE17_STAGE2_EVALS": 5,
        "PHASE17_SHORTLIST_N": 4,
        "PHASE17_VEGAS_BOOTSTRAP": 320,
        "PHASE17_HIGH_CONF_BOOTSTRAP": 1200,
        "PHASE17_MIN_POSITIVE_RATIO": 0.85,
        "PHASE17_MIN_SEASON_EDGE_FLOOR": -0.03,
        "PHASE17_MAX_NEGATIVE_SEASON_RATIO": 0.30,
        "PHASE17_MAX_EDGE_DROP_VS_BASELINE": 0.0008,
    }

    if control_mode == "DOWNSIDE_RECOVERY" or downside_regression_streak >= 1:
        floor = -0.02
        if baseline_min_season_edge is not None:
            floor = max(baseline_min_season_edge - 0.001, -0.02)
        params.update(
            {
                "PHASE17_MIN_POSITIVE_RATIO": 0.90,
                "PHASE17_MIN_SEASON_EDGE_FLOOR": round(floor, 4),
                "PHASE17_MAX_NEGATIVE_SEASON_RATIO": 0.20,
                "PHASE17_MAX_EDGE_DROP_VS_BASELINE": 0.0005,
            }
        )
    if control_mode == "ESCALATE_EXPLORATION":
        params["PHASE17_CANDIDATE_BUDGET"] = 24
    return params


def _build_env_command(script_path: str, env_vars: Dict[str, Any]) -> str:
    parts = []
    for key in sorted(env_vars):
        value = env_vars[key]
        if isinstance(value, float):
            rendered = f"{value:.6g}"
        else:
            rendered = str(value)
        parts.append(f"{key}={shlex.quote(rendered)}")
    parts.append(f"python3 {script_path}")
    return " ".join(parts)


def _run_recommended(params16: Dict[str, Any], params17: Dict[str, Any]) -> List[Dict[str, Any]]:
    env = os.environ.copy()
    py = sys.executable
    steps: List[Tuple[str, str, Dict[str, Any]]] = [
        ("phase16", "scripts/run_phase16_adaptive_learning_loop.py", params16),
        ("phase17", "scripts/run_phase17_downside_stability_lane.py", params17),
    ]
    results: List[Dict[str, Any]] = []
    for phase, script, overrides in steps:
        step_env = env.copy()
        for key, value in overrides.items():
            step_env[key] = str(value)
        try:
            proc = subprocess.run(
                [py, script],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                env=step_env,
                timeout=RECOMMENDED_STEP_TIMEOUT_SECONDS,
            )
            results.append(
                {
                    "phase": phase,
                    "cmd": f"{py} {script}",
                    "returncode": int(proc.returncode),
                    "stdout": (proc.stdout or "").strip(),
                    "stderr": (proc.stderr or "").strip(),
                    "timedOut": False,
                    "timeoutSeconds": RECOMMENDED_STEP_TIMEOUT_SECONDS,
                }
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            results.append(
                {
                    "phase": phase,
                    "cmd": f"{py} {script}",
                    "returncode": 124,
                    "stdout": stdout.strip(),
                    "stderr": f"Timed out after {RECOMMENDED_STEP_TIMEOUT_SECONDS}s",
                    "timedOut": True,
                    "timeoutSeconds": RECOMMENDED_STEP_TIMEOUT_SECONDS,
                }
            )
    return results


def _build_blockers(metrics: Dict[str, Any], state_after: Dict[str, Any]) -> List[str]:
    blockers: List[str] = []
    strong_gap = _as_float(metrics.get("phase16StrongGap"))
    if strong_gap is not None and strong_gap > EPS:
        blockers.append(
            f"Strong-tier gap remains {strong_gap:.4f} (target {metrics.get('targetEdge'):.4f})."
        )

    min_delta = _as_float(metrics.get("phase17DownsideMinSeasonEdgeDelta"))
    if min_delta is not None and min_delta < -EPS:
        blockers.append(
            f"Downside floor regressed by {min_delta:.4f} vs baseline."
        )

    if int(state_after.get("stagnationStreak", 0) or 0) >= 2:
        blockers.append(
            f"Edge stagnation streak is {int(state_after.get('stagnationStreak', 0))} loops."
        )
    return blockers


def _next_actions(
    control_mode: str,
    blockers: List[str],
    cmd_phase16: str,
    cmd_phase17: str,
) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = [
        {
            "owner": "Model Lead",
            "priority": "P0",
            "action": f"Execute feedback-tuned phase16 lane: `{cmd_phase16}`",
        },
        {
            "owner": "Quant Engineer",
            "priority": "P0",
            "action": f"Execute feedback-tuned phase17 lane: `{cmd_phase17}`",
        },
        {
            "owner": "Program Lead",
            "priority": "P1",
            "action": f"Control mode is `{control_mode}`; keep strict non-regression and promotion safety unchanged.",
        },
    ]
    if blockers:
        actions.append(
            {
                "owner": "Prevention Loop",
                "priority": "P1",
                "action": f"Convert top blocker into hard control: {blockers[0]}",
            }
        )
    return actions[:5]


def main() -> int:
    benchmark = _read_json(BENCHMARK_PATH)
    phase16 = _read_json(PHASE16_PATH)
    phase17 = _read_json(PHASE17_PATH)

    metrics = _extract_metrics(benchmark, phase16, phase17)
    state_before = _load_state()

    min_improvement = float(os.getenv("PHASE18_MIN_EDGE_IMPROVEMENT", "0.0005"))
    state_after = _update_state(state_before, metrics, min_edge_improvement=min_improvement)

    control_mode = _infer_control_mode(
        strong_gap=_as_float(metrics.get("phase16StrongGap")),
        stagnation_streak=int(state_after.get("stagnationStreak", 0) or 0),
        downside_regression_streak=int(state_after.get("downsideRegressionStreak", 0) or 0),
    )

    phase16_params = _recommend_phase16_params(
        control_mode=control_mode,
        strong_gap=_as_float(metrics.get("phase16StrongGap")),
        stagnation_streak=int(state_after.get("stagnationStreak", 0) or 0),
    )
    phase17_params = _recommend_phase17_params(
        control_mode=control_mode,
        downside_regression_streak=int(state_after.get("downsideRegressionStreak", 0) or 0),
        baseline_min_season_edge=_as_float(metrics.get("phase17BaselineMinSeasonEdge")),
    )

    cmd_phase16 = _build_env_command("scripts/run_phase16_adaptive_learning_loop.py", phase16_params)
    cmd_phase17 = _build_env_command("scripts/run_phase17_downside_stability_lane.py", phase17_params)

    execute_recommended = os.getenv("PHASE18_EXECUTE_RECOMMENDED", "0") == "1"
    execution_results = []
    if execute_recommended:
        execution_results = _run_recommended(phase16_params, phase17_params)

    blockers = _build_blockers(metrics, state_after)
    next_actions = _next_actions(control_mode, blockers, cmd_phase16, cmd_phase17)

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase18_feedback_control_loop",
        "summary": {
            "controlMode": control_mode,
            "targetEdge": metrics.get("targetEdge"),
            "phase16BestEdge": metrics.get("phase16BestEdge"),
            "phase16StrongGap": metrics.get("phase16StrongGap"),
            "phase17DownsideMinSeasonEdgeDelta": metrics.get("phase17DownsideMinSeasonEdgeDelta"),
            "stagnationStreak": state_after.get("stagnationStreak"),
            "downsideRegressionStreak": state_after.get("downsideRegressionStreak"),
            "strongGapStreak": state_after.get("strongGapStreak"),
            "releaseFloorMet": metrics.get("releaseFloorMet"),
            "promotionGateStatus": metrics.get("phase16StrictPromotionGateStatus"),
            "executeRecommended": execute_recommended,
            "executionFailureCount": len([row for row in execution_results if row.get("returncode") != 0]),
            "blockerCount": len(blockers),
        },
        "inputs": {
            "benchmarkTimestamp": benchmark.get("current", {}).get("timestamp"),
            "phase16GeneratedAt": phase16.get("generatedAt"),
            "phase17GeneratedAt": phase17.get("generatedAt"),
            "metrics": metrics,
        },
        "stateBefore": state_before,
        "stateAfter": state_after,
        "recommendedParams": {
            "phase16": phase16_params,
            "phase17": phase17_params,
        },
        "recommendedCommands": {
            "phase16": cmd_phase16,
            "phase17": cmd_phase17,
            "pipeline": f"{cmd_phase16} && {cmd_phase17}",
        },
        "execution": execution_results,
        "blockers": blockers,
        "nextActions": next_actions,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state_after, indent=2) + "\n")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 18 Feedback Control Loop",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"- Control mode: `{report['summary']['controlMode']}`",
        f"- Target edge: `{report['summary']['targetEdge']}`",
        f"- Phase16 best edge: `{report['summary']['phase16BestEdge']}`",
        f"- Strong-tier gap: `{report['summary']['phase16StrongGap']}`",
        f"- Phase17 downside min-season-edge delta: `{report['summary']['phase17DownsideMinSeasonEdgeDelta']}`",
        f"- Stagnation streak: `{report['summary']['stagnationStreak']}`",
        f"- Downside regression streak: `{report['summary']['downsideRegressionStreak']}`",
        f"- Execute recommended loop this run: `{report['summary']['executeRecommended']}`",
        "",
        "## Recommended Commands",
        "",
        f"- Phase16: `{report['recommendedCommands']['phase16']}`",
        f"- Phase17: `{report['recommendedCommands']['phase17']}`",
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
            "## Next Actions",
            "",
        ]
    )
    for row in next_actions:
        lines.append(f"- `{row['owner']}` ({row['priority']}): {row['action']}")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"Updated {STATE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
