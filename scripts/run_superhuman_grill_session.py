#!/usr/bin/env python3
"""
Generate an adversarial superhuman-team grill session report.

This captures cross-functional challenges and forced-counter proposals so the
project optimizes for "undeniably best" outcomes, not minimum gate pass.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
OUT_JSON = REPORTS_DIR / "superhuman_grill_session_latest.json"
OUT_MD = REPORTS_DIR / "SUPERHUMAN_GRILL_SESSION_LATEST.md"

BENCHMARK_PATH = REPORTS_DIR / "benchmark_latest.json"
PHASE16_PATH = REPORTS_DIR / "phase16_adaptive_learning_loop.json"
PHASE17_PATH = REPORTS_DIR / "phase17_downside_stability_lane.json"
PHASE18_PATH = REPORTS_DIR / "phase18_feedback_control_loop.json"
PHASE7_LATEST_PATH = REPORTS_DIR / "phase7_release_cycle_latest.json"
PHASE7_PATH = REPORTS_DIR / "phase7_release_cycle.json"
DASHBOARD_FEEDBACK_PATH = REPORTS_DIR / "dashboard_feedback_loop_latest.json"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _fmt_pct(value: Any, digits: int = 2) -> str:
    if not isinstance(value, (int, float)):
        return "--"
    return f"{float(value) * 100:.{digits}f}%"


def _resolve_release_strict_status(payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "UNKNOWN"
    strict = payload.get("strict", {})
    status = payload.get("shipGateStatus") or strict.get("status") or payload.get("status") or "UNKNOWN"
    return str(status).upper()


def _build_grill_rounds(snapshot: Dict[str, Any]) -> List[Dict[str, str]]:
    edge = snapshot.get("benchmark", {}).get("edge")
    strong_gap = snapshot.get("phase16", {}).get("strongGap")
    phase17_min_delta = snapshot.get("phase17", {}).get("minSeasonEdgeDelta")
    phase18_mode = snapshot.get("phase18", {}).get("controlMode")

    return [
        {
            "challenger": "Vegas Skeptic",
            "challenge": (
                f"Edge is {_fmt_pct(edge)} and still below strong-tier target; why should anyone trust this as an enduring market edge?"
            ),
            "counterOwner": "Model Lead",
            "counter": (
                "Run expanded adaptive candidate budget with strict non-regression and require high-confidence CI checks on finalists."
            ),
            "commitment": "Execute phase16 with larger budget and shortlist high-confidence evaluations.",
            "command": "PHASE16_CANDIDATE_BUDGET=28 PHASE16_STAGE1_TOP_N=14 PHASE16_MAX_STAGE2_EVALS=6 PHASE16_SHORTLIST_N=4 python3 scripts/run_phase16_adaptive_learning_loop.py",
        },
        {
            "challenger": "Downside Risk Sheriff",
            "challenge": (
                f"Even if edge rises, downside seasons can erase trust. What is the hard plan for min-season-edge and positive-season-ratio stability?"
            ),
            "counterOwner": "Quant Engineer",
            "counter": (
                "Run dedicated downside-stability lane with floor constraints and reject any candidate that worsens tail behavior."
            ),
            "commitment": (
                f"Improve downside floor (current delta {_fmt_pct(phase17_min_delta, 3)}) while keeping edge non-regression."
            ),
            "command": "python3 scripts/run_phase17_downside_stability_lane.py",
        },
        {
            "challenger": "Feedback Controller",
            "challenge": "Do we have a real closed-loop response to stagnation/downside regression, or are we just re-running static scripts?",
            "counterOwner": "ML Systems Engineer",
            "counter": "Phase18 now tracks loop-state streaks and emits control-mode specific commands for phase16/phase17.",
            "commitment": f"Run next cycle in feedback mode `{phase18_mode}` and enforce parameter updates from the control loop.",
            "command": "python3 scripts/run_phase18_feedback_control_loop.py",
        },
        {
            "challenger": "Release Sheriff",
            "challenge": "Could a candidate be promoted on metric excitement without full release truth?",
            "counterOwner": "Platform Engineer",
            "counter": "No. Promotion path now requires target-tier pass and strict phase7 release gate pass in the same execution context.",
            "commitment": "Keep auto-deploy blocked unless both conditions pass in one run.",
            "command": "PHASE16_AUTO_DEPLOY=1 python3 scripts/run_phase16_adaptive_learning_loop.py",
        },
        {
            "challenger": "Design Critic (Ives bar)",
            "challenge": "Is the dashboard narrating uncomfortable truth clearly, or still hiding behind scorecards?",
            "counterOwner": "Dashboard Lead",
            "counter": "Mission Control now shows adaptive-loop status, target gap, and explicit blockers/actions from both phase16 and phase17.",
            "commitment": "Keep trust surfaces explicit and fail-language first.",
            "command": "python3 -m pytest tests/test_dashboard.py tests/test_dashboard_interactions.py -q",
        },
        {
            "challenger": "Program Operator",
            "challenge": "Are we optimizing for minimum gates instead of category leadership?",
            "counterOwner": "Superhuman Team",
            "counter": (
                "Raise default objective to strong-tier and track moonshot runway continuously; block self-congratulation on release-floor only."
            ),
            "commitment": (
                f"Current strong-tier gap is {_fmt_pct(strong_gap, 3)}; treat this as primary weekly burn-down KPI."
            ),
            "command": "python3 scripts/run_superhuman_team_cycle.py",
        },
    ]


def _build_limiting_factors(snapshot: Dict[str, Any]) -> List[Dict[str, str]]:
    benchmark = snapshot.get("benchmark", {})
    phase16 = snapshot.get("phase16", {})
    phase17 = snapshot.get("phase17", {})
    phase18 = snapshot.get("phase18", {})
    phase7 = snapshot.get("phase7", {})
    dashboard_feedback = snapshot.get("dashboardFeedback", {})
    benchmark_comparison = snapshot.get("benchmarkComparison", {})

    factors: List[Dict[str, str]] = []
    strong_gap = phase16.get("strongGap")
    release_strict_status = str(phase7.get("strictStatus", "UNKNOWN")).upper()
    dashboard_status = str(dashboard_feedback.get("status", "UNKNOWN")).upper()
    dashboard_errors = dashboard_feedback.get("errors", []) or []
    phase17_min_delta = phase17.get("downsideMinSeasonEdgeDelta")
    phase17_recommendation = phase17.get("recommendation")
    skipped_identical = int(benchmark_comparison.get("skippedIdenticalRuns", 0) or 0)
    edge = benchmark.get("edge")
    strong_target = benchmark.get("strongTarget")

    if isinstance(strong_gap, (int, float)) and strong_gap > 0:
        factors.append(
            {
                "id": "LF-01",
                "factor": "Strong-tier edge gap remains open",
                "evidence": (
                    f"Current Cup edge {_fmt_pct(edge)} vs strong target {_fmt_pct(strong_target)}; "
                    f"remaining gap {_fmt_pct(strong_gap, 3)}."
                ),
                "owner": "Model Lead + superhuman-edge-goal-loop",
                "overcomePlan": (
                    "Run phase16 with feedback-tuned exploration budget and reject candidates that break strict non-regression."
                ),
                "successMetric": "phase16.summary.targetMet == true and benchmark.current.vegas.cup_target.strong_met == true",
                "verificationCommand": "python3 scripts/run_phase16_adaptive_learning_loop.py && python3 scripts/update_benchmark_metrics.py",
            }
        )

    if phase17_recommendation != "USE_PHASE17_CANDIDATE" or (
        isinstance(phase17_min_delta, (int, float)) and phase17_min_delta < 0
    ):
        factors.append(
            {
                "id": "LF-02",
                "factor": "Downside stability lane is not decisively improving tail risk",
                "evidence": (
                    f"Phase17 recommendation={phase17_recommendation or 'unknown'}; "
                    f"min-season-edge delta {_fmt_pct(phase17_min_delta, 3)}."
                ),
                "owner": "Quant Engineer + superhuman-prevention-loop",
                "overcomePlan": (
                    "Tighten phase17 downside constraints and gate promotions on positive-season-ratio + min-season-edge floors."
                ),
                "successMetric": "phase17.summary.recommendation == USE_PHASE17_CANDIDATE and phase17.summary.downsideMinSeasonEdgeDelta >= 0",
                "verificationCommand": "python3 scripts/run_phase17_downside_stability_lane.py",
            }
        )

    if dashboard_status != "PASS":
        factors.append(
            {
                "id": "LF-03",
                "factor": "Dashboard trust regressions are still escaping review",
                "evidence": (
                    f"dashboard_feedback_loop status={dashboard_status}; "
                    f"errors={len(dashboard_errors)}."
                ),
                "owner": "Dashboard Lead + superhuman-dashboard-trust-polisher",
                "overcomePlan": (
                    "Treat dashboard feedback script as hard blocker and resolve bracket coherence, scorecard sanity, and mission overflow issues before release."
                ),
                "successMetric": "reports/dashboard_feedback_loop_latest.json.status == PASS",
                "verificationCommand": "python3 scripts/run_dashboard_feedback_loop.py",
            }
        )

    if release_strict_status != "PASS":
        factors.append(
            {
                "id": "LF-04",
                "factor": "Release-truth contract is not consistently passing",
                "evidence": f"Strict release status is {release_strict_status}.",
                "owner": "Release Sheriff + superhuman-review-improver",
                "overcomePlan": (
                    "Do not allow finalization until strict release gate passes with all blocking checks green in one run context."
                ),
                "successMetric": "phase7_release_cycle_latest.shipGateStatus == PASS",
                "verificationCommand": "python3 scripts/verify_model_performance.py --require-vegas-edge --require-cup-vegas-goal",
            }
        )

    if skipped_identical > 0:
        factors.append(
            {
                "id": "LF-05",
                "factor": "Benchmark progress interpretation can be noisy across identical reruns",
                "evidence": (
                    f"Scorecard needed to skip {skipped_identical} identical run(s) to find a meaningful baseline."
                ),
                "owner": "Framework Operator",
                "overcomePlan": (
                    "Keep last-distinct comparison mode and require explanation artifacts when repeated reruns produce no metric movement."
                ),
                "successMetric": "benchmark_latest.comparison.mode == last_distinct_snapshot with non-identical deltas when changes are claimed",
                "verificationCommand": "python3 scripts/update_benchmark_metrics.py",
            }
        )

    if not factors:
        factors.append(
            {
                "id": "LF-00",
                "factor": "No active limiting factor detected by current sensors",
                "evidence": "All tracked gates currently report green.",
                "owner": "Superhuman Team",
                "overcomePlan": "Sustain current controls and run next cycle without reducing quality bars.",
                "successMetric": "All gate statuses remain PASS",
                "verificationCommand": "python3 scripts/run_superhuman_team_cycle.py",
            }
        )

    return factors


def main() -> int:
    benchmark_payload = _read_json(BENCHMARK_PATH)
    phase16_payload = _read_json(PHASE16_PATH)
    phase17_payload = _read_json(PHASE17_PATH)
    phase18_payload = _read_json(PHASE18_PATH)
    phase7_payload = _read_json(PHASE7_LATEST_PATH) if PHASE7_LATEST_PATH.exists() else _read_json(PHASE7_PATH)
    dashboard_feedback_payload = _read_json(DASHBOARD_FEEDBACK_PATH)

    benchmark = benchmark_payload.get("current", {})
    vegas = benchmark.get("vegas", {})
    target = vegas.get("cup_target", {})
    phase16_summary = phase16_payload.get("summary", {})
    phase17_summary = phase17_payload.get("summary", {})
    phase18_summary = phase18_payload.get("summary", {})

    snapshot = {
        "benchmark": {
            "edge": vegas.get("cup_relative_brier_edge"),
            "ciLow": vegas.get("cup_relative_brier_edge_ci_low"),
            "goalTier": target.get("goal_tier"),
            "strongTarget": target.get("relative_brier_improvement_strong"),
        },
        "phase16": {
            "bestEligibleName": phase16_summary.get("bestEligibleName"),
            "bestEligibleEdge": phase16_summary.get("bestEligibleEdge"),
            "strongGap": phase16_summary.get("closestGoalDistance", {}).get("edgeGapToTarget"),
            "blockers": phase16_payload.get("blockers", []),
        },
        "phase17": {
            "bestDownsideName": phase17_summary.get("bestDownsideName"),
            "downsideMinSeasonEdgeDelta": phase17_summary.get("downsideMinSeasonEdgeDelta"),
            "minSeasonEdgeDelta": phase17_summary.get("downsideMinSeasonEdgeDelta"),
            "recommendation": phase17_summary.get("recommendation"),
            "blockers": phase17_payload.get("blockers", []),
        },
        "phase18": {
            "controlMode": phase18_summary.get("controlMode"),
            "stagnationStreak": phase18_summary.get("stagnationStreak"),
            "downsideRegressionStreak": phase18_summary.get("downsideRegressionStreak"),
            "strongGap": phase18_summary.get("phase16StrongGap"),
            "blockers": phase18_payload.get("blockers", []),
        },
        "phase7": {
            "strictStatus": _resolve_release_strict_status(phase7_payload),
        },
        "dashboardFeedback": {
            "status": dashboard_feedback_payload.get("status"),
            "errors": dashboard_feedback_payload.get("errors", []),
            "warnings": dashboard_feedback_payload.get("warnings", []),
        },
        "benchmarkComparison": benchmark_payload.get("comparison", {}),
    }

    rounds = _build_grill_rounds(snapshot)
    limiting_factors = _build_limiting_factors(snapshot)

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "ACTIVE_CHALLENGE",
        "objective": "Be undeniably best NHL model + dashboard, not minimum release-floor pass",
        "snapshot": snapshot,
        "grillRounds": rounds,
        "limitingFactors": limiting_factors,
        "nonNegotiables": [
            "No promotion without strong-tier target + strict release pass in same run context.",
            "No optimistic dashboard language when blockers exist.",
            "No broad random churn without bounded hypotheses and rejection reasons.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Superhuman Grill Session (Latest)",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"Objective: **{report['objective']}**",
        "",
        "## Reality Check",
        "",
        f"- Benchmark Cup edge: `{_fmt_pct(snapshot['benchmark']['edge'])}`",
        f"- Benchmark CI low: `{_fmt_pct(snapshot['benchmark']['ciLow'])}`",
        f"- Goal tier: `{snapshot['benchmark']['goalTier']}`",
        f"- Strong target: `{_fmt_pct(snapshot['benchmark']['strongTarget'])}`",
        f"- Phase16 best eligible: `{snapshot['phase16']['bestEligibleName']}` ({_fmt_pct(snapshot['phase16']['bestEligibleEdge'])})",
        f"- Phase16 strong-gap: `{_fmt_pct(snapshot['phase16']['strongGap'], 3)}`",
        f"- Phase17 downside winner: `{snapshot['phase17']['bestDownsideName']}`",
        f"- Phase17 min-season-edge delta: `{_fmt_pct(snapshot['phase17']['downsideMinSeasonEdgeDelta'], 3)}`",
        f"- Phase18 control mode: `{snapshot['phase18']['controlMode']}`",
        f"- Phase18 streaks (stagnation/downside): `{snapshot['phase18']['stagnationStreak']}` / `{snapshot['phase18']['downsideRegressionStreak']}`",
        f"- Release strict status: `{snapshot['phase7']['strictStatus']}`",
        f"- Dashboard feedback status: `{snapshot['dashboardFeedback']['status']}`",
        "",
        "## Grill Rounds",
        "",
    ]

    for idx, row in enumerate(rounds, start=1):
        lines.extend(
            [
                f"### Round {idx}: {row['challenger']}",
                "",
                f"- Challenge: {row['challenge']}",
                f"- Counter owner: `{row['counterOwner']}`",
                f"- Counter: {row['counter']}",
                f"- Commitment: {row['commitment']}",
                f"- Command: `{row['command']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Limiting Factors and Ownership",
            "",
            "| ID | Limiting Factor | Evidence | Owner | Overcome Plan | Success Metric | Verification |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in limiting_factors:
        lines.append(
            "| {id} | {factor} | {evidence} | {owner} | {overcomePlan} | {successMetric} | `{verificationCommand}` |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Non-Negotiables",
            "",
            *[f"- {item}" for item in report["nonNegotiables"]],
            "",
        ]
    )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
