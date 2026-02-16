#!/usr/bin/env python3
"""
Phase 9 experimental wider search (non-deploying).

Runs a broader candidate grid and reports:
1) best strict-eligible candidate (current production rules)
2) best relaxed candidate (experimental-only, not deployed)
"""

from __future__ import annotations

import json
import math
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.evaluation_contract import CUP_VEGAS_EDGE_GOAL, DELTA_GUARDRAILS, HARD_GATES
from superhuman.model_profile import load_active_model_profile
from superhuman.validation import generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge


OUT_JSON = PROJECT_ROOT / "reports" / "phase9_cup_edge_experiment.json"
OUT_MD = PROJECT_ROOT / "reports" / "PHASE9_CUP_EDGE_EXPERIMENT.md"

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def _overrides_from_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
        "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
    }


def _extract_core(backtest: Dict[str, Any]) -> Dict[str, float]:
    summary = backtest.get("summary", {})
    return {
        "top1_accuracy_pct": float(summary.get("topPickAccuracy", 0.0)),
        "top5_accuracy_pct": float(summary.get("top5Accuracy", 0.0)),
        "average_winner_rank": float(summary.get("averageWinnerRank", 999.0)),
        "playoff_f1": float(summary.get("averagePlayoffF1", 0.0)),
    }


def _hard_gate(core: Dict[str, float]) -> bool:
    return (
        core["top1_accuracy_pct"] >= HARD_GATES["top1_accuracy_pct_min"]
        and core["top5_accuracy_pct"] >= HARD_GATES["top5_accuracy_pct_min"]
        and core["playoff_f1"] >= HARD_GATES["playoff_f1_min"]
        and core["average_winner_rank"] <= HARD_GATES["average_winner_rank_max"]
    )


def _strict_non_reg(base: Dict[str, float], cand: Dict[str, float]) -> bool:
    return (
        (base["top1_accuracy_pct"] - cand["top1_accuracy_pct"]) <= DELTA_GUARDRAILS["top1_accuracy_pct_max_drop"]
        and (base["top5_accuracy_pct"] - cand["top5_accuracy_pct"]) <= DELTA_GUARDRAILS["top5_accuracy_pct_max_drop"]
        and (base["playoff_f1"] - cand["playoff_f1"]) <= DELTA_GUARDRAILS["playoff_f1_max_drop"]
        and (cand["average_winner_rank"] - base["average_winner_rank"]) <= DELTA_GUARDRAILS["average_winner_rank_max_increase"]
    )


def _relaxed_non_reg(base: Dict[str, float], cand: Dict[str, float]) -> bool:
    return (
        (base["top1_accuracy_pct"] - cand["top1_accuracy_pct"]) <= 2.0
        and (base["top5_accuracy_pct"] - cand["top5_accuracy_pct"]) <= 3.0
        and (base["playoff_f1"] - cand["playoff_f1"]) <= 0.010
        and (cand["average_winner_rank"] - base["average_winner_rank"]) <= 0.6
    )


def _edge(row: Dict[str, Any]) -> float:
    value = row.get("vegas", {}).get("cup_relative_brier_edge")
    if value is None:
        return -1e9
    return float(value)


def _required_positive_seasons(total_seasons: int) -> int:
    return int(math.ceil(float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"]) * float(total_seasons) - 1e-12))


def _passes_positive_ratio_prefilter(vegas: Dict[str, Any]) -> bool:
    pos = vegas.get("cup_positive_seasons")
    total = vegas.get("cup_total_seasons")
    ratio = vegas.get("cup_positive_season_ratio")
    if isinstance(pos, (int, float)) and isinstance(total, (int, float)) and int(total) > 0:
        return int(pos) >= _required_positive_seasons(int(total))
    if ratio is None:
        return False
    return float(ratio) >= float(CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"])


def _candidate_grid(base: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    decays = [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.22, 0.25, 0.28]
    boosts = [1.0, 1.5, 2.0, 2.5, 3.0]
    cals = [False, True]

    rows.append({"name": "baseline", "overrides": dict(base)})
    for decay in decays:
        for boost in boosts:
            for cal in cals:
                name = f"d{decay:.2f}-b{boost:.1f}-cal{int(cal)}"
                rows.append(
                    {
                        "name": name,
                        "overrides": {
                            **dict(base),
                            "recency_decay_rate": float(decay),
                            "cup_winner_boost": float(boost),
                            "use_cup_calibration": bool(cal),
                        },
                    }
                )
    # Extra weight-only experiments.
    for gb, nn, mc in [
        (0.2, 0.2, 0.6),
        (0.2, 0.0, 0.8),
        (0.4, 0.2, 0.4),
        (0.0, 0.0, 1.0),
    ]:
        rows.append(
            {
                "name": f"w-{gb:.1f}-{nn:.1f}-{mc:.1f}",
                "overrides": {
                    **dict(base),
                    "use_cup_calibration": False,
                    "cup_ensemble_weights": {
                        "gradient_boosting": gb,
                        "neural_network": nn,
                        "monte_carlo": mc,
                    },
                },
            }
        )
    return rows


def main() -> int:
    data = load_training_data()
    profile = load_active_model_profile()
    base = _overrides_from_profile(profile)
    candidates = _candidate_grid(base)

    rows: List[Dict[str, Any]] = []
    for cand in candidates:
        print(f"[phase9-exp] vegas eval: {cand['name']}", flush=True)
        diag = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=cand["overrides"],
            n_bootstrap=250,
        )
        cup = diag.get("cup", {})
        rows.append(
            {
                "name": cand["name"],
                "overrides": cand["overrides"],
                "vegas": {
                    "cup_relative_brier_edge": cup.get("relative_brier_edge"),
                    "cup_relative_brier_edge_ci_low": cup.get("relative_brier_edge_ci_low"),
                    "cup_relative_brier_edge_ci_high": cup.get("relative_brier_edge_ci_high"),
                    "cup_model_brier": cup.get("model_brier"),
                    "cup_vegas_brier": cup.get("vegas_brier"),
                    "cup_positive_season_ratio": cup.get("positive_season_ratio"),
                    "cup_positive_seasons": cup.get("positive_seasons"),
                    "cup_total_seasons": cup.get("total_seasons"),
                },
                "positiveRatioPrefilterPass": _passes_positive_ratio_prefilter(
                    {
                        "cup_positive_season_ratio": cup.get("positive_season_ratio"),
                        "cup_positive_seasons": cup.get("positive_seasons"),
                        "cup_total_seasons": cup.get("total_seasons"),
                    }
                ),
                "core": None,
                "hardGate": None,
                "strictNonRegression": None,
                "relaxedNonRegression": None,
            }
        )

    rows.sort(key=_edge, reverse=True)
    top_for_core = rows[:18]
    baseline_row = next(r for r in rows if r["name"] == "baseline")

    for row in top_for_core:
        if row["name"] != "baseline" and not bool(row.get("positiveRatioPrefilterPass")):
            continue
        print(f"[phase9-exp] core eval: {row['name']}", flush=True)
        backtest = generate_backtest_report(
            data,
            cache_path=None,
            force_refresh=True,
            model_overrides=row["overrides"],
        )
        row["core"] = _extract_core(backtest)

    baseline_core = baseline_row.get("core")
    if baseline_core is None:
        backtest = generate_backtest_report(
            data,
            cache_path=None,
            force_refresh=True,
            model_overrides=baseline_row["overrides"],
        )
        baseline_row["core"] = _extract_core(backtest)
        baseline_core = baseline_row["core"]

    for row in rows:
        if row.get("core") is None:
            continue
        row["hardGate"] = _hard_gate(row["core"])
        row["strictNonRegression"] = _strict_non_reg(baseline_core, row["core"])
        row["relaxedNonRegression"] = _relaxed_non_reg(baseline_core, row["core"])
        if row["name"] != "baseline" and not bool(row.get("positiveRatioPrefilterPass")):
            row["strictNonRegression"] = False
            row["relaxedNonRegression"] = False

    strict_pool = [r for r in rows if r.get("hardGate") and r.get("strictNonRegression")]
    relaxed_pool = [r for r in rows if r.get("hardGate") and r.get("relaxedNonRegression")]
    best_strict: Optional[Dict[str, Any]] = strict_pool[0] if strict_pool else None
    best_relaxed: Optional[Dict[str, Any]] = relaxed_pool[0] if relaxed_pool else None

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "phase": "phase9_cup_edge_experiment",
        "baseline": baseline_row,
        "summary": {
            "totalCandidates": len(rows),
            "coreEvaluatedCandidates": len([r for r in rows if r.get("core") is not None]),
            "positiveRatioPrefilterPassCount": len([r for r in rows if r.get("positiveRatioPrefilterPass")]),
            "strictEligibleCount": len(strict_pool),
            "relaxedEligibleCount": len(relaxed_pool),
            "bestStrict": best_strict["name"] if best_strict else None,
            "bestRelaxed": best_relaxed["name"] if best_relaxed else None,
            "bestStrictEdge": _edge(best_strict) if best_strict else None,
            "bestRelaxedEdge": _edge(best_relaxed) if best_relaxed else None,
            "baselineEdge": _edge(baseline_row),
            "deployment": "DISABLED_EXPERIMENT_ONLY",
        },
        "topByEdge": rows[:25],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Phase 9 Cup Edge Experiment (Wider Search)",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        f"- Total candidates: `{report['summary']['totalCandidates']}`",
        f"- Core evaluated: `{report['summary']['coreEvaluatedCandidates']}`",
        f"- Positive-ratio prefilter pass: `{report['summary']['positiveRatioPrefilterPassCount']}`",
        f"- Baseline edge: `{report['summary']['baselineEdge']}`",
        f"- Best strict candidate: `{report['summary']['bestStrict']}` ({report['summary']['bestStrictEdge']})",
        f"- Best relaxed candidate: `{report['summary']['bestRelaxed']}` ({report['summary']['bestRelaxedEdge']})",
        "- Deployment: `DISABLED_EXPERIMENT_ONLY`",
        "",
        "## Top Candidates By Cup Edge",
        "",
        "| Candidate | Edge | CI Low | Pos Ratio | Prefilter | Hard Gate | Strict Non-Reg | Relaxed Non-Reg |",
        "|---|---:|---:|---:|---|---|---|---|",
    ]
    for row in report["topByEdge"][:20]:
        vegas = row.get("vegas", {})
        edge = vegas.get("cup_relative_brier_edge")
        ci_low = vegas.get("cup_relative_brier_edge_ci_low")
        pos = vegas.get("cup_positive_season_ratio")
        lines.append(
            f"| {row['name']} | "
            f"{'N/A' if edge is None else f'{edge:.4f}'} | "
            f"{'N/A' if ci_low is None else f'{ci_low:.4f}'} | "
            f"{'N/A' if pos is None else f'{pos:.3f}'} | "
            f"{row.get('positiveRatioPrefilterPass')} | "
            f"{row.get('hardGate')} | {row.get('strictNonRegression')} | {row.get('relaxedNonRegression')} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
