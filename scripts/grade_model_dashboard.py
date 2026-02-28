#!/usr/bin/env python3
"""
Generate current model and dashboard grade with explicit rubric.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_PATH = PROJECT_ROOT / "reports" / "benchmark_latest.json"
PHASE7_LATEST_PATH = PROJECT_ROOT / "reports" / "phase7_release_cycle_latest.json"
PHASE7_PATH = PROJECT_ROOT / "reports" / "phase7_release_cycle.json"
DASHBOARD_PATH = PROJECT_ROOT / "dashboard_data.json"
OUT_JSON = PROJECT_ROOT / "reports" / "current_model_dashboard_grade.json"
OUT_MD = PROJECT_ROOT / "reports" / "CURRENT_MODEL_DASHBOARD_GRADE.md"
FRESHNESS_WINDOW_HOURS = 72.0


def _letter(score: float) -> str:
    if score >= 97:
        return "A+"
    if score >= 93:
        return "A"
    if score >= 90:
        return "A-"
    if score >= 87:
        return "B+"
    if score >= 83:
        return "B"
    if score >= 80:
        return "B-"
    if score >= 77:
        return "C+"
    if score >= 73:
        return "C"
    if score >= 70:
        return "C-"
    if score >= 67:
        return "D+"
    if score >= 63:
        return "D"
    return "F"


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _score_accuracy(core: Dict) -> Tuple[float, Dict]:
    top1 = float(core.get("top1_accuracy_pct", 0.0))
    top5 = float(core.get("top5_accuracy_pct", 0.0))
    rank = float(core.get("average_winner_rank", 99.0))
    f1 = float(core.get("playoff_f1", 0.0))

    s_top1 = _clamp01(top1 / 35.0)
    s_top5 = _clamp01(top5 / 60.0)
    s_rank = _clamp01((10.0 - rank) / 6.0)
    s_f1 = _clamp01((f1 - 0.80) / 0.18)
    score = 100.0 * (0.35 * s_top1 + 0.25 * s_top5 + 0.20 * s_rank + 0.20 * s_f1)
    detail = {"top1": top1, "top5": top5, "winner_rank": rank, "playoff_f1": f1}
    return round(score, 1), detail


def _score_probability_quality(quality: Dict) -> Tuple[float, Dict]:
    brier_p = float(quality.get("brier_playoff", 1.0))
    brier_c = float(quality.get("brier_cup", 1.0))
    log_loss = float(quality.get("log_loss_playoff", 10.0))
    ece = float(quality.get("calibration_error", 1.0))

    s_bp = _clamp01((0.12 - brier_p) / 0.06)
    s_bc = _clamp01((0.06 - brier_c) / 0.04)
    s_ll = _clamp01((0.35 - log_loss) / 0.20)
    s_ece = _clamp01((0.05 - ece) / 0.04)
    score = 100.0 * (0.35 * s_bp + 0.25 * s_bc + 0.20 * s_ll + 0.20 * s_ece)
    detail = {"brier_playoff": brier_p, "brier_cup": brier_c, "log_loss_playoff": log_loss, "calibration_error": ece}
    return round(score, 1), detail


def _score_coverage(cov: Dict) -> Tuple[float, Dict]:
    season_ratio = float(cov.get("advanced_accepted_season_ratio", 0.0))
    team_ratio = float(cov.get("advanced_accepted_team_ratio", 0.0))
    raw_ratio = float(cov.get("advanced_raw_team_ratio", 0.0))
    score = 100.0 * (0.40 * season_ratio + 0.40 * team_ratio + 0.20 * raw_ratio)
    return round(score, 1), {
        "accepted_season_ratio": season_ratio,
        "accepted_team_ratio": team_ratio,
        "raw_team_ratio": raw_ratio,
    }


def _score_operations(phase7: Dict, benchmark_current: Dict) -> Tuple[float, Dict]:
    status = phase7.get("status", "FAIL")
    gate_runs = phase7.get("commands", [])
    gate_pass_ratio = 0.0
    if gate_runs:
        gate_pass_ratio = sum(1 for r in gate_runs if int(r.get("returncode", 1)) == 0) / len(gate_runs)
    leakage_free = bool(benchmark_current.get("evaluationContract", {}).get("leakageFree", False))

    score = 100.0 * (0.55 * (1.0 if status == "PASS" else 0.0) + 0.30 * gate_pass_ratio + 0.15 * (1.0 if leakage_free else 0.0))
    return round(score, 1), {
        "release_cycle_status": status,
        "gate_pass_ratio": round(gate_pass_ratio, 3),
        "leakage_free": leakage_free,
    }


def _score_market_readiness(benchmark_current: Dict) -> Tuple[float, Dict]:
    has_vegas = bool(benchmark_current.get("vegas", {}).get("available", False))
    score = 85.0 if has_vegas else 62.0
    return score, {"has_historical_vegas_benchmark": has_vegas}


def _resolve_ship_gate_phase7(phase7_payload: Dict) -> Dict:
    if not isinstance(phase7_payload, dict):
        return {"status": "FAIL", "commands": []}
    strict = phase7_payload.get("strict")
    if isinstance(strict, dict):
        resolved = dict(strict)
        resolved["status"] = str(phase7_payload.get("shipGateStatus") or strict.get("status") or "FAIL").upper()
        return resolved
    resolved = dict(phase7_payload)
    resolved["status"] = str(phase7_payload.get("status") or "FAIL").upper()
    return resolved


def _score_dashboard(dashboard: Dict, phase7: Dict, benchmark_current: Dict) -> Tuple[float, Dict]:
    teams = dashboard.get("teams", [])
    required_sections = ["playoffPicture", "bracket", "backtest", "glossary", "featureWeights", "roundAdvancement"]
    present = sum(1 for k in required_sections if dashboard.get(k))
    section_ratio = present / len(required_sections)

    team_score = 1.0 if len(teams) == 32 else max(0.0, len(teams) / 32.0)

    generated_ts = dashboard.get("meta", {}).get("generated")
    freshness = 0.5
    if generated_ts:
        try:
            ts = datetime.fromisoformat(generated_ts)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds() / 3600.0
            freshness = _clamp01((FRESHNESS_WINDOW_HOURS - age_hours) / FRESHNESS_WINDOW_HOURS)
        except Exception:
            freshness = 0.5

    release_status = str(phase7.get("status", "FAIL")).upper()
    release_alignment = 1.0 if release_status == "PASS" else 0.0
    cup_target = benchmark_current.get("vegas", {}).get("cup_target", {}) if isinstance(benchmark_current, dict) else {}
    cup_goal_met = bool(cup_target.get("goal_met", False))
    strong_goal_present = "strong_met" in cup_target
    strong_goal_met = bool(cup_target.get("strong_met", False))
    goal_alignment = 1.0 if cup_goal_met else 0.0

    edge_research = dashboard.get("edgeResearch", {}) if isinstance(dashboard, dict) else {}
    phase16_blockers = (edge_research.get("phase16") or {}).get("blockers", [])
    phase17_blockers = (edge_research.get("phase17") or {}).get("blockers", [])
    phase18_blockers = (edge_research.get("phase18") or {}).get("blockers", [])
    edge_blocker_count = len(phase16_blockers) + len(phase17_blockers) + len(phase18_blockers)

    projected = (dashboard.get("bracket") or {}).get("projected", {})
    coherent_path = projected.get("coherentPath") if isinstance(projected, dict) else None
    coherent_path_available = bool(isinstance(coherent_path, dict) and coherent_path.get("cupFinalSelected"))

    score = 100.0 * (
        0.20 * section_ratio
        + 0.15 * team_score
        + 0.15 * freshness
        + 0.30 * release_alignment
        + 0.20 * goal_alignment
    )

    # Prevent inflated dashboard grades when release trust is not achieved.
    cap_reasons = []
    if release_status != "PASS":
        score = min(score, 82.0)
        cap_reasons.append("release_cycle_not_pass")
    if not cup_goal_met:
        score = min(score, 86.0)
        cap_reasons.append("cup_goal_not_met")
    if strong_goal_present and not strong_goal_met:
        score = min(score, 89.0)
        cap_reasons.append("strong_tier_not_met")
    if edge_blocker_count > 0:
        score = min(score, 88.0)
        cap_reasons.append("active_edge_research_blockers")
    if not coherent_path_available:
        score = min(score, 90.0)
        cap_reasons.append("coherent_bracket_path_missing")

    return round(score, 1), {
        "team_count": len(teams),
        "section_ratio": round(section_ratio, 3),
        "freshness_score": round(freshness, 3),
        "release_status": release_status,
        "cup_goal_met": cup_goal_met,
        "strong_goal_met": strong_goal_met if strong_goal_present else None,
        "edge_blocker_count": edge_blocker_count,
        "coherent_bracket_path_available": coherent_path_available,
        "capped": bool(cap_reasons),
        "cap_reasons": cap_reasons,
    }


def main() -> int:
    with open(BENCHMARK_PATH) as f:
        benchmark = json.load(f)
    if PHASE7_LATEST_PATH.exists():
        with open(PHASE7_LATEST_PATH) as f:
            phase7_raw = json.load(f)
    else:
        with open(PHASE7_PATH) as f:
            phase7_raw = json.load(f)
    phase7 = _resolve_ship_gate_phase7(phase7_raw)
    with open(DASHBOARD_PATH) as f:
        dashboard = json.load(f)

    current = benchmark.get("current", {})
    core = current.get("core", {})
    quality = current.get("quality", {})
    coverage = current.get("dataCoverage", {})

    acc_score, acc_detail = _score_accuracy(core)
    prob_score, prob_detail = _score_probability_quality(quality)
    cov_score, cov_detail = _score_coverage(coverage)
    ops_score, ops_detail = _score_operations(phase7, current)
    market_score, market_detail = _score_market_readiness(current)
    dash_score, dash_detail = _score_dashboard(dashboard, phase7, current)
    release_status = ops_detail["release_cycle_status"]
    gate_pass_ratio = ops_detail["gate_pass_ratio"]

    model_numeric = round(
        0.35 * acc_score
        + 0.25 * prob_score
        + 0.15 * cov_score
        + 0.15 * ops_score
        + 0.10 * market_score,
        1,
    )
    model_grade = _letter(model_numeric)
    dashboard_grade = _letter(dash_score)
    overall_numeric = round(0.70 * model_numeric + 0.30 * dash_score, 1)
    overall_grade = _letter(overall_numeric)

    market_note = (
        "- Market-readiness credit earned: historical Vegas benchmark is present and scored."
        if market_detail["has_historical_vegas_benchmark"]
        else "- Grade is held back by missing historical Vegas benchmark data in-repo (market-readiness penalty)."
    )
    process_note = (
        "- Process rigor is high: strict walk-forward leakage-free contract and release gates are passing."
        if release_status == "PASS"
        else f"- Process rigor has a release mismatch: release cycle is `{release_status}` with gate pass ratio `{gate_pass_ratio}`."
    )

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "model": {
            "numeric": model_numeric,
            "grade": model_grade,
            "components": {
                "accuracy": {"score": acc_score, "detail": acc_detail},
                "probability_quality": {"score": prob_score, "detail": prob_detail},
                "coverage": {"score": cov_score, "detail": cov_detail},
                "operations": {"score": ops_score, "detail": ops_detail},
                "market_readiness": {"score": market_score, "detail": market_detail},
            },
        },
        "dashboard": {
            "numeric": dash_score,
            "grade": dashboard_grade,
            "detail": dash_detail,
        },
        "overall": {"numeric": overall_numeric, "grade": overall_grade},
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Current Model + Dashboard Grade",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Grades",
        "",
        f"- Model Grade: **{model_grade}** ({model_numeric}/100)",
        f"- Dashboard Grade: **{dashboard_grade}** ({dash_score}/100)",
        f"- Overall Grade: **{overall_grade}** ({overall_numeric}/100)",
        "",
        "## Model Component Scores",
        "",
        f"- Accuracy: {acc_score}/100",
        f"- Probability Quality: {prob_score}/100",
        f"- Data Coverage: {cov_score}/100",
        f"- Operations & Gates: {ops_score}/100",
        f"- Market Readiness: {market_score}/100",
        "",
        "## Why This Grade",
        "",
        f"- Strong core performance and stability (`Top-1 {acc_detail['top1']}%`, `Top-5 {acc_detail['top5']}%`, `Winner Rank {acc_detail['winner_rank']}`, `Playoff F1 {acc_detail['playoff_f1']}`).",
        f"- Strong probability behavior (`Brier playoff {prob_detail['brier_playoff']}`, `Brier cup {prob_detail['brier_cup']}`, `ECE {prob_detail['calibration_error']}`).",
        process_note,
        market_note,
        "",
        "## Dashboard Notes",
        "",
        f"- Team rows: {dash_detail['team_count']}/32",
        f"- Required sections present ratio: {dash_detail['section_ratio']}",
        f"- Freshness score: {dash_detail['freshness_score']}",
        f"- Release status alignment: {dash_detail['release_status']}",
        f"- Cup-goal alignment: {dash_detail['cup_goal_met']}",
        f"- Grade cap active: {dash_detail['capped']}",
        f"- Grade cap reasons: {', '.join(dash_detail['cap_reasons']) if dash_detail['cap_reasons'] else 'none'}",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
