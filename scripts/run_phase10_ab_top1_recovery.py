#!/usr/bin/env python3
"""
Phase 10: guarded A/B profile path for Top-1 recovery vs Cup-edge tradeoff.

Creates a separate experimental profile track and evaluates recovery variants
without auto-deploying to production profile.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.evaluation_contract import CUP_VEGAS_EDGE_GOAL, DELTA_GUARDRAILS, HARD_GATES
from superhuman.model_profile import load_active_model_profile
from superhuman.validation import generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge


OUT_JSON = PROJECT_ROOT / "reports" / "phase10_ab_top1_recovery.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE10_AB_TOP1_RECOVERY.md"
PROFILES_DIR = PROJECT_ROOT / "data" / "model_profiles"


def _base_overrides(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
        "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
        "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
        "monte_carlo_simulations": 2000,
        "strict_verification": True,
        "require_series_data_in_strict_mode": True,
        "require_oof_cup_calibration_in_strict_mode": True,
    }


def _extract_core(summary: Dict[str, Any]) -> Dict[str, float]:
    return {
        "top1_accuracy_pct": float(summary.get("topPickAccuracy", 0.0)),
        "top5_accuracy_pct": float(summary.get("top5Accuracy", 0.0)),
        "average_winner_rank": float(summary.get("averageWinnerRank", 999.0)),
        "playoff_f1": float(summary.get("averagePlayoffF1", 0.0)),
    }


def _hard_gates_pass(core: Dict[str, float]) -> bool:
    return (
        core["top1_accuracy_pct"] >= HARD_GATES["top1_accuracy_pct_min"]
        and core["top5_accuracy_pct"] >= HARD_GATES["top5_accuracy_pct_min"]
        and core["playoff_f1"] >= HARD_GATES["playoff_f1_min"]
        and core["average_winner_rank"] <= HARD_GATES["average_winner_rank_max"]
    )


def _strict_non_regression(base: Dict[str, float], cand: Dict[str, float]) -> bool:
    return (
        (base["top1_accuracy_pct"] - cand["top1_accuracy_pct"]) <= DELTA_GUARDRAILS["top1_accuracy_pct_max_drop"]
        and (base["top5_accuracy_pct"] - cand["top5_accuracy_pct"]) <= DELTA_GUARDRAILS["top5_accuracy_pct_max_drop"]
        and (base["playoff_f1"] - cand["playoff_f1"]) <= DELTA_GUARDRAILS["playoff_f1_max_drop"]
        and (cand["average_winner_rank"] - base["average_winner_rank"]) <= DELTA_GUARDRAILS["average_winner_rank_max_increase"]
    )


def _required_positive_seasons(total_seasons: int) -> int:
    return int(math.ceil(float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"]) * float(total_seasons) - 1e-12))


def _passes_positive_ratio_prefilter(pos_seasons: Any, total_seasons: Any, ratio: Any) -> bool:
    if isinstance(pos_seasons, (int, float)) and isinstance(total_seasons, (int, float)) and int(total_seasons) > 0:
        return int(pos_seasons) >= _required_positive_seasons(int(total_seasons))
    if ratio is None:
        return False
    return float(ratio) >= float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"])


def _candidate_grid(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    baseline_blend = float(base.get("cup_market_prior_blend", 0.0))
    edge_blends = sorted({0.0, round(min(0.35, baseline_blend), 2), round(baseline_blend, 2)})

    experimental_edge = {
        **copy.deepcopy(base),
        "use_cup_calibration": False,
        "cup_market_prior_blend": 0.0,
        "cup_ensemble_weights": {
            "gradient_boosting": 0.0,
            "neural_network": 0.0,
            "monte_carlo": 1.0,
        },
    }

    rows = [
        {"name": "baseline", "overrides": copy.deepcopy(base)},
        {"name": "experimental-edge-mc100", "overrides": experimental_edge},
        {
            "name": "recovery-mc85",
            "overrides": {
                **copy.deepcopy(base),
                "use_cup_calibration": False,
                "cup_ensemble_weights": {
                    "gradient_boosting": 0.10,
                    "neural_network": 0.05,
                    "monte_carlo": 0.85,
                },
            },
        },
        {
            "name": "recovery-mc80",
            "overrides": {
                **copy.deepcopy(base),
                "use_cup_calibration": False,
                "cup_ensemble_weights": {
                    "gradient_boosting": 0.15,
                    "neural_network": 0.05,
                    "monte_carlo": 0.80,
                },
            },
        },
        {
            "name": "recovery-mc75",
            "overrides": {
                **copy.deepcopy(base),
                "use_cup_calibration": False,
                "cup_ensemble_weights": {
                    "gradient_boosting": 0.20,
                    "neural_network": 0.05,
                    "monte_carlo": 0.75,
                },
            },
        },
    ]
    for blend in edge_blends:
        rows.append(
            {
                "name": f"experimental-edge-mc100-blend{blend:.2f}",
                "overrides": {
                    **copy.deepcopy(experimental_edge),
                    "cup_market_prior_blend": float(blend),
                },
            }
        )
    return rows


def _write_profile(path: Path, base_profile: Dict[str, Any], name: str, overrides: Dict[str, Any]) -> None:
    profile = copy.deepcopy(base_profile)
    profile.update(overrides)
    profile["profileVersion"] = name
    profile["abTrack"] = True
    profile["generatedAt"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(profile, indent=2) + "\n")


def main() -> int:
    profile = load_active_model_profile()
    base = _base_overrides(profile)
    candidates = _candidate_grid(base)
    data = load_training_data()

    rows: List[Dict[str, Any]] = []
    for cand in candidates:
        print(f"[phase10-ab] evaluating: {cand['name']}", flush=True)
        backtest = generate_backtest_report(
            data,
            cache_path=None,
            force_refresh=True,
            model_overrides=cand["overrides"],
        )
        vegas = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=cand["overrides"],
            n_bootstrap=300,
        )
        core = _extract_core(backtest.get("summary", {}))
        cup = vegas.get("cup", {})
        ratio = cup.get("positive_season_ratio")
        pos_seasons = cup.get("positive_seasons")
        total_seasons = cup.get("total_seasons")
        rows.append(
            {
                "name": cand["name"],
                "overrides": cand["overrides"],
                "core": core,
                "hardGatesPass": _hard_gates_pass(core),
                "cupRelativeEdge": cup.get("relative_brier_edge"),
                "cupEdgeCiLow": cup.get("relative_brier_edge_ci_low"),
                "cupEdgeCiHigh": cup.get("relative_brier_edge_ci_high"),
                "cupPositiveSeasonRatio": ratio,
                "cupPositiveSeasons": pos_seasons,
                "cupTotalSeasons": total_seasons,
                "positiveRatioPrefilterPass": _passes_positive_ratio_prefilter(pos_seasons, total_seasons, ratio),
                "cupModelBrier": cup.get("model_brier"),
                "cupVegasBrier": cup.get("vegas_brier"),
            }
        )

    baseline = next(r for r in rows if r["name"] == "baseline")
    baseline_edge = float(baseline.get("cupRelativeEdge") or -1e9)

    for row in rows:
        row["strictNonRegression"] = _strict_non_regression(baseline["core"], row["core"])
        edge = row.get("cupRelativeEdge")
        row["edgeImprovementVsBaseline"] = None if edge is None else float(edge) - baseline_edge
        row["edgeImproved"] = edge is not None and float(edge) > baseline_edge + 1e-9
        row["abEligible"] = bool(
            row["hardGatesPass"]
            and row["edgeImproved"]
            and row["strictNonRegression"]
            and bool(row.get("positiveRatioPrefilterPass"))
        )

    eligible = [r for r in rows if r.get("abEligible")]
    if eligible:
        # A/B objective: recover Top-1 first, then maximize Cup edge.
        eligible.sort(
            key=lambda r: (
                r["core"]["top1_accuracy_pct"],
                float(r.get("cupRelativeEdge") or -1e9),
                -r["core"]["average_winner_rank"],
            ),
            reverse=True,
        )
        selected = eligible[0]
        reason = "selected highest Top-1 among edge-improved, strict-non-regression candidates"
    else:
        selected = baseline
        reason = "no edge-improved candidate satisfied strict non-regression"

    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    _write_profile(PROFILES_DIR / "baseline_profile.json", profile, "phase10-baseline", baseline["overrides"])
    edge_row = next(r for r in rows if r["name"] == "experimental-edge-mc100")
    _write_profile(
        PROFILES_DIR / "experimental_edge_profile.json",
        profile,
        "phase10-experimental-edge-mc100",
        edge_row["overrides"],
    )
    _write_profile(
        PROFILES_DIR / "ab_recovery_candidate_profile.json",
        profile,
        f"phase10-ab-recovery-{selected['name']}",
        selected["overrides"],
    )

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase10_ab_top1_recovery",
        "activeProfileVersion": profile.get("profileVersion"),
        "rows": rows,
        "decision": {
            "selected": selected["name"],
            "reason": reason,
            "autoDeploy": False,
            "note": "A/B track only: active production profile unchanged.",
        },
        "profileArtifacts": {
            "baseline": str(PROFILES_DIR / "baseline_profile.json"),
            "experimentalEdge": str(PROFILES_DIR / "experimental_edge_profile.json"),
            "abRecoveryCandidate": str(PROFILES_DIR / "ab_recovery_candidate_profile.json"),
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 10 A/B Top-1 Recovery",
        "",
        f"Generated: `{report['generatedAt']}`",
        f"- Active profile (unchanged): `{report['activeProfileVersion']}`",
        f"- Selected A/B candidate: `{report['decision']['selected']}`",
        f"- Decision reason: {report['decision']['reason']}",
        "",
        "## Candidate Results",
        "",
        "| Candidate | Top1 | Top5 | Avg Rank | F1 | Cup Edge | CI Low | Pos Ratio | Prefilter | Hard Gates | Strict Non-Reg | A/B Eligible |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        edge_val = row.get("cupRelativeEdge")
        ci_low_val = row.get("cupEdgeCiLow")
        pos_ratio = row.get("cupPositiveSeasonRatio")
        edge_text = "N/A" if edge_val is None else f"{float(edge_val):.4f}"
        ci_low_text = "N/A" if ci_low_val is None else f"{float(ci_low_val):.4f}"
        pos_text = "N/A" if pos_ratio is None else f"{float(pos_ratio):.3f}"
        lines.append(
            f"| {row['name']} | "
            f"{row['core']['top1_accuracy_pct']:.1f} | "
            f"{row['core']['top5_accuracy_pct']:.1f} | "
            f"{row['core']['average_winner_rank']:.2f} | "
            f"{row['core']['playoff_f1']:.3f} | "
            f"{edge_text} | "
            f"{ci_low_text} | "
            f"{pos_text} | "
            f"{row.get('positiveRatioPrefilterPass')} | "
            f"{row['hardGatesPass']} | {row['strictNonRegression']} | {row['abEligible']} |"
        )

    lines.extend(
        [
            "",
            "## Profile Artifacts",
            "",
            f"- Baseline profile: `{report['profileArtifacts']['baseline']}`",
            f"- Experimental edge profile: `{report['profileArtifacts']['experimentalEdge']}`",
            f"- Recovery candidate profile: `{report['profileArtifacts']['abRecoveryCandidate']}`",
            "",
            "Deployment mode: `NO_AUTODEPLOY_AB_ONLY`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
