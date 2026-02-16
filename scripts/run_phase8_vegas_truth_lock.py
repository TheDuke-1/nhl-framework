#!/usr/bin/env python3
"""
Phase 8: Historical Vegas completion + truth lock.

Validates canonical season files, verifies benchmark coverage is complete, and
writes a deterministic fingerprint so future runs can detect data drift.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_DIR = PROJECT_ROOT / "data" / "historical" / "verified"
BENCHMARK_PATH = PROJECT_ROOT / "reports" / "benchmark_latest.json"
VALIDATION_PATH = PROJECT_ROOT / "reports" / "vegas_backfill_validation.json"
OUT_JSON = PROJECT_ROOT / "reports" / "phase8_vegas_truth_lock.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE8_VEGAS_TRUTH_LOCK.md"


def _run(cmd: List[str], timeout_seconds: int | None = None) -> Dict[str, object]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return {
            "cmd": " ".join(cmd),
            "returncode": 124,
            "stdout": stdout.strip(),
            "stderr": f"Timed out after {timeout_seconds}s",
        }
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect_file_fingerprints(start_season: int, end_season: int) -> Dict[str, str]:
    fingerprints: Dict[str, str] = {}
    for season in range(start_season, end_season + 1):
        fp = VERIFIED_DIR / f"vegas_odds_{season}.csv"
        if fp.exists():
            fingerprints[str(season)] = _sha256(fp)
    return fingerprints


def _lock_hash(fingerprints: Dict[str, str]) -> str:
    h = hashlib.sha256()
    for season in sorted(fingerprints.keys()):
        h.update(season.encode("utf-8"))
        h.update(fingerprints[season].encode("utf-8"))
    return h.hexdigest()


def main() -> int:
    start_season, end_season = 2010, 2025
    skip_benchmark_refresh = os.getenv("PHASE8_SKIP_BENCHMARK_REFRESH", "0") == "1"
    benchmark_timeout_seconds = int(os.getenv("PHASE8_BENCHMARK_TIMEOUT_SECONDS", "900"))

    commands = [
        _run(
            [
                "python3",
                "scripts/repair_historical_vegas_odds.py",
                "--start-season",
                str(start_season),
                "--end-season",
                str(end_season),
            ]
        ),
        _run(
            [
                "python3",
                "scripts/validate_historical_vegas.py",
                "--start-season",
                str(start_season),
                "--end-season",
                str(end_season),
            ]
        ),
    ]
    if skip_benchmark_refresh:
        commands.append(
            {
                "cmd": "python3 scripts/update_benchmark_metrics.py",
                "returncode": 0,
                "stdout": "Skipped benchmark refresh (PHASE8_SKIP_BENCHMARK_REFRESH=1)",
                "stderr": "",
            }
        )
    else:
        commands.append(
            _run(
                ["python3", "scripts/update_benchmark_metrics.py"],
                timeout_seconds=benchmark_timeout_seconds,
            )
        )

    validation = {}
    if VALIDATION_PATH.exists():
        validation = json.loads(VALIDATION_PATH.read_text())

    benchmark = {}
    if BENCHMARK_PATH.exists():
        benchmark = json.loads(BENCHMARK_PATH.read_text()).get("current", {})

    vegas = benchmark.get("vegas", {})
    missing = vegas.get("seasons_missing", [])
    available = bool(vegas.get("available", False))
    fingerprints = _collect_file_fingerprints(start_season, end_season)
    expected = end_season - start_season + 1
    fingerprint_complete = len(fingerprints) == expected

    status = "PASS"
    reasons: List[str] = []
    if commands[0]["returncode"] != 0:
        status = "FAIL"
        reasons.append("historical Vegas repair failed")
    if commands[1]["returncode"] != 0:
        status = "FAIL"
        reasons.append("historical Vegas validation failed")
    if commands[2]["returncode"] != 0:
        status = "FAIL"
        reasons.append("benchmark refresh failed")
    if not available:
        status = "FAIL"
        reasons.append("Vegas comparison unavailable in benchmark")
    if missing:
        status = "FAIL"
        reasons.append(f"benchmark missing Vegas seasons: {missing}")
    if not fingerprint_complete:
        status = "FAIL"
        reasons.append(
            f"truth lock fingerprint missing files ({len(fingerprints)}/{expected})"
        )

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase8_vegas_truth_lock",
        "status": status,
        "reasons": reasons,
        "range": {"startSeason": start_season, "endSeason": end_season},
        "validation": {
            "okCount": validation.get("okCount"),
            "missingCount": validation.get("missingCount"),
            "invalidCount": validation.get("invalidCount"),
        },
        "benchmarkVegas": {
            "available": available,
            "seasonsAvailable": vegas.get("seasons_available", []),
            "seasonsMissing": missing,
        },
        "truthLock": {
            "filesFingerprinted": len(fingerprints),
            "expectedFiles": expected,
            "fingerprints": fingerprints,
            "lockHash": _lock_hash(fingerprints),
        },
        "commands": commands,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 8 Vegas Truth Lock",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"Status: **{status}**",
        "",
        f"- Validation status: `{validation.get('okCount', 0)}` OK, "
        f"`{validation.get('missingCount', 0)}` missing, "
        f"`{validation.get('invalidCount', 0)}` invalid",
        f"- Benchmark vegas available: `{available}`",
        f"- Benchmark missing seasons: `{missing}`",
        (
            f"- Truth lock fingerprint: `{len(fingerprints)}/{expected}` files, "
            f"`{report['truthLock']['lockHash'][:16]}...`"
        ),
        "",
        "## Command Status",
        "",
        "| Command | Status |",
        "|---|---|",
    ]

    for cmd in commands:
        lines.append(
            f"| `{cmd['cmd']}` | {'PASS' if cmd['returncode'] == 0 else 'FAIL'} |"
        )

    if reasons:
        lines.extend(["", "## Fail Reasons", ""])
        for reason in reasons:
            lines.append(f"- {reason}")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
