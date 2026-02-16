#!/usr/bin/env python3
"""
Execute phases 8-14 sequentially and publish a consolidated status report.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = PROJECT_ROOT / "reports" / "phase8_14_execution.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE8_14_EXECUTION.md"
DEFAULT_PHASE_TIMEOUT_SECONDS = 900
MIN_PHASE_TIMEOUT_SECONDS = 60

_raw_phase_timeout = int(os.getenv("PHASE_TIMEOUT_SECONDS", str(DEFAULT_PHASE_TIMEOUT_SECONDS)))
PHASE_TIMEOUT_SECONDS = max(MIN_PHASE_TIMEOUT_SECONDS, _raw_phase_timeout)


def _clean_output(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return str(value).strip()


def _run(cmd: List[str]) -> Dict[str, object]:
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=PHASE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        duration = (datetime.now(timezone.utc) - started).total_seconds()
        return {
            "cmd": " ".join(cmd),
            "returncode": 124,
            "stdout": _clean_output(exc.stdout),
            "stderr": f"Timed out after {PHASE_TIMEOUT_SECONDS}s",
            "timedOut": True,
            "timeoutSeconds": PHASE_TIMEOUT_SECONDS,
            "durationSeconds": round(duration, 2),
        }
    duration = (datetime.now(timezone.utc) - started).total_seconds()
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": _clean_output(proc.stdout),
        "stderr": _clean_output(proc.stderr),
        "timedOut": False,
        "timeoutSeconds": PHASE_TIMEOUT_SECONDS,
        "durationSeconds": round(duration, 2),
    }


def main() -> int:
    phases = [
        {
            "phase": "Phase 8 (Vegas Truth Lock)",
            "cmd": ["python3", "scripts/run_phase8_vegas_truth_lock.py"],
        },
        {
            "phase": "Phase 9 (Cup Edge Optimization)",
            "cmd": ["python3", "scripts/run_phase9_cup_edge_optimization.py"],
        },
        {
            "phase": "Phase 10 (A/B Top-1 Recovery)",
            "cmd": ["python3", "scripts/run_phase10_ab_top1_recovery.py"],
        },
        {
            "phase": "Phase 11 (Constrained Edge Batch)",
            "cmd": ["python3", "scripts/run_phase11_constrained_edge_batch.py"],
        },
        {
            "phase": "Phase 12 (Goal Gap Closure)",
            "cmd": ["python3", "scripts/run_phase12_goal_gap_closure.py"],
        },
        {
            "phase": "Phase 13 (Eligible Feature Push)",
            "cmd": ["python3", "scripts/run_phase13_eligible_feature_push.py"],
        },
        {
            "phase": "Phase 14 (Release Contract Closure)",
            "cmd": ["python3", "scripts/update_benchmark_metrics.py"],
        },
        {
            "phase": "Phase 14 (Release Contract Closure)",
            "cmd": ["python3", "scripts/verify_benchmark_contract.py"],
        },
        {
            "phase": "Phase 14 (Release Contract Closure)",
            "cmd": ["python3", "scripts/run_phase7_release_cycle.py"],
        },
        {
            "phase": "Phase 14 (Release Contract Closure)",
            "cmd": ["python3", "scripts/grade_model_dashboard.py"],
        },
    ]

    results = []
    for step in phases:
        cmd = step["cmd"]
        phase = step["phase"]
        print(f"[phase8-14] {phase}: running {' '.join(cmd)}", flush=True)
        result = _run(cmd)
        result["phase"] = phase
        results.append(result)

    status = "PASS" if all(r["returncode"] == 0 for r in results) else "FAIL"
    failed = [f"{r['phase']}: {r['cmd']}" for r in results if r["returncode"] != 0]

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase8_14_execution",
        "status": status,
        "timeoutSeconds": PHASE_TIMEOUT_SECONDS,
        "rawTimeoutSeconds": _raw_phase_timeout,
        "minTimeoutSeconds": MIN_PHASE_TIMEOUT_SECONDS,
        "failedCommands": failed,
        "commands": results,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 8-14 Execution",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"Status: **{status}**",
        f"Per-phase timeout: `{PHASE_TIMEOUT_SECONDS}s`",
        "",
        "## Command Results",
        "",
        "| Phase | Command | Status |",
        "|---|---|---|",
    ]
    for result in results:
        lines.append(
            f"| {result['phase']} | `{result['cmd']}` | {'PASS' if result['returncode'] == 0 else 'FAIL'} |"
        )

    if failed:
        lines.extend(["", "## Failed Commands", ""])
        for cmd in failed:
            lines.append(f"- `{cmd}`")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
