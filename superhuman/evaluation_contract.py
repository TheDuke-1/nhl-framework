"""
Project-wide evaluation contract for model quality and release gates.
"""

# Locked scorecard metrics shown after each update.
CORE_SCORECARD = (
    "top1_accuracy_pct",
    "top5_accuracy_pct",
    "average_winner_rank",
    "playoff_f1",
)

PROBABILITY_QUALITY_SCORECARD = (
    "brier_playoff",
    "brier_cup",
    "log_loss_playoff",
    "calibration_error",
)

VEGAS_SCORECARD = (
    "model_minus_vegas_brier_playoff",
    "model_minus_vegas_brier_cup",
    "cup_relative_brier_edge",
    "cup_relative_brier_edge_ci_low",
    "cup_relative_brier_edge_ci_high",
)

# Absolute floor/ceiling gates.
HARD_GATES = {
    "top1_accuracy_pct_min": 12.0,
    "top5_accuracy_pct_min": 45.0,
    "playoff_f1_min": 0.90,
    "average_winner_rank_max": 8.0,
}

# Tiered top-level goal for Cup-market edge.
#
# Realignment rationale:
# - Keep an achievable release floor for an efficient market.
# - Preserve ambitious targets as non-blocking tiers.
# - Maintain backward-compatible keys consumed across scripts/tests.
CUP_VEGAS_EDGE_GOAL = {
    # Release hard gate: pragmatic, evidence-backed floor.
    "relative_brier_improvement_min": 0.015,
    # Strong/stretch operational target used in reports.
    "relative_brier_improvement_stretch": 0.05,
    # Additional tiers for decisioning and roadmap.
    "relative_brier_improvement_strong": 0.03,
    "relative_brier_improvement_moonshot": 0.08,
    # Confidence interval over season-level relative edge.
    "confidence_level": 0.95,
    # CI lower bound must stay above zero.
    "ci_lower_bound_min": 0.0,
    # "Sustained across many seasons."
    "min_seasons_compared": 10,
    "min_positive_season_ratio": 0.60,
}

# Maximum allowed regression versus prior snapshot.
# Positive values for "lower-better" metrics mean max allowed increase.
DELTA_GUARDRAILS = {
    "top1_accuracy_pct_max_drop": 0.5,
    "top5_accuracy_pct_max_drop": 0.5,
    "playoff_f1_max_drop": 0.005,
    "average_winner_rank_max_increase": 0.10,
    "brier_playoff_max_increase": 0.005,
    "brier_cup_max_increase": 0.005,
    "log_loss_playoff_max_increase": 0.010,
    "calibration_error_max_increase": 0.010,
}

CONTRACT_VERSION = "phase-3-tiered-cup-vegas-target-2026-02-15"
