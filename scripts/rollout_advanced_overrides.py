#!/usr/bin/env python3
"""
Controlled rollout for staged advanced override seasons.

Promotes one season at a time from `advanced_staging` to `advanced`, runs
benchmark update, and keeps the season only if core and quality metrics do not
regress beyond tolerance.
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_JSON = PROJECT_ROOT / "reports" / "advanced_rollout_report.json"
REPORT_MD = PROJECT_ROOT / "reports" / "ADVANCED_ROLLOUT_REPORT.md"
ADVANCED_DIR = PROJECT_ROOT / "data" / "historical" / "verified" / "advanced"
STAGING_DIR = PROJECT_ROOT / "data" / "historical" / "verified" / "advanced_staging"
BENCHMARK_LATEST = PROJECT_ROOT / "reports" / "benchmark_latest.json"
DEFAULT_UPDATE_TIMEOUT_SECONDS = 900
MIN_UPDATE_TIMEOUT_SECONDS = 60
_raw_update_timeout = int(os.getenv("ADVANCED_ROLLOUT_UPDATE_TIMEOUT_SECONDS", str(DEFAULT_UPDATE_TIMEOUT_SECONDS)))
UPDATE_TIMEOUT_SECONDS = max(MIN_UPDATE_TIMEOUT_SECONDS, _raw_update_timeout)


TOL = {
    "top1_accuracy_pct": 1e-9,           # lower is worse
    "top5_accuracy_pct": 1e-9,           # lower is worse
    "average_winner_rank": 1e-9,         # higher is worse
    "playoff_f1": 1e-9,                  # lower is worse
    "brier_playoff": 5e-4,               # higher is worse
    "brier_cup": 5e-4,                   # higher is worse
    "log_loss_playoff": 1e-3,            # higher is worse
    "calibration_error": 1e-3,           # higher is worse
}


@dataclass
class Snapshot:
    core: Dict[str, float]
    quality: Dict[str, float]


def _run_update() -> None:
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "update_benchmark_metrics.py")]
    try:
        subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=UPDATE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Benchmark refresh timed out after {UPDATE_TIMEOUT_SECONDS}s: {' '.join(cmd)}"
        ) from exc


def _load_snapshot() -> Snapshot:
    payload = json.loads(BENCHMARK_LATEST.read_text())
    current = payload["current"]
    return Snapshot(core=current["core"], quality=current["quality"])


def _is_regression(base: Snapshot, cand: Snapshot) -> tuple[bool, Dict[str, float]]:
    deltas = {
        "top1_accuracy_pct": cand.core["top1_accuracy_pct"] - base.core["top1_accuracy_pct"],
        "top5_accuracy_pct": cand.core["top5_accuracy_pct"] - base.core["top5_accuracy_pct"],
        "average_winner_rank": cand.core["average_winner_rank"] - base.core["average_winner_rank"],
        "playoff_f1": cand.core["playoff_f1"] - base.core["playoff_f1"],
        "brier_playoff": cand.quality["brier_playoff"] - base.quality["brier_playoff"],
        "brier_cup": cand.quality["brier_cup"] - base.quality["brier_cup"],
        "log_loss_playoff": cand.quality["log_loss_playoff"] - base.quality["log_loss_playoff"],
        "calibration_error": cand.quality["calibration_error"] - base.quality["calibration_error"],
    }
    bad = (
        deltas["top1_accuracy_pct"] < -TOL["top1_accuracy_pct"]
        or deltas["top5_accuracy_pct"] < -TOL["top5_accuracy_pct"]
        or deltas["average_winner_rank"] > TOL["average_winner_rank"]
        or deltas["playoff_f1"] < -TOL["playoff_f1"]
        or deltas["brier_playoff"] > TOL["brier_playoff"]
        or deltas["brier_cup"] > TOL["brier_cup"]
        or deltas["log_loss_playoff"] > TOL["log_loss_playoff"]
        or deltas["calibration_error"] > TOL["calibration_error"]
    )
    return bad, deltas


def _write_report(rows: List[Dict[str, Any]], final_snapshot: Snapshot) -> None:
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
        "finalCore": final_snapshot.core,
        "finalQuality": final_snapshot.quality,
        "acceptedSeasons": [r["season"] for r in rows if r["status"] == "accepted"],
        "rejectedSeasons": [r["season"] for r in rows if r["status"] == "rejected"],
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Advanced Override Rollout Report",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "| Season | Status | Top1 Delta | Top5 Delta | Winner Rank Delta | Playoff F1 Delta |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        d = r["deltas"]
        lines.append(
            f"| {r['season']} | {r['status']} | {d['top1_accuracy_pct']:.3f} | "
            f"{d['top5_accuracy_pct']:.3f} | {d['average_winner_rank']:.3f} | "
            f"{d['playoff_f1']:.3f} |"
        )

    REPORT_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    ADVANCED_DIR.mkdir(parents=True, exist_ok=True)
    _run_update()
    baseline = _load_snapshot()

    rows: List[Dict[str, Any]] = []
    for season in range(2011, 2024):
        src = STAGING_DIR / f"season_{season}.json"
        dst = ADVANCED_DIR / f"season_{season}.json"

        if not src.exists():
            rows.append({"season": season, "status": "missing_staging", "deltas": {k: 0.0 for k in TOL}})
            continue

        shutil.copy2(src, dst)
        _run_update()
        cand = _load_snapshot()
        regressed, deltas = _is_regression(baseline, cand)

        if regressed:
            dst.unlink(missing_ok=True)
            _run_update()
            # Keep baseline unchanged after rollback.
            rows.append({"season": season, "status": "rejected", "deltas": deltas})
        else:
            baseline = cand
            rows.append({"season": season, "status": "accepted", "deltas": deltas})

    _write_report(rows, baseline)
    print(f"Rollout report: {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
