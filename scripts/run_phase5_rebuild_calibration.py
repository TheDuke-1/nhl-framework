#!/usr/bin/env python3
"""
Phase 5: rebuild + calibration diagnostics + verification gates.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.validation import ValidationFramework
from superhuman.models import EnsemblePredictor
from superhuman.model_profile import load_active_model_profile


OUT_JSON = PROJECT_ROOT / "reports" / "phase5_rebuild_calibration.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE5_REBUILD_CALIBRATION.md"


def _run(cmd: list[str]) -> Dict:
    proc = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main() -> int:
    profile = load_active_model_profile()
    data = load_training_data()
    validator = ValidationFramework()
    cv = validator.cross_validate(
        data,
        model_factory=lambda: EnsemblePredictor(
            use_neural_network=bool(profile.get("use_neural_network", True)),
            use_recency_weighting=bool(profile.get("use_recency_weighting", True)),
            use_cup_calibration=bool(profile.get("use_cup_calibration", True)),
            recency_decay_rate=float(profile.get("recency_decay_rate", 0.15)),
            cup_winner_boost=float(profile.get("cup_winner_boost", 2.0)),
            cup_ensemble_weights=profile.get("cup_ensemble_weights"),
        ),
    )

    gate_results = [
        _run(["python3", "scripts/verify_model_performance.py"]),
        _run(["python3", "scripts/update_benchmark_metrics.py"]),
        _run(["python3", "scripts/verify_benchmark_contract.py"]),
    ]

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "phase5_rebuild_calibration",
        "profile": profile,
        "crossValidation": cv.to_dict(),
        "gateResults": gate_results,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 5 Rebuild + Calibration",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Active Profile",
        "",
        f"- Profile Version: `{profile.get('profileVersion', 'unknown')}`",
        f"- Recency Decay: `{profile.get('recency_decay_rate')}`",
        f"- Cup Winner Boost: `{profile.get('cup_winner_boost')}`",
        "",
        "## Calibration Diagnostics (Cross-Validation)",
        "",
        f"- Brier Playoff: {cv.brier_score_playoff:.4f}",
        f"- Brier Cup: {cv.brier_score_cup:.4f}",
        f"- Log Loss Playoff: {cv.log_loss_playoff:.4f}",
        f"- Calibration Error (playoff): {cv.calibration_error:.4f}",
        f"- Cup Picks Correct: {cv.n_correct_cup_picks}/{cv.n_cup_events}",
        "",
        "## Verification Gates",
        "",
        "| Command | Status |",
        "|---|---|",
    ]
    for r in gate_results:
        status = "PASS" if r["returncode"] == 0 else "FAIL"
        lines.append(f"| `{r['cmd']}` | {status} |")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
