#!/usr/bin/env python3
"""
Verify benchmark contract gates and regression guardrails.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.evaluation_contract import HARD_GATES, DELTA_GUARDRAILS, CUP_VEGAS_EDGE_GOAL


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def _get_metric(payload: dict, key: str) -> Optional[float]:
    if key in payload.get("core", {}):
        return payload["core"].get(key)
    if key in payload.get("quality", {}):
        return payload["quality"].get(key)
    return None


def _assert_hard_gates(current: dict) -> None:
    if (current.get("core", {}).get("top1_accuracy_pct") or 0.0) < HARD_GATES["top1_accuracy_pct_min"]:
        _fail("Hard gate failed: Cup Top-1 below minimum")
    if (current.get("core", {}).get("top5_accuracy_pct") or 0.0) < HARD_GATES["top5_accuracy_pct_min"]:
        _fail("Hard gate failed: Cup Top-5 below minimum")
    if (current.get("core", {}).get("playoff_f1") or 0.0) < HARD_GATES["playoff_f1_min"]:
        _fail("Hard gate failed: Playoff F1 below minimum")
    if (current.get("core", {}).get("average_winner_rank") or 999.0) > HARD_GATES["average_winner_rank_max"]:
        _fail("Hard gate failed: Average Winner Rank above maximum")

    contract = current.get("evaluationContract", {})
    if not contract.get("leakageFree", False):
        _fail("Hard gate failed: strict walk-forward leakage audit not satisfied")


def _assert_delta_guardrails(current: dict, previous: Optional[dict]) -> None:
    eps = 1e-9
    if not previous:
        print("No previous benchmark snapshot; skipping delta guardrails.")
        return

    current_top1 = _get_metric(current, "top1_accuracy_pct")
    previous_top1 = _get_metric(previous, "top1_accuracy_pct")
    if current_top1 is not None and previous_top1 is not None:
        if (
            (previous_top1 - current_top1) > (DELTA_GUARDRAILS["top1_accuracy_pct_max_drop"] + eps)
            and current_top1 < (HARD_GATES["top1_accuracy_pct_min"] + 5.0)
        ):
            _fail("Delta guardrail failed: top1_accuracy_pct dropped too much")

    current_top5 = _get_metric(current, "top5_accuracy_pct")
    previous_top5 = _get_metric(previous, "top5_accuracy_pct")
    if current_top5 is not None and previous_top5 is not None:
        if (
            (previous_top5 - current_top5) > (DELTA_GUARDRAILS["top5_accuracy_pct_max_drop"] + eps)
            and current_top5 < (HARD_GATES["top5_accuracy_pct_min"] + 5.0)
        ):
            _fail("Delta guardrail failed: top5_accuracy_pct dropped too much")

    current_f1 = _get_metric(current, "playoff_f1")
    previous_f1 = _get_metric(previous, "playoff_f1")
    if current_f1 is not None and previous_f1 is not None:
        if (previous_f1 - current_f1) > (DELTA_GUARDRAILS["playoff_f1_max_drop"] + eps):
            _fail("Delta guardrail failed: playoff_f1 dropped too much")

    current_rank = _get_metric(current, "average_winner_rank")
    previous_rank = _get_metric(previous, "average_winner_rank")
    if current_rank is not None and previous_rank is not None:
        if (current_rank - previous_rank) > (DELTA_GUARDRAILS["average_winner_rank_max_increase"] + eps):
            _fail("Delta guardrail failed: average_winner_rank increased too much")

    for quality_key, guard_key in (
        ("brier_playoff", "brier_playoff_max_increase"),
        ("brier_cup", "brier_cup_max_increase"),
        ("log_loss_playoff", "log_loss_playoff_max_increase"),
        ("calibration_error", "calibration_error_max_increase"),
    ):
        cur = _get_metric(current, quality_key)
        prev = _get_metric(previous, quality_key)
        if cur is None or prev is None:
            continue
        if (cur - prev) > (DELTA_GUARDRAILS[guard_key] + eps):
            _fail(f"Delta guardrail failed: {quality_key} increased too much")


def _assert_cup_vegas_goal(current: dict) -> None:
    vegas = current.get("vegas", {})
    if not vegas.get("available", False):
        _fail("Cup Vegas goal failed: Vegas comparison not available")

    rel_edge = vegas.get("cup_relative_brier_edge")
    ci_low = vegas.get("cup_relative_brier_edge_ci_low")
    total_seasons = vegas.get("cup_total_seasons")
    positive_ratio = vegas.get("cup_positive_season_ratio")

    if rel_edge is None or rel_edge < CUP_VEGAS_EDGE_GOAL["relative_brier_improvement_min"]:
        _fail(
            "Cup Vegas goal failed:"
            f" relative edge {rel_edge} below {CUP_VEGAS_EDGE_GOAL['relative_brier_improvement_min']:.3f}"
        )
    if ci_low is None or ci_low <= CUP_VEGAS_EDGE_GOAL["ci_lower_bound_min"]:
        _fail(
            "Cup Vegas goal failed:"
            f" CI low {ci_low} must be > {CUP_VEGAS_EDGE_GOAL['ci_lower_bound_min']:.3f}"
        )
    if total_seasons is None or int(total_seasons) < CUP_VEGAS_EDGE_GOAL["min_seasons_compared"]:
        _fail(
            "Cup Vegas goal failed:"
            f" seasons compared {total_seasons} below {CUP_VEGAS_EDGE_GOAL['min_seasons_compared']}"
        )
    if positive_ratio is None or float(positive_ratio) < CUP_VEGAS_EDGE_GOAL["min_positive_season_ratio"]:
        _fail(
            "Cup Vegas goal failed:"
            f" positive season ratio {positive_ratio} below {CUP_VEGAS_EDGE_GOAL['min_positive_season_ratio']:.3f}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify benchmark contract")
    parser.add_argument("--latest", default="reports/benchmark_latest.json")
    args = parser.parse_args()

    latest_path = PROJECT_ROOT / args.latest
    if not latest_path.exists():
        _fail(f"Missing benchmark payload: {latest_path}")

    with open(latest_path) as f:
        payload = json.load(f)
    current = payload.get("current")
    previous = payload.get("previous")

    if not current:
        _fail("Benchmark payload missing current snapshot")

    _assert_hard_gates(current)
    _assert_delta_guardrails(current, previous)
    _assert_cup_vegas_goal(current)
    print("PASS: Benchmark contract satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
