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
    proc = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
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
    ]


def _next_actions(
    strict_gate_failed: bool,
    bench: Dict[str, object],
    phase10: Dict[str, object],
    phase12: Dict[str, object],
    phase13: Dict[str, object],
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

    strict_gate_failed = any(
        ("verify_model_performance.py" in r["cmd"] and r["returncode"] != 0)
        for r in results
    )
    actions = _next_actions(strict_gate_failed, benchmark, phase10, phase12, phase13)

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
