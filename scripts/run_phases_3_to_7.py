#!/usr/bin/env python3
"""
Execute phases 3-7 in sequence with fail-fast behavior.
"""

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    commands = [
        ["python3", "scripts/run_phase3_weight_optimization.py"],
        ["python3", "scripts/generate_backlog_feature_templates.py"],
        ["python3", "scripts/populate_backlog_feature_proxies.py"],
        ["python3", "scripts/upgrade_backlog_true_sources.py"],
        ["python3", "scripts/audit_backlog_feature_coverage.py"],
        ["python3", "scripts/run_phase5_rebuild_calibration.py"],
        ["python3", "scripts/generate_betting_edge_report.py"],
        ["python3", "scripts/run_phase7_release_cycle.py"],
    ]

    for cmd in commands:
        proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        if proc.returncode != 0:
            return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
