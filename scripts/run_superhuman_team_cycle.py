#!/usr/bin/env python3
"""
Run a full Superhuman team collaboration cycle.

This script executes the agreed multi-team workflow and publishes:
- machine-readable execution report
- human-readable owner/action summary
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = PROJECT_ROOT / "reports" / "superhuman_team_cycle_latest.json"
OUT_MD = PROJECT_ROOT / "reports" / "SUPERHUMAN_TEAM_CYCLE_LATEST.md"
BENCHMARK_PATH = PROJECT_ROOT / "reports" / "benchmark_latest.json"
PHASE10_PATH = PROJECT_ROOT / "reports" / "phase10_ab_top1_recovery.json"
PHASE12_PATH = PROJECT_ROOT / "reports" / "phase12_goal_gap_closure.json"
PHASE13_PATH = PROJECT_ROOT / "reports" / "phase13_eligible_feature_push.json"
PHASE16_PATH = PROJECT_ROOT / "reports" / "phase16_adaptive_learning_loop.json"
PHASE17_PATH = PROJECT_ROOT / "reports" / "phase17_downside_stability_lane.json"
PHASE18_PATH = PROJECT_ROOT / "reports" / "phase18_feedback_control_loop.json"
DASHBOARD_FEEDBACK_PATH = PROJECT_ROOT / "reports" / "dashboard_feedback_loop_latest.json"
DEFAULT_STEP_TIMEOUT_SECONDS = 1800
MIN_STEP_TIMEOUT_SECONDS = 60
_raw_step_timeout = int(os.getenv("TEAM_CYCLE_STEP_TIMEOUT_SECONDS", str(DEFAULT_STEP_TIMEOUT_SECONDS)))
STEP_TIMEOUT_SECONDS = max(MIN_STEP_TIMEOUT_SECONDS, _raw_step_timeout)


@dataclass
class Step:
    phase: str
    owner: str
    purpose: str
    cmd: List[str]
    blocking: bool = True


def _run(cmd: List[str]) -> Dict[str, object]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=STEP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        duration = (datetime.now(timezone.utc) - started).total_seconds()
        return {
            "cmd": " ".join(cmd),
            "returncode": 124,
            "stdout": stdout.strip(),
            "stderr": f"Timed out after {STEP_TIMEOUT_SECONDS}s",
            "timedOut": True,
            "timeoutSeconds": STEP_TIMEOUT_SECONDS,
            "durationSeconds": round(duration, 2),
        }
    duration = (datetime.now(timezone.utc) - started).total_seconds()
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "timedOut": False,
        "timeoutSeconds": STEP_TIMEOUT_SECONDS,
        "durationSeconds": round(duration, 2),
    }


def _load_benchmark_snapshot() -> Dict[str, object]:
    if not BENCHMARK_PATH.exists():
        return {}
    payload = json.loads(BENCHMARK_PATH.read_text())
    return payload.get("current", {})


def _load_phase10_snapshot() -> Dict[str, object]:
    if not PHASE10_PATH.exists():
        return {}
    return json.loads(PHASE10_PATH.read_text())


def _load_phase12_snapshot() -> Dict[str, object]:
    if not PHASE12_PATH.exists():
        return {}
    return json.loads(PHASE12_PATH.read_text())


def _load_phase13_snapshot() -> Dict[str, object]:
    if not PHASE13_PATH.exists():
        return {}
    return json.loads(PHASE13_PATH.read_text())


def _load_phase16_snapshot() -> Dict[str, object]:
    if not PHASE16_PATH.exists():
        return {}
    return json.loads(PHASE16_PATH.read_text())


def _load_phase17_snapshot() -> Dict[str, object]:
    if not PHASE17_PATH.exists():
        return {}
    return json.loads(PHASE17_PATH.read_text())


def _load_phase18_snapshot() -> Dict[str, object]:
    if not PHASE18_PATH.exists():
        return {}
    return json.loads(PHASE18_PATH.read_text())


def _load_dashboard_feedback_snapshot() -> Dict[str, object]:
    if not DASHBOARD_FEEDBACK_PATH.exists():
        return {}
    return json.loads(DASHBOARD_FEEDBACK_PATH.read_text())


def _build_steps() -> List[Step]:
    py = sys.executable
    return [
        Step(
            phase="Phase 2 (Cup Edge A/B)",
            owner="superhuman-builder-verifier",
            purpose="Run A/B profile recovery cycle and preserve artifacts.",
            cmd=[py, "scripts/run_phase10_ab_top1_recovery.py"],
        ),
        Step(
            phase="Phase 2 (Cup Edge Constrained Batch)",
            owner="superhuman-builder-verifier",
            purpose="Run constrained edge-improvement candidate batch with strict non-regression.",
            cmd=[py, "scripts/run_phase11_constrained_edge_batch.py"],
        ),
        Step(
            phase="Phase 2 (Goal Gap Closure)",
            owner="superhuman-builder-verifier",
            purpose="Run anchor-based search focused on closing the undeniable Cup-vs-Vegas target gap.",
            cmd=[py, "scripts/run_phase12_goal_gap_closure.py"],
        ),
        Step(
            phase="Phase 2 (Eligible Feature Push)",
            owner="superhuman-builder-verifier",
            purpose="Run Phase 13 focused on strict-eligible anchors with hard positive-ratio prefilter.",
            cmd=[py, "scripts/run_phase13_eligible_feature_push.py"],
        ),
        Step(
            phase="Phase 2 (Adaptive Strong-Tier Loop)",
            owner="superhuman-edge-goal-loop",
            purpose="Run adaptive learning loop targeting strong-tier Cup-vs-Vegas edge under strict gates.",
            cmd=[py, "scripts/run_phase16_adaptive_learning_loop.py"],
        ),
        Step(
            phase="Phase 2 (Downside Stability Lane)",
            owner="superhuman-edge-goal-loop",
            purpose="Run positive-season-ratio and downside-tail suppression lane with strict core protections.",
            cmd=[py, "scripts/run_phase17_downside_stability_lane.py"],
        ),
        Step(
            phase="Phase 2 (Feedback Control Loop)",
            owner="superhuman-edge-goal-loop",
            purpose="Convert latest edge/downside outcomes into adaptive next-cycle control decisions.",
            cmd=[py, "scripts/run_phase18_feedback_control_loop.py"],
        ),
        Step(
            phase="Phase 3 (Data Truth)",
            owner="superhuman-builder-verifier",
            purpose="Validate historical advanced coverage health.",
            cmd=[py, "scripts/audit_historical_feature_coverage.py"],
        ),
        Step(
            phase="Phase 1 (Core Gate Protection)",
            owner="superhuman-project-operator",
            purpose="Refresh benchmark snapshot for decision board.",
            cmd=[py, "scripts/update_benchmark_metrics.py"],
        ),
        Step(
            phase="Phase 4 (Release Decision)",
            owner="superhuman-review-improver",
            purpose="Run strict model-vs-Vegas gate.",
            cmd=[
                py,
                "-W",
                "error::RuntimeWarning",
                "scripts/verify_model_performance.py",
                "--require-vegas-edge",
                "--require-cup-vegas-goal",
            ],
        ),
        Step(
            phase="Phase 1 (Core Gate Protection)",
            owner="test-engineer",
            purpose="Run regression tests.",
            cmd=[py, "-m", "pytest", "-q"],
        ),
        Step(
            phase="Phase 1 (Core Gate Protection)",
            owner="verify-app",
            purpose="Run data integrity gate.",
            cmd=[py, "scripts/validate_data.py", "--strict"],
        ),
        Step(
            phase="Phase 1 (Core Gate Protection)",
            owner="verify-app",
            purpose="Regenerate dashboard artifact.",
            cmd=[py, "-m", "superhuman.dashboard_generator"],
        ),
        Step(
            phase="Phase 1 (Dashboard Feedback Loop)",
            owner="superhuman-dashboard-trust-polisher",
            purpose="Block finalization when dashboard trust, coherence, or overflow checks fail.",
            cmd=[py, "scripts/run_dashboard_feedback_loop.py"],
        ),
        Step(
            phase="Phase 5 (Adversarial Team Grill)",
            owner="superhuman-issue-squad-orchestrator",
            purpose="Publish limiting-factor grill artifact with owner/accountability commitments.",
            cmd=[py, "scripts/run_superhuman_grill_session.py"],
        ),
    ]


def _next_actions(
    strict_gate_failed: bool,
    bench: Dict[str, object],
    phase10: Dict[str, object],
    phase12: Dict[str, object],
    phase13: Dict[str, object],
    phase16: Dict[str, object],
    phase17: Dict[str, object],
    phase18: Dict[str, object],
    dashboard_feedback: Dict[str, object],
) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []

    if strict_gate_failed:
        actions.append(
            {
                "owner": "superhuman-discovery-planner",
                "action": "Narrow next candidate search around edge-preserving profiles with hard Top5/F1 constraints.",
            }
        )
        actions.append(
            {
                "owner": "superhuman-builder-verifier",
                "action": "Run constrained candidate batch focused on improving Cup edge while maintaining strict non-regression.",
            }
        )
        actions.append(
            {
                "owner": "superhuman-review-improver",
                "action": "Reject candidates that improve edge but degrade core reliability metrics.",
            }
        )

    if phase10:
        decision = phase10.get("decision", {})
        selected = decision.get("selected")
        if selected:
            actions.append(
                {
                    "owner": "superhuman-project-operator",
                    "action": f"Keep production on baseline lane and maintain `{selected}` as tracked A/B context only.",
                }
            )

    phase11_path = PROJECT_ROOT / "reports" / "phase11_constrained_edge_batch.json"
    if phase11_path.exists():
        try:
            phase11 = json.loads(phase11_path.read_text())
            summary = phase11.get("summary", {})
            if int(summary.get("eligibleCount", 0)) == 0:
                actions.append(
                    {
                        "owner": "superhuman-discovery-planner",
                        "action": "Adjust constrained search space (decay/boost/weights) because current phase11 batch yielded zero strict-eligible edge-improvers.",
                    }
                )
            else:
                actions.append(
                    {
                        "owner": "superhuman-review-improver",
                        "action": f"Review phase11 best eligible candidate `{summary.get('bestEligibleName')}` for promotion readiness.",
                    }
                )
        except Exception:
            pass

    if phase12:
        summary = phase12.get("summary", {})
        undeniable_count = int(summary.get("undeniableCount", 0) or 0)
        eligible_count = int(summary.get("eligibleCount", 0) or 0)
        closest_name = summary.get("closestGoalName")

        if undeniable_count > 0:
            actions.append(
                {
                    "owner": "superhuman-review-improver",
                    "action": f"Review undeniable candidate set and prepare promotion package (closest: `{closest_name}`).",
                }
            )
            actions.append(
                {
                    "owner": "superhuman-project-operator",
                    "action": "Run release decision lane with promotion-candidate profile artifacts and strict gate verification.",
                }
            )
        elif eligible_count > 0:
            actions.append(
                {
                    "owner": "superhuman-discovery-planner",
                    "action": f"Design the next constrained profile batch around `{closest_name}` to close remaining target gaps.",
                }
            )
            actions.append(
                {
                    "owner": "superhuman-builder-verifier",
                    "action": "Execute another goal-gap closure batch with stronger season-level signal features while preserving strict non-regression.",
                }
            )
        else:
            actions.append(
                {
                    "owner": "superhuman-discovery-planner",
                    "action": "Re-scope phase-2 search space; current goal-gap closure batch yielded zero strict-eligible edge-improvers.",
                }
            )

    if phase13:
        summary = phase13.get("summary", {})
        undeniable_count = int(summary.get("undeniableCount", 0) or 0)
        eligible_count = int(summary.get("eligibleCount", 0) or 0)
        prefilter_count = int(summary.get("positiveRatioPrefilterPassCount", 0) or 0)
        closest_feasible = summary.get("closestFeasibleName")

        if undeniable_count > 0:
            actions.append(
                {
                    "owner": "superhuman-review-improver",
                    "action": "Phase 13 produced undeniable candidate(s); prepare promotion audit package immediately.",
                }
            )
        elif prefilter_count == 0:
            actions.append(
                {
                    "owner": "superhuman-discovery-planner",
                    "action": "No Phase 13 candidate passed hard positive-season-ratio feasibility; plan structural feature changes (not just profile tuning).",
                }
            )
            actions.append(
                {
                    "owner": "superhuman-builder-verifier",
                    "action": "Implement feature-level data/model upgrades aimed at increasing positive-season ratio before next edge search.",
                }
            )
        elif eligible_count > 0:
            actions.append(
                {
                    "owner": "superhuman-review-improver",
                    "action": f"Review Phase 13 best eligible profile and closest feasible candidate `{closest_feasible}` for next constrained batch.",
                }
            )

    if phase16:
        summary = phase16.get("summary", {})
        target = phase16.get("target", {})
        blockers = phase16.get("blockers", []) or []
        target_tier = target.get("tier", "strong")
        target_edge = target.get("edge")
        best_eligible = summary.get("bestEligibleName")
        target_met = bool(summary.get("targetMet"))

        if target_met and best_eligible:
            actions.append(
                {
                    "owner": "superhuman-review-improver",
                    "action": f"Adaptive loop hit `{target_tier}` target; run promotion audit for `{best_eligible}`.",
                }
            )
        else:
            actions.append(
                {
                    "owner": "superhuman-discovery-planner",
                    "action": f"Re-run adaptive strong-tier loop and close remaining gap to `{target_tier}` target ({target_edge}).",
                }
            )
            if blockers:
                actions.append(
                    {
                        "owner": "superhuman-prevention-loop",
                        "action": f"Convert top blocker into durable control: {blockers[0]}",
                    }
                )

    if phase17:
        summary = phase17.get("summary", {})
        rec = summary.get("recommendation")
        best = summary.get("bestDownsideName")
        min_delta = summary.get("downsideMinSeasonEdgeDelta")
        if rec == "USE_PHASE17_CANDIDATE" and best:
            actions.append(
                {
                    "owner": "superhuman-review-improver",
                    "action": f"Review downside-stability winner `{best}` and assess merge strategy with phase16 champion.",
                }
            )
        else:
            actions.append(
                {
                    "owner": "superhuman-discovery-planner",
                    "action": f"Phase17 produced no strict winner; re-scope downside controls (current min-season-edge delta: {min_delta}).",
                }
            )

    if phase18:
        summary = phase18.get("summary", {})
        commands = phase18.get("recommendedCommands", {})
        control_mode = summary.get("controlMode")
        strong_gap = summary.get("phase16StrongGap")
        if control_mode:
            actions.append(
                {
                    "owner": "superhuman-edge-goal-loop",
                    "action": f"Run next loop in `{control_mode}` mode; strong-tier gap currently {strong_gap}.",
                }
            )
        if commands.get("phase16"):
            actions.append(
                {
                    "owner": "superhuman-builder-verifier",
                    "action": f"Execute feedback-tuned phase16 command: {commands.get('phase16')}",
                }
            )
        if commands.get("phase17"):
            actions.append(
                {
                    "owner": "superhuman-builder-verifier",
                    "action": f"Execute feedback-tuned phase17 command: {commands.get('phase17')}",
                }
            )

    if dashboard_feedback:
        status = str(dashboard_feedback.get("status", "FAIL")).upper()
        errors = dashboard_feedback.get("errors", []) or []
        if status != "PASS":
            actions.append(
                {
                    "owner": "superhuman-dashboard-trust-polisher",
                    "action": "Fix dashboard blocker checks before final status; resolve bracket coherence, scorecard sanity, and mission overflow regressions.",
                }
            )
            if errors:
                actions.append(
                    {
                        "owner": "superhuman-prevention-loop",
                        "action": f"Convert top dashboard failure into durable regression control: {errors[0]}",
                    }
                )

    cup_edge = bench.get("vegas", {}).get("cup_relative_brier_edge") if bench else None
    if cup_edge is not None and float(cup_edge) < 0:
        actions.append(
            {
                "owner": "framework-improver",
                "action": "Record this cycle's edge-vs-stability tradeoff and update future search priors.",
            }
        )
    return actions


def main() -> int:
    steps = _build_steps()
    results = []

    for step in steps:
        print(f"[team-cycle] {step.owner} -> {' '.join(step.cmd)}", flush=True)
        res = _run(step.cmd)
        results.append(
            {
                "phase": step.phase,
                "owner": step.owner,
                "purpose": step.purpose,
                "blocking": step.blocking,
                **res,
            }
        )

    blocking_failures = [r for r in results if r["blocking"] and r["returncode"] != 0]
    status = "PASS" if not blocking_failures else "FAIL"

    benchmark = _load_benchmark_snapshot()
    phase10 = _load_phase10_snapshot()
    phase12 = _load_phase12_snapshot()
    phase13 = _load_phase13_snapshot()
    phase16 = _load_phase16_snapshot()
    phase17 = _load_phase17_snapshot()
    phase18 = _load_phase18_snapshot()
    dashboard_feedback = _load_dashboard_feedback_snapshot()

    strict_gate_failed = any(
        ("verify_model_performance.py" in r["cmd"] and r["returncode"] != 0)
        for r in results
    )
    actions = _next_actions(
        strict_gate_failed,
        benchmark,
        phase10,
        phase12,
        phase13,
        phase16,
        phase17,
        phase18,
        dashboard_feedback,
    )

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "blockingFailures": [r["cmd"] for r in blocking_failures],
        "steps": results,
        "snapshot": {
            "core": benchmark.get("core", {}),
            "vegas": benchmark.get("vegas", {}),
            "phase10Decision": phase10.get("decision", {}),
            "phase12Summary": phase12.get("summary", {}),
            "phase13Summary": phase13.get("summary", {}),
            "phase16Summary": phase16.get("summary", {}),
            "phase17Summary": phase17.get("summary", {}),
            "phase18Summary": phase18.get("summary", {}),
            "dashboardFeedback": {
                "status": dashboard_feedback.get("status"),
                "errors": dashboard_feedback.get("errors", []),
                "warnings": dashboard_feedback.get("warnings", []),
            },
        },
        "nextActions": actions,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Superhuman Team Cycle (Latest)",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"Status: **{status}**",
        "",
        "## Execution",
        "",
        "| Phase | Owner | Command | Status |",
        "|---|---|---|---|",
    ]
    for row in results:
        lines.append(
            f"| {row['phase']} | {row['owner']} | `{row['cmd']}` | "
            f"{'PASS' if row['returncode'] == 0 else 'FAIL'} |"
        )

    lines.extend(
        [
            "",
            "## Snapshot",
            "",
            f"- Core: `{report['snapshot']['core']}`",
            f"- Vegas: `{report['snapshot']['vegas']}`",
            f"- Phase10 decision: `{report['snapshot']['phase10Decision']}`",
            f"- Phase12 summary: `{report['snapshot']['phase12Summary']}`",
            f"- Phase13 summary: `{report['snapshot']['phase13Summary']}`",
            f"- Phase16 summary: `{report['snapshot']['phase16Summary']}`",
            f"- Phase17 summary: `{report['snapshot']['phase17Summary']}`",
            f"- Phase18 summary: `{report['snapshot']['phase18Summary']}`",
            f"- Dashboard feedback: `{report['snapshot']['dashboardFeedback']}`",
            "",
            "## Next Owner Actions",
            "",
        ]
    )
    if actions:
        for action in actions:
            lines.append(f"- `{action['owner']}`: {action['action']}")
    else:
        lines.append("- No follow-up actions required.")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
