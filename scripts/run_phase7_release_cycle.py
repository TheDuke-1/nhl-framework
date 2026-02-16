#!/usr/bin/env python3
"""
Phase 7: promotion gates and continuous release cycle.

Dual-track release truth:
- strict: ship gate (warnings are fatal)
- advisory: local telemetry (warnings are non-fatal)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

# Backward-compatible legacy outputs
OUT_JSON = REPORTS_DIR / "phase7_release_cycle.json"
OUT_MD = REPORTS_DIR / "PHASE7_RELEASE_CYCLE.md"

# Dual-track outputs
OUT_STRICT_JSON = REPORTS_DIR / "phase7_release_cycle_strict.json"
OUT_ADVISORY_JSON = REPORTS_DIR / "phase7_release_cycle_advisory.json"
OUT_LATEST_JSON = REPORTS_DIR / "phase7_release_cycle_latest.json"
OUT_STRICT_MD = REPORTS_DIR / "PHASE7_RELEASE_CYCLE_STRICT.md"
OUT_ADVISORY_MD = REPORTS_DIR / "PHASE7_RELEASE_CYCLE_ADVISORY.md"
REFRESH_HEARTBEAT_PATH = REPORTS_DIR / "data_refresh_heartbeat.json"

BENCHMARK_LATEST = REPORTS_DIR / "benchmark_latest.json"

DEFAULT_TIMEOUT_SECONDS = 1800
MIN_TIMEOUT_SECONDS = 300
DEFAULT_REFRESH_TIMEOUT_SECONDS = 600

_raw_timeout = int(os.getenv("PHASE7_COMMAND_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
COMMAND_TIMEOUT_SECONDS = max(MIN_TIMEOUT_SECONDS, _raw_timeout)
VERIFY_MODEL_TIMEOUT_SECONDS = max(
    COMMAND_TIMEOUT_SECONDS,
    int(os.getenv("PHASE7_VERIFY_MODEL_TIMEOUT_SECONDS", str(COMMAND_TIMEOUT_SECONDS))),
)
REFRESH_TIMEOUT_SECONDS = max(
    MIN_TIMEOUT_SECONDS,
    int(os.getenv("PHASE7_REFRESH_TIMEOUT_SECONDS", str(DEFAULT_REFRESH_TIMEOUT_SECONDS))),
)

ALLOW_DATA_WARNINGS_ENV = os.getenv("PHASE7_ALLOW_DATA_WARNINGS")
SKIP_AUTO_REFRESH_ENV = os.getenv("PHASE7_SKIP_AUTO_REFRESH", "0") == "1"


def _run(cmd: List[str], timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
    effective_timeout = int(timeout_seconds or COMMAND_TIMEOUT_SECONDS)
    started = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=effective_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        duration = (datetime.now(timezone.utc) - started).total_seconds()
        return {
            "cmd": " ".join(cmd),
            "returncode": 124,
            "stdout": stdout.strip(),
            "stderr": f"Timed out after {effective_timeout}s",
            "timedOut": True,
            "timeoutSeconds": effective_timeout,
            "durationSeconds": round(duration, 2),
        }

    duration = (datetime.now(timezone.utc) - started).total_seconds()
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "timedOut": False,
        "timeoutSeconds": effective_timeout,
        "durationSeconds": round(duration, 2),
    }


def _extract_failure_reason(cmd: str, combined_output: str, stderr: str) -> str:
    lines = [line.strip() for line in combined_output.splitlines() if line.strip()]

    health_line = next((line for line in lines if line.startswith("HEALTH_FAIL:")), "")
    if health_line:
        return health_line.replace("HEALTH_FAIL:", "").strip()

    fail_line = next((line for line in lines if line.startswith("FAIL:")), "")
    if fail_line:
        return fail_line.replace("FAIL:", "").strip()

    if "scripts/validate_data.py" in cmd:
        stale_lines = [line.lstrip("⚠️ ").strip() for line in lines if "Data is" in line and "old" in line]
        if stale_lines:
            return stale_lines[0]
        strict_line = next((line for line in lines if "Strict mode treats warnings as failures" in line), "")
        if strict_line:
            return strict_line.lstrip("⚠️ ").strip()
        validation_line = next((line for line in lines if "VALIDATION FAILED" in line), "")
        if validation_line:
            return validation_line.lstrip("❌ ").strip()

    first_stderr = next((line for line in stderr.splitlines() if line.strip()), "")
    if first_stderr:
        return first_stderr.strip()

    if lines:
        return lines[0]
    return "command failed"


def _load_benchmark_current_snapshot() -> Dict[str, Any]:
    if not BENCHMARK_LATEST.exists():
        return {}
    try:
        with open(BENCHMARK_LATEST) as f:
            benchmark = json.load(f)
        return benchmark.get("current", {})
    except Exception:
        return {}


def _load_freshness_report() -> List[Dict[str, Any]]:
    scripts_dir = PROJECT_ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from utils import get_data_freshness_report  # type: ignore

        report = get_data_freshness_report()
        return report if isinstance(report, list) else []
    except Exception:
        return []


def _summarize_stale_sources(report: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    stale = []
    for row in report:
        status = str(row.get("status", ""))
        if "STALE" not in status and "MISSING" not in status:
            continue
        stale.append(
            {
                "file": row.get("file"),
                "status": status,
                "ageHours": row.get("age_hours"),
                "thresholdHours": row.get("threshold_hours"),
            }
        )
    return stale


def _run_refresh_automation(enabled: bool) -> Dict[str, Any]:
    before_report = _load_freshness_report()
    stale_before = _summarize_stale_sources(before_report)

    refresh_meta: Dict[str, Any] = {
        "enabled": enabled,
        "attempted": False,
        "before": stale_before,
        "after": stale_before,
        "command": None,
        "heartbeat": _load_json(REFRESH_HEARTBEAT_PATH),
    }
    if not enabled or not stale_before:
        return refresh_meta

    refresh_meta["attempted"] = True
    refresh_meta["command"] = _run(["python3", "scripts/refresh_data.py"], timeout_seconds=REFRESH_TIMEOUT_SECONDS)
    after_report = _load_freshness_report()
    refresh_meta["after"] = _summarize_stale_sources(after_report)
    refresh_meta["heartbeat"] = _load_json(REFRESH_HEARTBEAT_PATH)
    return refresh_meta


def _build_refresh_health_gate_run(mode: str, refresh_meta: Dict[str, Any]) -> Dict[str, Any]:
    if mode != "strict":
        return {
            "cmd": "phase7.refresh_health_gate",
            "returncode": 0,
            "stdout": "HEALTH_PASS: advisory mode does not enforce strict refresh health gate",
            "stderr": "",
            "timedOut": False,
            "timeoutSeconds": 0,
            "durationSeconds": 0.0,
        }

    heartbeat = refresh_meta.get("heartbeat")
    if not isinstance(heartbeat, dict):
        return {
            "cmd": "phase7.refresh_health_gate",
            "returncode": 1,
            "stdout": "",
            "stderr": "HEALTH_FAIL: missing refresh heartbeat artifact",
            "timedOut": False,
            "timeoutSeconds": 0,
            "durationSeconds": 0.0,
        }

    overall = heartbeat.get("overall") or {}
    if bool(overall.get("criticalHealthy")):
        return {
            "cmd": "phase7.refresh_health_gate",
            "returncode": 0,
            "stdout": "HEALTH_PASS: critical sources healthy (or expected static during scheduled break)",
            "stderr": "",
            "timedOut": False,
            "timeoutSeconds": 0,
            "durationSeconds": 0.0,
        }

    sources = heartbeat.get("sources") or {}
    critical_failures = []
    for name, row in sources.items():
        if not isinstance(row, dict):
            continue
        if not bool(row.get("critical")):
            continue
        health = str(row.get("health", "")).lower()
        if health in {"healthy", "expected_static"}:
            continue
        message = str(row.get("message", "")).strip()
        critical_failures.append(f"{name}={health or 'unknown'} ({message or 'no message'})")

    details = "; ".join(critical_failures) if critical_failures else "critical source health check failed"
    return {
        "cmd": "phase7.refresh_health_gate",
        "returncode": 1,
        "stdout": "",
        "stderr": f"HEALTH_FAIL: {details}",
        "timedOut": False,
        "timeoutSeconds": 0,
        "durationSeconds": 0.0,
    }


def _build_skipped_run(cmd: str, reason: str) -> Dict[str, Any]:
    return {
        "cmd": cmd,
        "returncode": 0,
        "stdout": reason,
        "stderr": "",
        "timedOut": False,
        "timeoutSeconds": 0,
        "durationSeconds": 0.0,
    }


def _build_blocking_reasons(runs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    reasons = []
    for run in runs:
        if int(run.get("returncode", 1)) == 0:
            continue
        combined_output = "\n".join(
            [str(run.get("stdout", "")).strip(), str(run.get("stderr", "")).strip()]
        ).strip()
        reason = _extract_failure_reason(str(run.get("cmd", "")), combined_output, str(run.get("stderr", "")))
        reasons.append({"cmd": str(run.get("cmd", "")), "reason": reason})
    return reasons


def _extract_data_warnings(validation_run: Dict[str, Any], allow_warnings: bool) -> List[str]:
    if not allow_warnings:
        return []
    if not isinstance(validation_run.get("stdout"), str):
        return []
    return [line.strip() for line in validation_run["stdout"].splitlines() if "⚠️" in line]


def _write_report_markdown(path: Path, title: str, report: Dict[str, Any]) -> None:
    core = report.get("benchmarkSnapshot", {}).get("core", {})
    runs = report.get("commands", [])
    blocking = report.get("blockingReasons", [])
    refresh = report.get("refreshAutomation", {})

    lines = [
        f"# {title}",
        "",
        f"Generated: `{report.get('generatedAt')}`",
        f"Mode: `{report.get('mode')}`",
        f"Truth Tier: `{report.get('truthTier')}`",
        f"Overall Status: `{report.get('status')}`",
        f"Fail-fast triggered: `{report.get('failFastTriggered')}`",
        f"Data warning policy: `{'ALLOW_WARNINGS' if report.get('dataValidationPolicy', {}).get('allowWarnings') else 'STRICT'}`",
        "",
        "## Refresh Automation",
        "",
        f"- Enabled: `{refresh.get('enabled')}`",
        f"- Attempted: `{refresh.get('attempted')}`",
        f"- Stale/Missing before: `{len(refresh.get('before', []))}`",
        f"- Stale/Missing after: `{len(refresh.get('after', []))}`",
    ]

    refresh_cmd = refresh.get("command") or {}
    if refresh_cmd:
        lines += [
            f"- Refresh command: `{refresh_cmd.get('cmd')}`",
            f"- Refresh status: `{'PASS' if int(refresh_cmd.get('returncode', 1)) == 0 else 'FAIL'}`",
        ]

    lines += [
        "",
        "## Gate Results",
        "",
        "| Command | Status |",
        "|---|---|",
    ]
    for run in runs:
        lines.append(f"| `{run.get('cmd')}` | {'PASS' if int(run.get('returncode', 1)) == 0 else 'FAIL'} |")

    if blocking:
        lines += ["", "## Blocking Reasons", ""]
        for row in blocking:
            lines.append(f"- `{row.get('cmd')}` -> {row.get('reason')}")

    warnings = report.get("advisories", {}).get("dataWarnings", [])
    if warnings:
        lines += ["", "## Data Freshness Advisories", ""]
        for row in warnings:
            lines.append(f"- {row}")

    lines += [
        "",
        "## Current Benchmark Snapshot",
        "",
        f"- Cup Top-1: {core.get('top1_accuracy_pct', 'n/a')}",
        f"- Cup Top-5: {core.get('top5_accuracy_pct', 'n/a')}",
        f"- Average Winner Rank: {core.get('average_winner_rank', 'n/a')}",
        f"- Playoff F1: {core.get('playoff_f1', 'n/a')}",
    ]
    path.write_text("\n".join(lines) + "\n")


def _write_mode_outputs(mode: str, report: Dict[str, Any], out_override: Optional[Path] = None) -> Dict[str, str]:
    if mode == "strict":
        json_path = OUT_STRICT_JSON
        md_path = OUT_STRICT_MD
        title = "Phase 7 Release Cycle (Strict)"
    else:
        json_path = OUT_ADVISORY_JSON
        md_path = OUT_ADVISORY_MD
        title = "Phase 7 Release Cycle (Advisory)"

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n")
    _write_report_markdown(md_path, title, report)

    if out_override:
        out_override.parent.mkdir(parents=True, exist_ok=True)
        out_override.write_text(json.dumps(report, indent=2) + "\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    if out_override:
        print(f"Wrote {out_override}")
    return {"json": str(json_path), "md": str(md_path)}


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _build_latest_report(strict_report: Optional[Dict[str, Any]], advisory_report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    ship_gate_status = str((strict_report or {}).get("status", "UNKNOWN")).upper() if strict_report else "UNKNOWN"
    local_advisory_status = (
        str((advisory_report or {}).get("status", "UNKNOWN")).upper() if advisory_report else "UNKNOWN"
    )
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "shipGateStatus": ship_gate_status,
        "localAdvisoryStatus": local_advisory_status,
        "strict": strict_report or {},
        "advisory": advisory_report or {},
    }


def _execute_mode(mode: str, allow_warnings: bool, enable_refresh: bool) -> Dict[str, Any]:
    data_validation_cmd = [
        "python3",
        "scripts/validate_data.py",
        "--allow-warnings" if allow_warnings else "--strict",
        "--break-aware",
    ]

    refresh_meta = _run_refresh_automation(enable_refresh and mode == "strict")

    runs: List[Dict[str, Any]] = []
    refresh_gate_run = _build_refresh_health_gate_run(mode, refresh_meta)
    runs.append(refresh_gate_run)
    precheck_run = _run(data_validation_cmd)
    runs.append(precheck_run)

    fail_fast = mode == "strict" and (
        int(refresh_gate_run.get("returncode", 1)) != 0 or int(precheck_run.get("returncode", 1)) != 0
    )
    if not fail_fast:
        runs.extend(
            [
                _run(
                    [
                        "python3",
                        "-W",
                        "error::RuntimeWarning",
                        "scripts/verify_model_performance.py",
                        "--require-vegas-edge",
                        "--require-cup-vegas-goal",
                    ],
                    timeout_seconds=VERIFY_MODEL_TIMEOUT_SECONDS,
                ),
                _run(["python3", "scripts/verify_benchmark_contract.py"]),
                _run(["python3", "scripts/grade_model_dashboard.py"]),
                _run(["python3", "scripts/generate_betting_edge_report.py"]),
            ]
        )

    if fail_fast:
        benchmark_refresh = _build_skipped_run(
            "python3 scripts/update_benchmark_metrics.py",
            "SKIPPED: fail-fast triggered before full gate pipeline",
        )
    else:
        benchmark_refresh = _run(["python3", "scripts/update_benchmark_metrics.py"])
    status = "PASS" if all(int(r.get("returncode", 1)) == 0 for r in runs) else "FAIL"

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "truthTier": "ship_gate" if mode == "strict" else "local_advisory",
        "status": status,
        "failFastTriggered": fail_fast,
        "timeoutPolicy": {
            "defaultSeconds": COMMAND_TIMEOUT_SECONDS,
            "verifyModelSeconds": VERIFY_MODEL_TIMEOUT_SECONDS,
            "refreshSeconds": REFRESH_TIMEOUT_SECONDS,
            "rawEnvSeconds": _raw_timeout,
            "minSeconds": MIN_TIMEOUT_SECONDS,
        },
        "dataValidationPolicy": {
            "strictWarningsAreFatal": not allow_warnings,
            "allowWarnings": allow_warnings,
            "command": " ".join(data_validation_cmd),
        },
        "refreshAutomation": refresh_meta,
        "advisories": {
            "dataWarnings": _extract_data_warnings(precheck_run, allow_warnings),
        },
        "commands": runs,
        "observabilityCommands": [benchmark_refresh],
        "blockingReasons": _build_blocking_reasons(runs),
        "benchmarkSnapshot": _load_benchmark_current_snapshot(),
    }
    return report


def _resolve_requested_mode(explicit_mode: Optional[str]) -> str:
    if explicit_mode:
        return explicit_mode
    if ALLOW_DATA_WARNINGS_ENV is not None:
        return "advisory" if ALLOW_DATA_WARNINGS_ENV == "1" else "strict"
    return "both"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 7 release cycle gates with strict/advisory modes.")
    parser.add_argument(
        "--mode",
        choices=["strict", "advisory", "both"],
        default=None,
        help="Execution mode. Default is env-compatible fallback; otherwise dual-track both.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional JSON output override path for the selected single mode.",
    )
    parser.add_argument(
        "--skip-refresh",
        action="store_true",
        help="Disable pre-gate auto-refresh attempts for strict mode.",
    )
    args = parser.parse_args()

    mode = _resolve_requested_mode(args.mode)
    enable_refresh = not args.skip_refresh and not SKIP_AUTO_REFRESH_ENV

    strict_report: Optional[Dict[str, Any]] = None
    advisory_report: Optional[Dict[str, Any]] = None

    if mode in {"strict", "both"}:
        strict_report = _execute_mode(mode="strict", allow_warnings=False, enable_refresh=enable_refresh)
        out_override = Path(args.out).resolve() if (args.out and mode == "strict") else None
        _write_mode_outputs("strict", strict_report, out_override=out_override)

    if mode in {"advisory", "both"}:
        advisory_report = _execute_mode(mode="advisory", allow_warnings=True, enable_refresh=False)
        out_override = Path(args.out).resolve() if (args.out and mode == "advisory") else None
        _write_mode_outputs("advisory", advisory_report, out_override=out_override)

    # Keep latest index stable even when running a single mode.
    if strict_report is None:
        strict_report = _load_json(OUT_STRICT_JSON)
    if advisory_report is None:
        advisory_report = _load_json(OUT_ADVISORY_JSON)

    latest_report = _build_latest_report(strict_report, advisory_report)
    OUT_LATEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_LATEST_JSON.write_text(json.dumps(latest_report, indent=2) + "\n")
    print(f"Wrote {OUT_LATEST_JSON}")

    # Backward-compatibility alias: legacy phase7_release_cycle.* maps to ship-gate strict truth.
    primary_report = strict_report or advisory_report or {"status": "FAIL"}
    OUT_JSON.write_text(json.dumps(primary_report, indent=2) + "\n")
    _write_report_markdown(OUT_MD, "Phase 7 Release Cycle", primary_report)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")

    ship_gate_status = str((strict_report or primary_report).get("status", "FAIL")).upper()
    return 0 if ship_gate_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
