#!/usr/bin/env python3
"""
Model performance gate for Superhuman NHL predictions.

Checks strict walk-forward backtest quality and optionally enforces
outperformance vs Vegas on probability metrics.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.data_loader import load_training_data
from superhuman.validation import generate_backtest_report
from superhuman.vegas_edge import evaluate_model_vs_vegas_edge
from superhuman.real_data_loader import get_advanced_override_coverage
from superhuman.evaluation_contract import HARD_GATES, CUP_VEGAS_EDGE_GOAL
from superhuman.config import RANDOM_SEED
from superhuman.model_profile import load_active_model_profile


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def _load_report(
    cache_path: Path,
    require_series_data: bool,
    require_oof_cup_calibration: bool,
) -> dict:
    data = load_training_data(allow_synthetic_fallback=False)
    profile = load_active_model_profile()
    model_overrides = {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
        "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
        "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
        "strict_verification": True,
        "require_series_data_in_strict_mode": bool(require_series_data),
        "require_oof_cup_calibration_in_strict_mode": bool(require_oof_cup_calibration),
    }
    report = generate_backtest_report(
        data,
        cache_path=str(cache_path),
        model_overrides=model_overrides,
    )
    return report


def _assert_no_leakage(report: dict) -> None:
    audit = report.get("walkForwardAudit")
    if not audit:
        _fail("Backtest report missing walkForwardAudit; cannot verify leakage gate")
    if not audit.get("leakageFree", False):
        _fail("walkForwardAudit indicates leakage in strict walk-forward splits")
    for split in audit.get("splits", []):
        held_out = split.get("heldOutSeason")
        max_train = split.get("maxTrainSeason")
        if max_train is None or held_out is None:
            _fail("walkForwardAudit split missing required season metadata")
        if max_train >= held_out:
            _fail(f"Leakage detected: split heldOut={held_out} has maxTrainSeason={max_train}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify model performance gates")
    parser.add_argument("--cache", default="data/backtest_cache.json")
    parser.add_argument("--min-top1", type=float, default=HARD_GATES["top1_accuracy_pct_min"])
    parser.add_argument("--min-top5", type=float, default=HARD_GATES["top5_accuracy_pct_min"])
    parser.add_argument("--min-playoff-f1", type=float, default=HARD_GATES["playoff_f1_min"])
    parser.add_argument("--max-avg-winner-rank", type=float, default=HARD_GATES["average_winner_rank_max"])
    parser.add_argument("--require-vegas-edge", action="store_true")
    parser.add_argument(
        "--require-cup-vegas-goal",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require the Cup-vs-Vegas release-floor target gate.",
    )
    parser.add_argument(
        "--min-cup-relative-edge",
        type=float,
        default=CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_min"],
    )
    parser.add_argument(
        "--cup-edge-confidence-level",
        type=float,
        default=CUP_VEGAS_EDGE_GOAL["confidence_level"],
    )
    parser.add_argument(
        "--min-vegas-seasons",
        type=int,
        default=CUP_VEGAS_EDGE_GOAL["min_seasons_compared"],
    )
    parser.add_argument(
        "--min-positive-season-ratio",
        type=float,
        default=CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"],
    )
    parser.add_argument(
        "--vegas-random-seed",
        type=int,
        default=RANDOM_SEED,
        help="Random seed for deterministic Vegas diagnostics.",
    )
    parser.add_argument(
        "--require-series-data",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require trained playoff series data in strict verification mode.",
    )
    parser.add_argument(
        "--require-oof-cup-calibration",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require out-of-fold Cup calibration coverage in strict verification mode.",
    )
    parser.add_argument("--min-accepted-override-ratio", type=float, default=0.0)
    args = parser.parse_args()

    report = _load_report(
        Path(args.cache),
        require_series_data=bool(args.require_series_data),
        require_oof_cup_calibration=bool(args.require_oof_cup_calibration),
    )
    summary = report.get("summary", {})

    # Core strict walk-forward gates
    if report.get("evaluationMode") != "strict_walk_forward":
        _fail("Backtest must run in strict_walk_forward mode")
    _assert_no_leakage(report)

    top1 = float(summary.get("topPickAccuracy", 0.0))
    top5 = float(summary.get("top5Accuracy", 0.0))
    avg_rank = float(summary.get("averageWinnerRank", 999.0))
    playoff_f1 = float(summary.get("averagePlayoffF1", 0.0))

    print("Backtest summary:")
    print(json.dumps(summary, indent=2))

    if top1 < args.min_top1:
        _fail(f"Top-1 accuracy {top1:.1f}% below threshold {args.min_top1:.1f}%")
    if top5 < args.min_top5:
        _fail(f"Top-5 accuracy {top5:.1f}% below threshold {args.min_top5:.1f}%")
    if avg_rank > args.max_avg_winner_rank:
        _fail(f"Average winner rank {avg_rank:.2f} above threshold {args.max_avg_winner_rank:.2f}")
    if playoff_f1 < args.min_playoff_f1:
        _fail(f"Average playoff F1 {playoff_f1:.3f} below threshold {args.min_playoff_f1:.3f}")

    coverage = get_advanced_override_coverage(start_season=2010, end_season=2024)
    accepted_override_ratio = float(coverage.get("acceptedTeamCoverageRatio", 0.0))
    print(
        "Advanced override coverage:"
        f" accepted seasons {coverage.get('acceptedSeasons', 0)}/{coverage.get('totalSeasons', 0)},"
        f" accepted team ratio {accepted_override_ratio:.3f}"
    )
    if accepted_override_ratio < args.min_accepted_override_ratio:
        _fail(
            "Historical advanced override coverage ratio "
            f"{accepted_override_ratio:.3f} below threshold {args.min_accepted_override_ratio:.3f}"
        )

    if args.require_vegas_edge or args.require_cup_vegas_goal:
        data = load_training_data(allow_synthetic_fallback=False)
        profile = load_active_model_profile()
        model_overrides = {
            "use_neural_network": bool(profile.get("use_neural_network", True)),
            "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
            "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
            "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
            "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
            "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
            "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
            "strict_verification": True,
            "require_series_data_in_strict_mode": bool(args.require_series_data),
            "require_oof_cup_calibration_in_strict_mode": bool(args.require_oof_cup_calibration),
        }
        vegas_diag = evaluate_model_vs_vegas_edge(
            historical_data=data,
            model_overrides=model_overrides,
            confidence_level=args.cup_edge_confidence_level,
            random_seed=args.vegas_random_seed,
        )
        if not vegas_diag.get("available"):
            _fail("Vegas gate requested but strict walk-forward model-vs-vegas rows are unavailable")

        cup = vegas_diag.get("cup", {})
        playoff = vegas_diag.get("playoff", {})

        print("Vegas comparison (strict walk-forward):")
        print(f"  seasons compared: {len(vegas_diag.get('seasons_compared', []))}")
        print(f"  model playoff brier: {playoff.get('model_brier', float('nan')):.4f}")
        print(f"  vegas playoff brier: {playoff.get('vegas_brier', float('nan')):.4f}")
        print(f"  model playoff log loss: {playoff.get('model_log_loss', float('nan')):.4f}")
        print(f"  vegas playoff log loss: {playoff.get('vegas_log_loss', float('nan')):.4f}")
        print(f"  model cup brier: {cup.get('model_brier', float('nan')):.4f}")
        print(f"  vegas cup brier: {cup.get('vegas_brier', float('nan')):.4f}")
        print(f"  model cup log loss: {cup.get('model_log_loss', float('nan')):.4f}")
        print(f"  vegas cup log loss: {cup.get('vegas_log_loss', float('nan')):.4f}")
        if cup.get("relative_brier_edge") is not None:
            print(f"  cup relative brier edge: {cup['relative_brier_edge']:.4f}")
            print(
                "  cup edge CI:"
                f" [{cup.get('relative_brier_edge_ci_low', float('nan')):.4f},"
                f" {cup.get('relative_brier_edge_ci_high', float('nan')):.4f}]"
            )
            print(
                "  cup positive-season ratio:"
                f" {cup.get('positive_season_ratio', 0.0):.3f}"
            )

        # Strict market-outperformance gate (Brier + log-loss, playoff + cup).
        if args.require_vegas_edge:
            if playoff.get("model_brier", float("inf")) >= playoff.get("vegas_brier", float("-inf")):
                _fail("Model playoff Brier does not beat Vegas")
            if cup.get("model_brier", float("inf")) >= cup.get("vegas_brier", float("-inf")):
                _fail("Model Cup Brier does not beat Vegas")
            if playoff.get("model_log_loss", float("inf")) >= playoff.get("vegas_log_loss", float("-inf")):
                _fail("Model playoff log-loss does not beat Vegas")
            if cup.get("model_log_loss", float("inf")) >= cup.get("vegas_log_loss", float("-inf")):
                _fail("Model Cup log-loss does not beat Vegas")

        # Cup edge release-floor gate.
        if args.require_cup_vegas_goal:
            seasons_compared = int(cup.get("total_seasons", 0))
            relative_edge = cup.get("relative_brier_edge")
            ci_low = cup.get("relative_brier_edge_ci_low")
            positive_ratio = cup.get("positive_season_ratio", 0.0)
            if seasons_compared < args.min_vegas_seasons:
                _fail(
                    "Cup Vegas goal failed:"
                    f" only {seasons_compared} seasons compared (need >= {args.min_vegas_seasons})"
                )
            if relative_edge is None or relative_edge < args.min_cup_relative_edge:
                _fail(
                    "Cup Vegas goal failed:"
                    f" relative edge {relative_edge} below target {args.min_cup_relative_edge:.3f}"
                )
            if ci_low is None or ci_low <= 0:
                _fail(
                    "Cup Vegas goal failed:"
                    f" CI low {ci_low} is not above 0.0"
                )
            if positive_ratio < args.min_positive_season_ratio:
                _fail(
                    "Cup Vegas goal failed:"
                    f" positive-season ratio {positive_ratio:.3f} below {args.min_positive_season_ratio:.3f}"
                )

    print("PASS: Model performance gates satisfied")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        logger.exception("Performance verification failed")
        raise SystemExit(1) from exc
