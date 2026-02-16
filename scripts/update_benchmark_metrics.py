#!/usr/bin/env python3
"""
Generate project benchmark snapshot and delta vs previous snapshot.

Tracks the core four metrics plus probability-quality diagnostics.
"""

import json
import logging
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.validation import (
    ValidationFramework,
    generate_backtest_report,
    generate_checkpoint_backtest_report,
)
from superhuman.betting_odds_loader import (
    get_available_vegas_seasons,
)
from superhuman.models import EnsemblePredictor
from superhuman.real_data_loader import get_advanced_override_coverage
from superhuman.model_profile import load_active_model_profile
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge
from superhuman.evaluation_contract import (
    CONTRACT_VERSION,
    HARD_GATES,
    DELTA_GUARDRAILS,
    CUP_VEGAS_EDGE_GOAL,
)
from superhuman.config import RANDOM_SEED


logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
warnings.filterwarnings("ignore", category=RuntimeWarning)

HISTORY_PATH = PROJECT_ROOT / "reports" / "benchmark_history.json"
LATEST_PATH = PROJECT_ROOT / "reports" / "benchmark_latest.json"
LATEST_MD_PATH = PROJECT_ROOT / "reports" / "BENCHMARK_LATEST.md"
BACKTEST_REPORT_PATH = PROJECT_ROOT / "reports" / "backtest_strict_walk_forward.json"
BACKTEST_CACHE_PATH = PROJECT_ROOT / "data" / "backtest_cache.json"


def _safe_delta(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None:
        return None
    return current - previous


def _fmt(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def _collect_metrics() -> Dict[str, Any]:
    logging.getLogger("superhuman.playoff_experience_loader").setLevel(logging.ERROR)
    logging.getLogger("superhuman.playoff_series_model").setLevel(logging.ERROR)
    logging.getLogger("superhuman.models").setLevel(logging.ERROR)

    profile = load_active_model_profile()
    monte_carlo_simulations = int(os.getenv("BENCHMARK_MONTE_CARLO_SIMULATIONS", "2000"))
    vegas_bootstrap = int(os.getenv("BENCHMARK_VEGAS_BOOTSTRAP", "400"))
    vegas_random_seed = int(os.getenv("BENCHMARK_VEGAS_RANDOM_SEED", str(RANDOM_SEED)))
    force_refresh = os.getenv("BENCHMARK_FORCE_REFRESH", "1") != "0"
    skip_checkpoints = os.getenv("BENCHMARK_SKIP_CHECKPOINTS", "0") == "1"
    strict_verification = os.getenv("BENCHMARK_STRICT_VERIFICATION", "1") != "0"
    require_series_data = os.getenv("BENCHMARK_REQUIRE_SERIES_DATA", "1") != "0"
    require_oof_cup_calibration = os.getenv("BENCHMARK_REQUIRE_OOF_CUP_CALIBRATION", "1") != "0"
    quality_strict_cv = os.getenv("BENCHMARK_QUALITY_STRICT_CV", "0") == "1"
    model_overrides = {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
        "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
        "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
        "monte_carlo_simulations": monte_carlo_simulations,
        "strict_verification": strict_verification,
        "require_series_data_in_strict_mode": require_series_data,
        "require_oof_cup_calibration_in_strict_mode": require_oof_cup_calibration,
    }

    data = load_training_data()
    backtest = generate_backtest_report(
        data,
        cache_path=str(BACKTEST_CACHE_PATH),
        force_refresh=force_refresh,
        model_overrides=model_overrides,
    )
    checkpoint_report: Dict[str, Any] = {"checkpoints": []}
    if not skip_checkpoints:
        checkpoint_report = generate_checkpoint_backtest_report(
            data,
            checkpoints=[0, 20, 40, 60],
            model_overrides=model_overrides,
        )

    BACKTEST_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKTEST_REPORT_PATH, "w") as f:
        json.dump(backtest, f, indent=2)

    validator = ValidationFramework()
    cv = validator.cross_validate(
        data,
        model_factory=lambda: EnsemblePredictor(
            use_neural_network=bool(profile.get("use_neural_network", True)),
            use_recency_weighting=bool(profile.get("use_recency_weighting", True)),
            use_cup_calibration=bool(profile.get("use_cup_calibration", True)),
            recency_decay_rate=float(profile.get("recency_decay_rate", 0.15)),
            cup_winner_boost=float(profile.get("cup_winner_boost", 2.0)),
            cup_market_prior_blend=float(profile.get("cup_market_prior_blend", 0.0)),
            cup_ensemble_weights=profile.get("cup_ensemble_weights"),
            monte_carlo_simulations=monte_carlo_simulations,
            strict_verification=quality_strict_cv,
            require_series_data_in_strict_mode=require_series_data,
            require_oof_cup_calibration_in_strict_mode=require_oof_cup_calibration,
        ),
    )

    vegas_seasons = get_available_vegas_seasons(start_season=2010, end_season=2025)
    vegas_diag = evaluate_model_vs_vegas_edge(
        historical_data=data,
        model_overrides=model_overrides,
        start_season=2010,
        end_season=2025,
        confidence_level=float(CUP_VEGAS_EDGE_GOAL["confidence_level"]),
        n_bootstrap=vegas_bootstrap,
        random_seed=vegas_random_seed,
    )

    summary = backtest.get("summary", {})
    coverage = get_advanced_override_coverage(start_season=2010, end_season=2024)

    has_vegas = bool(vegas_diag.get("available"))
    vegas_playoff = vegas_diag.get("playoff", {}) if has_vegas else {}
    vegas_cup = vegas_diag.get("cup", {}) if has_vegas else {}
    expected_seasons = list(range(2010, 2026))
    missing_vegas_seasons = [s for s in expected_seasons if s not in vegas_seasons]
    cup_rel_edge = vegas_cup.get("relative_brier_edge")
    cup_ci_low = vegas_cup.get("relative_brier_edge_ci_low")
    cup_ci_high = vegas_cup.get("relative_brier_edge_ci_high")
    cup_positive_ratio = vegas_cup.get("positive_season_ratio")
    cup_total_seasons = vegas_cup.get("total_seasons")
    cup_gate_prereqs_met = bool(
        has_vegas
        and cup_rel_edge is not None
        and cup_ci_low is not None
        and cup_positive_ratio is not None
        and cup_total_seasons is not None
        and cup_ci_low > CUP_VEGAS_EDGE_GOAL["ci_lower_bound_min"]
        and cup_positive_ratio >= CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"]
        and cup_total_seasons >= CUP_VEGAS_EDGE_GOAL["min_seasons_compared"]
    )
    cup_release_floor_met = bool(
        cup_gate_prereqs_met
        and cup_rel_edge >= CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_min"]
    )
    cup_strong_met = bool(
        cup_gate_prereqs_met
        and cup_rel_edge >= CUP_VEGAS_EDGE_GOAL.get(
            "relative_brier_improvement_strong",
            CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_stretch"],
        )
    )
    cup_stretch_met = bool(
        cup_gate_prereqs_met
        and cup_rel_edge >= CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_stretch"]
    )
    cup_moonshot_met = bool(
        cup_gate_prereqs_met
        and cup_rel_edge >= CUP_VEGAS_EDGE_GOAL.get(
            "relative_brier_improvement_moonshot",
            CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_stretch"],
        )
    )
    if not cup_gate_prereqs_met:
        cup_goal_tier = "insufficient_data_or_stability"
    elif cup_moonshot_met:
        cup_goal_tier = "moonshot"
    elif cup_stretch_met:
        cup_goal_tier = "stretch"
    elif cup_strong_met:
        cup_goal_tier = "strong"
    elif cup_release_floor_met:
        cup_goal_tier = "release_floor"
    else:
        cup_goal_tier = "below_release_floor"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modelVersion": backtest.get("modelVersion"),
        "profileVersion": profile.get("profileVersion"),
        "evaluationMode": backtest.get("evaluationMode"),
        "evaluationContract": {
            "version": CONTRACT_VERSION,
            "hardGates": HARD_GATES,
            "deltaGuardrails": DELTA_GUARDRAILS,
            "leakageFree": bool(backtest.get("walkForwardAudit", {}).get("leakageFree", False)),
        },
        "verificationSettings": {
            "strict_verification": strict_verification,
            "require_series_data_in_strict_mode": require_series_data,
            "require_oof_cup_calibration_in_strict_mode": require_oof_cup_calibration,
            "quality_cv_strict_mode": quality_strict_cv,
            "vegas_random_seed": vegas_random_seed,
        },
        "core": {
            "top1_accuracy_pct": float(summary.get("topPickAccuracy", 0.0)),
            "top5_accuracy_pct": float(summary.get("top5Accuracy", 0.0)),
            "average_winner_rank": float(summary.get("averageWinnerRank", 0.0)),
            "playoff_f1": float(summary.get("averagePlayoffF1", 0.0)),
        },
        "quality": {
            "brier_playoff": float(cv.brier_score_playoff),
            "brier_cup": float(cv.brier_score_cup),
            "log_loss_playoff": float(cv.log_loss_playoff),
            "calibration_error": float(cv.calibration_error),
        },
        "checkpoint": {
            f"g{row['checkpointGames']}_playoff_f1": row["averagePlayoffF1"]
            for row in checkpoint_report.get("checkpoints", [])
        },
        "vegas": {
            "available": has_vegas,
            "seasons_available": vegas_seasons,
            "seasons_missing": missing_vegas_seasons,
            "sample_playoff": int(vegas_diag.get("rows_compared", 0)) if has_vegas else 0,
            "sample_cup": int(vegas_diag.get("rows_compared", 0)) if has_vegas else 0,
            "vegas_brier_playoff": float(vegas_playoff.get("vegas_brier")) if has_vegas else None,
            "vegas_brier_cup": float(vegas_cup.get("vegas_brier")) if has_vegas else None,
            "model_minus_vegas_brier_playoff": float(vegas_playoff.get("model_minus_vegas_brier")) if has_vegas else None,
            "model_minus_vegas_brier_cup": float(vegas_cup.get("model_minus_vegas_brier")) if has_vegas else None,
            "vegas_log_loss_playoff": float(vegas_playoff.get("vegas_log_loss")) if has_vegas else None,
            "vegas_log_loss_cup": float(vegas_cup.get("vegas_log_loss")) if has_vegas else None,
            "model_minus_vegas_log_loss_playoff": float(vegas_playoff.get("model_minus_vegas_log_loss")) if has_vegas else None,
            "model_minus_vegas_log_loss_cup": float(vegas_cup.get("model_minus_vegas_log_loss")) if has_vegas else None,
            "cup_relative_brier_edge": float(cup_rel_edge) if cup_rel_edge is not None else None,
            "cup_relative_brier_edge_ci_low": float(cup_ci_low) if cup_ci_low is not None else None,
            "cup_relative_brier_edge_ci_high": float(cup_ci_high) if cup_ci_high is not None else None,
            "cup_positive_season_ratio": float(cup_positive_ratio) if cup_positive_ratio is not None else None,
            "cup_positive_seasons": int(vegas_cup.get("positive_seasons")) if vegas_cup.get("positive_seasons") is not None else None,
            "cup_total_seasons": int(cup_total_seasons) if cup_total_seasons is not None else None,
            "cup_target": {
                "relative_brier_improvement_min": CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_min"],
                "relative_brier_improvement_strong": CUP_VEGAS_EDGE_GOAL.get(
                    "relative_brier_improvement_strong"
                ),
                "relative_brier_improvement_stretch": CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_stretch"],
                "relative_brier_improvement_moonshot": CUP_VEGAS_EDGE_GOAL.get(
                    "relative_brier_improvement_moonshot"
                ),
                "confidence_level": CUP_VEGAS_EDGE_GOAL["confidence_level"],
                "ci_lower_bound_min": CUP_VEGAS_EDGE_GOAL["ci_lower_bound_min"],
                "min_seasons_compared": CUP_VEGAS_EDGE_GOAL["min_seasons_compared"],
                "min_positive_season_ratio": CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"],
                # Backward-compatible release gate flag used by existing dashboards.
                "goal_met": cup_release_floor_met,
                "release_floor_met": cup_release_floor_met,
                "strong_met": cup_strong_met,
                "stretch_met": cup_stretch_met,
                "moonshot_met": cup_moonshot_met,
                "gate_prereqs_met": cup_gate_prereqs_met,
                "goal_tier": cup_goal_tier,
            },
            "season_edges": vegas_cup.get("season_edges", []) if has_vegas else [],
        },
        "dataCoverage": {
            "advanced_accepted_season_ratio": float(coverage.get("acceptedSeasonRatio", 0.0)),
            "advanced_accepted_team_ratio": float(coverage.get("acceptedTeamCoverageRatio", 0.0)),
            "advanced_raw_team_ratio": float(coverage.get("rawTeamCoverageRatio", 0.0)),
        },
    }


def _write_markdown(current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> None:
    c_core = current["core"]
    c_quality = current["quality"]
    c_vegas = current["vegas"]
    c_checkpoint = current.get("checkpoint", {})
    c_coverage = current.get("dataCoverage", {})

    p_core = previous["core"] if previous else {}
    p_quality = previous["quality"] if previous else {}
    p_vegas = previous["vegas"] if previous else {}
    p_checkpoint = previous.get("checkpoint", {}) if previous else {}
    p_coverage = previous.get("dataCoverage", {}) if previous else {}

    lines = []
    lines.append("# Latest Benchmark Metrics")
    lines.append("")
    lines.append(f"Generated: `{current['timestamp']}`")
    lines.append(f"Model Version: `{current.get('modelVersion')}`")
    lines.append(f"Profile Version: `{current.get('profileVersion')}`")
    lines.append("")
    lines.append("## Evaluation Contract")
    lines.append("")
    contract = current.get("evaluationContract", {})
    verification = current.get("verificationSettings", {})
    lines.append(f"- Contract Version: `{contract.get('version', 'N/A')}`")
    lines.append(f"- Strict Walk-Forward Leakage-Free: `{contract.get('leakageFree', False)}`")
    lines.append(f"- Benchmark strict verification: `{verification.get('strict_verification', False)}`")
    lines.append(f"- Vegas diagnostic random seed: `{verification.get('vegas_random_seed', 'N/A')}`")
    lines.append(
        "- Quality CV strict mode: "
        f"`{verification.get('quality_cv_strict_mode', False)}` "
        "(set `BENCHMARK_QUALITY_STRICT_CV=1` to enforce strict CV model fitting)."
    )
    lines.append("")
    lines.append("## Core 4 Metrics")
    lines.append("")
    lines.append("| Metric | Current | Previous | Delta |")
    lines.append("|---|---:|---:|---:|")

    core_rows = [
        ("Cup Top-1 Accuracy (%)", "top1_accuracy_pct", 1),
        ("Cup Top-5 Accuracy (%)", "top5_accuracy_pct", 1),
        ("Average Winner Rank (lower better)", "average_winner_rank", 2),
        ("Playoff F1", "playoff_f1", 3),
    ]
    for label, key, digits in core_rows:
        cur = c_core.get(key)
        prev = p_core.get(key)
        delta = _safe_delta(cur, prev)
        lines.append(f"| {label} | {_fmt(cur, digits)} | {_fmt(prev, digits)} | {_fmt(delta, digits)} |")

    lines.append("")
    lines.append("## Probability Quality")
    lines.append("")
    lines.append("| Metric | Current | Previous | Delta |")
    lines.append("|---|---:|---:|---:|")

    quality_rows = [
        ("Brier Playoff (lower better)", "brier_playoff"),
        ("Brier Cup (lower better)", "brier_cup"),
        ("Log Loss Playoff (lower better)", "log_loss_playoff"),
        ("Calibration Error (lower better)", "calibration_error"),
    ]
    for label, key in quality_rows:
        cur = c_quality.get(key)
        prev = p_quality.get(key)
        delta = _safe_delta(cur, prev)
        lines.append(f"| {label} | {_fmt(cur)} | {_fmt(prev)} | {_fmt(delta)} |")

    lines.append("")
    lines.append("## Checkpoint Playoff F1")
    lines.append("")
    lines.append("| Metric | Current | Previous | Delta |")
    lines.append("|---|---:|---:|---:|")
    checkpoint_rows = [
        ("Games 0 Playoff F1", "g0_playoff_f1"),
        ("Games 20 Playoff F1", "g20_playoff_f1"),
        ("Games 40 Playoff F1", "g40_playoff_f1"),
        ("Games 60 Playoff F1", "g60_playoff_f1"),
    ]
    for label, key in checkpoint_rows:
        cur = c_checkpoint.get(key)
        prev = p_checkpoint.get(key)
        delta = _safe_delta(cur, prev)
        lines.append(f"| {label} | {_fmt(cur)} | {_fmt(prev)} | {_fmt(delta)} |")

    lines.append("")
    lines.append("## Data Coverage")
    lines.append("")
    lines.append("| Metric | Current | Previous | Delta |")
    lines.append("|---|---:|---:|---:|")
    coverage_rows = [
        ("Advanced Accepted Season Ratio", "advanced_accepted_season_ratio"),
        ("Advanced Accepted Team Ratio", "advanced_accepted_team_ratio"),
        ("Advanced Raw Team Ratio", "advanced_raw_team_ratio"),
    ]
    for label, key in coverage_rows:
        cur = c_coverage.get(key)
        prev = p_coverage.get(key)
        delta = _safe_delta(cur, prev)
        lines.append(f"| {label} | {_fmt(cur)} | {_fmt(prev)} | {_fmt(delta)} |")

    lines.append("")
    lines.append("## Vegas Comparison")
    lines.append("")
    if not c_vegas.get("available"):
        missing = c_vegas.get("seasons_missing", [])
        lines.append("Vegas historical odds data is not fully available in repository; vegas deltas are `N/A`.")
        lines.append(f"- Seasons present: `{c_vegas.get('seasons_available', [])}`")
        lines.append(f"- Seasons missing: `{missing}`")
    else:
        lines.append("| Metric | Current | Previous | Delta |")
        lines.append("|---|---:|---:|---:|")
        vegas_rows = [
            ("Model - Vegas Brier (Playoff)", "model_minus_vegas_brier_playoff"),
            ("Model - Vegas Brier (Cup)", "model_minus_vegas_brier_cup"),
            ("Model - Vegas Log Loss (Playoff)", "model_minus_vegas_log_loss_playoff"),
            ("Model - Vegas Log Loss (Cup)", "model_minus_vegas_log_loss_cup"),
            ("Cup Relative Brier Edge", "cup_relative_brier_edge"),
            ("Cup Relative Brier Edge CI Low", "cup_relative_brier_edge_ci_low"),
            ("Cup Relative Brier Edge CI High", "cup_relative_brier_edge_ci_high"),
        ]
        for label, key in vegas_rows:
            cur = c_vegas.get(key)
            prev = p_vegas.get(key)
            delta = _safe_delta(cur, prev)
            lines.append(f"| {label} | {_fmt(cur)} | {_fmt(prev)} | {_fmt(delta)} |")
        lines.append("")
        cup_target = c_vegas.get("cup_target", {})
        lines.append("### Cup-Vegas Tiered Target")
        lines.append("")
        floor_thr = cup_target.get("relative_brier_improvement_min")
        strong_thr = cup_target.get("relative_brier_improvement_strong")
        stretch_thr = cup_target.get("relative_brier_improvement_stretch")
        moonshot_thr = cup_target.get("relative_brier_improvement_moonshot")
        lines.append(
            f"- Thresholds: release floor `>= {_fmt(floor_thr, 3)}`, "
            f"strong `>= {_fmt(strong_thr, 3)}`, "
            f"stretch `>= {_fmt(stretch_thr, 3)}`, "
            f"moonshot `>= {_fmt(moonshot_thr, 3)}`"
        )
        lines.append(
            f"- Confidence gate: CI low `> {cup_target.get('ci_lower_bound_min', 0.0):.2f}` "
            f"at `{cup_target.get('confidence_level', 0.95):.2f}` confidence"
        )
        lines.append(
            f"- Sustainability gate: `>= {cup_target.get('min_seasons_compared', 'n/a')}` seasons and "
            f"`>= {cup_target.get('min_positive_season_ratio', 'n/a'):.2f}` positive-season ratio"
        )
        lines.append(
            f"- Current: edge `{_fmt(c_vegas.get('cup_relative_brier_edge'))}`, "
            f"CI [`{_fmt(c_vegas.get('cup_relative_brier_edge_ci_low'))}`, `{_fmt(c_vegas.get('cup_relative_brier_edge_ci_high'))}`], "
            f"positive seasons `{c_vegas.get('cup_positive_seasons', 'n/a')}`/`{c_vegas.get('cup_total_seasons', 'n/a')}`"
        )
        lines.append(f"- Release gate status: `{'PASS' if cup_target.get('goal_met') else 'FAIL'}`")
        lines.append(f"- Tier reached: `{cup_target.get('goal_tier', 'unknown')}`")

    LATEST_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_MD_PATH.write_text("\n".join(lines) + "\n")


def main() -> int:
    current = _collect_metrics()

    history = []
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH) as f:
            history = json.load(f)

    previous = history[-1] if history else None
    history.append(current)

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)

    with open(LATEST_PATH, "w") as f:
        json.dump({"current": current, "previous": previous}, f, indent=2)

    _write_markdown(current, previous)

    print("Benchmark update complete")
    print(f"Current: {LATEST_PATH}")
    print(f"History: {HISTORY_PATH}")
    print(f"Markdown: {LATEST_MD_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
