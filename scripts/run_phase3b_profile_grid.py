#!/usr/bin/env python3
"""
Phase 3B: profile grid search using full benchmark pipeline.

Runs candidate model profiles through `scripts/update_benchmark_metrics.py`,
compares against baseline with strict non-regression core gates, and deploys
only if a candidate improves probability-quality objective.
"""

import json
import os
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.evaluation_contract import HARD_GATES
from superhuman.model_profile import DEFAULT_PROFILE_PATH, load_active_model_profile


OUT_JSON = PROJECT_ROOT / "reports" / "phase3b_profile_grid.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE3B_PROFILE_GRID.md"
BENCHMARK_LATEST = PROJECT_ROOT / "reports" / "benchmark_latest.json"


def _run_benchmark() -> None:
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "update_benchmark_metrics.py")]
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )


def _load_current_metrics() -> Dict[str, Any]:
    payload = json.loads(BENCHMARK_LATEST.read_text())
    return payload["current"]


def _write_profile(profile: Dict[str, Any]) -> None:
    DEFAULT_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DEFAULT_PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)


def _core_non_regression(base: Dict[str, Any], cand: Dict[str, Any]) -> bool:
    b = base["core"]
    c = cand["core"]
    return (
        c["top1_accuracy_pct"] >= b["top1_accuracy_pct"] - 1e-9
        and c["top5_accuracy_pct"] >= b["top5_accuracy_pct"] - 1e-9
        and c["playoff_f1"] >= b["playoff_f1"] - 1e-9
        and c["average_winner_rank"] <= b["average_winner_rank"] + 1e-9
    )


def _hard_gates_pass(metrics: Dict[str, Any]) -> bool:
    c = metrics["core"]
    return (
        c["top1_accuracy_pct"] >= HARD_GATES["top1_accuracy_pct_min"]
        and c["top5_accuracy_pct"] >= HARD_GATES["top5_accuracy_pct_min"]
        and c["playoff_f1"] >= HARD_GATES["playoff_f1_min"]
        and c["average_winner_rank"] <= HARD_GATES["average_winner_rank_max"]
    )


def _quality_score(metrics: Dict[str, Any]) -> float:
    q = metrics["quality"]
    # Lower is better on all terms.
    return (
        1.00 * float(q["brier_playoff"])
        + 0.75 * float(q["brier_cup"])
        + 0.35 * float(q["log_loss_playoff"])
        + 0.65 * float(q["calibration_error"])
    )


def _candidate_grid(active: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    base = deepcopy(active)
    candidates: List[Tuple[str, Dict[str, Any]]] = []

    candidates.append(("baseline", deepcopy(base)))

    p = deepcopy(base)
    p["cup_ensemble_weights"] = {"gradient_boosting": 0.45, "neural_network": 0.20, "monte_carlo": 0.35}
    p["profileVersion"] = "phase3b-gb-heavy"
    candidates.append(("gb-heavy", p))

    p = deepcopy(base)
    p["cup_ensemble_weights"] = {"gradient_boosting": 0.20, "neural_network": 0.20, "monte_carlo": 0.60}
    p["profileVersion"] = "phase3b-mc-heavy"
    candidates.append(("mc-heavy", p))

    p = deepcopy(base)
    p["cup_ensemble_weights"] = {"gradient_boosting": 0.25, "neural_network": 0.55, "monte_carlo": 0.20}
    p["profileVersion"] = "phase3b-nn-heavy"
    candidates.append(("nn-heavy", p))

    p = deepcopy(base)
    p["recency_decay_rate"] = 0.10
    p["profileVersion"] = "phase3b-decay-010"
    candidates.append(("decay-010", p))

    p = deepcopy(base)
    p["recency_decay_rate"] = 0.20
    p["profileVersion"] = "phase3b-decay-020"
    candidates.append(("decay-020", p))

    return candidates


def main() -> int:
    active = load_active_model_profile()
    original_profile = deepcopy(active)

    _write_profile(active)
    _run_benchmark()
    baseline_metrics = _load_current_metrics()
    baseline_quality = _quality_score(baseline_metrics)

    rows: List[Dict[str, Any]] = []
    best = {"name": "baseline", "profile": deepcopy(active), "metrics": baseline_metrics, "quality": baseline_quality}

    candidates = _candidate_grid(active)
    try:
        for name, profile in candidates:
            print(f"[phase3b] evaluating candidate: {name}", flush=True)
            _write_profile(profile)
            _run_benchmark()
            metrics = _load_current_metrics()
            q_score = _quality_score(metrics)
            row = {
                "name": name,
                "profileVersion": profile.get("profileVersion"),
                "core": metrics["core"],
                "quality": metrics["quality"],
                "qualityScore": q_score,
                "hardGatesPass": _hard_gates_pass(metrics),
                "coreNonRegression": _core_non_regression(baseline_metrics, metrics),
            }
            rows.append(row)
            if row["hardGatesPass"] and row["coreNonRegression"] and q_score < best["quality"] - 1e-9:
                best = {"name": name, "profile": deepcopy(profile), "metrics": metrics, "quality": q_score}
    finally:
        # Ensure profile always ends in a known-good state.
        print(f"[phase3b] restoring/deploying profile: {best['name']}", flush=True)
        _write_profile(best["profile"])
        _run_benchmark()

    deployed = best["name"] != "baseline"
    decision_reason = (
        f"deployed candidate `{best['name']}` with improved quality score"
        if deployed
        else "no candidate improved quality score under hard-gate + non-regression constraints"
    )

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "baseline": {
            "profileVersion": active.get("profileVersion"),
            "core": baseline_metrics["core"],
            "quality": baseline_metrics["quality"],
            "qualityScore": baseline_quality,
        },
        "candidates": rows,
        "decision": {
            "deployed": deployed,
            "name": best["name"],
            "reason": decision_reason,
            "profileVersion": best["profile"].get("profileVersion"),
            "qualityScore": best["quality"],
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 3B Profile Grid",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Baseline",
        "",
        f"- Profile Version: `{report['baseline']['profileVersion']}`",
        f"- Quality Score: `{report['baseline']['qualityScore']:.6f}`",
        f"- Core: `{report['baseline']['core']}`",
        f"- Quality: `{report['baseline']['quality']}`",
        "",
        "## Candidates",
        "",
        "| Candidate | Hard Gates | Core Non-Regression | Quality Score |",
        "|---|---|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['hardGatesPass']} | {row['coreNonRegression']} | {row['qualityScore']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Deployed: `{report['decision']['deployed']}`",
            f"- Candidate: `{report['decision']['name']}`",
            f"- Reason: {report['decision']['reason']}",
            f"- Active Profile Version: `{report['decision']['profileVersion']}`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
