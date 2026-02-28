#!/usr/bin/env python3
"""
Run dashboard-specific feedback loop checks and publish a review artifact.

This script is intended to block "final" status when dashboard integrity or UX
trust checks fail. It focuses on:
- projected bracket coherence
- proof scorecard comparison sanity
- mission-control overflow safety controls
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

DASHBOARD_PATH = PROJECT_ROOT / "dashboard_data.json"
BENCHMARK_PATH = REPORTS_DIR / "benchmark_latest.json"
CSS_PATH = PROJECT_ROOT / "css" / "style.css"
BRACKET_JS_PATH = PROJECT_ROOT / "js" / "bracket.js"

OUT_JSON = REPORTS_DIR / "dashboard_feedback_loop_latest.json"
OUT_MD = REPORTS_DIR / "DASHBOARD_FEEDBACK_LOOP_LATEST.md"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _snapshot_signature(snapshot: Optional[Dict[str, Any]]) -> Optional[tuple]:
    if not isinstance(snapshot, dict):
        return None
    core = snapshot.get("core", {}) or {}
    quality = snapshot.get("quality", {}) or {}
    vegas = snapshot.get("vegas", {}) or {}

    def _num(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    return (
        round(_num(core.get("top1_accuracy_pct")), 6),
        round(_num(core.get("top5_accuracy_pct")), 6),
        round(_num(core.get("average_winner_rank")), 6),
        round(_num(core.get("playoff_f1")), 6),
        round(_num(quality.get("brier_playoff")), 6),
        round(_num(quality.get("brier_cup")), 6),
        round(_num(quality.get("log_loss_playoff")), 6),
        round(_num(quality.get("calibration_error")), 6),
        round(_num(vegas.get("cup_relative_brier_edge")), 6),
        round(_num(vegas.get("cup_relative_brier_edge_ci_low")), 6),
        round(_num(vegas.get("cup_relative_brier_edge_ci_high")), 6),
    )


def _pick_r1_winner(matchup: Dict[str, Any]) -> Optional[str]:
    if not isinstance(matchup, dict):
        return None
    try:
        higher_prob = float(matchup.get("higherWinProb", 0.0))
    except (TypeError, ValueError):
        return None
    return matchup.get("higher") if higher_prob >= 50.0 else matchup.get("lower")


def _pick_series_winner(matchup: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(matchup, dict):
        return None
    try:
        a_prob = float(matchup.get("teamAWinProb", 0.0))
    except (TypeError, ValueError):
        return None
    return matchup.get("teamA") if a_prob >= 50.0 else matchup.get("teamB")


def _select_matchup(matchups: List[Dict[str, Any]], a: Optional[str], b: Optional[str]) -> Optional[Dict[str, Any]]:
    if not matchups:
        return None
    if a and b:
        target = {a, b}
        for row in matchups:
            if {row.get("teamA"), row.get("teamB")} == target:
                return row
    return matchups[0]


def _check_bracket_coherence(dashboard: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    bracket = (dashboard.get("bracket") or {}).get("projected", {}) if isinstance(dashboard, dict) else {}
    coherent = bracket.get("coherentPath") if isinstance(bracket, dict) else None

    if not isinstance(bracket, dict) or not bracket:
        errors.append("Projected bracket payload is missing.")
        return {"errors": errors, "warnings": warnings}

    for conf_name in ("East", "West"):
        conf = bracket.get(conf_name) or {}
        r1 = conf.get("round1") or []
        r2 = conf.get("round2") or []
        cf = conf.get("confFinal") or []

        if len(r1) != 4:
            errors.append(f"{conf_name}: expected 4 round1 matchups, found {len(r1)}.")
            continue

        r1_winners = [_pick_r1_winner(m) for m in r1]
        slot_map = {}
        for idx, slot in enumerate(r2):
            slot_idx = int(slot.get("slot", idx))
            slot_map[slot_idx] = slot.get("matchups") or []

        slot0 = _select_matchup(slot_map.get(0, []), r1_winners[0], r1_winners[1])
        slot1 = _select_matchup(slot_map.get(1, []), r1_winners[2], r1_winners[3])
        r2_winners = [_pick_series_winner(slot0), _pick_series_winner(slot1)]
        cf_sel = _select_matchup(cf, r2_winners[0], r2_winners[1])

        if slot0 is None or slot1 is None or cf_sel is None:
            errors.append(f"{conf_name}: missing coherent round2/conf-final matchups.")
            continue

        cf_set = {cf_sel.get("teamA"), cf_sel.get("teamB")}
        r2_set = {r2_winners[0], r2_winners[1]}
        if cf_set != r2_set:
            errors.append(
                f"{conf_name}: conf-final teams {sorted(cf_set)} do not match round2 winners {sorted(r2_set)}."
            )

    if not isinstance(coherent, dict) or not coherent.get("cupFinalSelected"):
        errors.append("Projected bracket coherentPath.cupFinalSelected is missing.")

    return {"errors": errors, "warnings": warnings}


def _check_scorecard_sanity(benchmark: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    current = benchmark.get("current") if isinstance(benchmark, dict) else None
    previous = benchmark.get("previous") if isinstance(benchmark, dict) else None
    comparison = benchmark.get("comparison", {}) if isinstance(benchmark, dict) else {}
    skipped = int(comparison.get("skippedIdenticalRuns", 0) or 0)

    if not current:
        errors.append("benchmark.current is missing.")
        return {"errors": errors, "warnings": warnings}
    if not previous:
        warnings.append("benchmark.previous is missing; scorecard delta rows may be unavailable.")
        return {"errors": errors, "warnings": warnings}

    if _snapshot_signature(current) == _snapshot_signature(previous):
        if skipped <= 0:
            errors.append(
                "benchmark.current and benchmark.previous are identical without last-distinct comparison metadata."
            )
        else:
            warnings.append(
                f"benchmark.current matches immediate prior run; comparison skipped {skipped} identical run(s)."
            )
    return {"errors": errors, "warnings": warnings}


def _check_mission_overflow_controls() -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    css_text = CSS_PATH.read_text() if CSS_PATH.exists() else ""
    bracket_js = BRACKET_JS_PATH.read_text() if BRACKET_JS_PATH.exists() else ""

    required_css_tokens = [
        ".mission-trace-row code",
        "overflow-wrap: anywhere;",
        "word-break: break-word;",
        "flex-wrap: wrap;",
    ]
    for token in required_css_tokens:
        if token not in css_text:
            errors.append(f"Mission-control overflow guard missing CSS token: `{token}`")

    required_js_tokens = [
        "buildCoherentPath(",
        "coherentPath",
        "Most-Likely Path Champion",
    ]
    for token in required_js_tokens:
        if token not in bracket_js:
            errors.append(f"Bracket coherence guard missing JS token: `{token}`")

    return {"errors": errors, "warnings": warnings}


def main() -> int:
    dashboard = _read_json(DASHBOARD_PATH)
    benchmark = _read_json(BENCHMARK_PATH)

    checks = [
        ("Bracket Coherence", _check_bracket_coherence(dashboard)),
        ("Scorecard Sanity", _check_scorecard_sanity(benchmark)),
        ("Mission Overflow Guards", _check_mission_overflow_controls()),
    ]

    errors: List[str] = []
    warnings: List[str] = []
    check_rows: List[Dict[str, Any]] = []
    for name, result in checks:
        e = result.get("errors", [])
        w = result.get("warnings", [])
        errors.extend([f"{name}: {msg}" for msg in e])
        warnings.extend([f"{name}: {msg}" for msg in w])
        check_rows.append(
            {
                "name": name,
                "errorCount": len(e),
                "warningCount": len(w),
                "status": "FAIL" if e else ("WARN" if w else "PASS"),
            }
        )

    status = "PASS" if not errors else "FAIL"
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": check_rows,
        "errors": errors,
        "warnings": warnings,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Dashboard Feedback Loop (Latest)",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"Status: **{status}**",
        "",
        "## Check Summary",
        "",
        "| Check | Status | Errors | Warnings |",
        "|---|---|---:|---:|",
    ]
    for row in check_rows:
        lines.append(f"| {row['name']} | {row['status']} | {row['errorCount']} | {row['warningCount']} |")

    lines.extend(["", "## Errors", ""])
    if errors:
        lines.extend([f"- {item}" for item in errors])
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend([f"- {item}" for item in warnings])
    else:
        lines.append("- none")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
