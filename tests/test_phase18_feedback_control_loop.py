"""Unit tests for phase18 feedback-control loop helpers."""

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "run_phase18_feedback_control_loop.py"

spec = importlib.util.spec_from_file_location("run_phase18_feedback_control_loop", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_control_mode_prioritizes_downside_recovery() -> None:
    mode = module._infer_control_mode(strong_gap=0.004, stagnation_streak=0, downside_regression_streak=2)
    assert mode == "DOWNSIDE_RECOVERY"


def test_control_mode_escalates_when_gap_and_stagnation_persist() -> None:
    mode = module._infer_control_mode(strong_gap=0.010, stagnation_streak=2, downside_regression_streak=0)
    assert mode == "ESCALATE_EXPLORATION"


def test_phase16_params_expand_under_escalation() -> None:
    params = module._recommend_phase16_params(
        control_mode="ESCALATE_EXPLORATION",
        strong_gap=0.015,
        stagnation_streak=3,
    )
    assert params["PHASE16_CANDIDATE_BUDGET"] >= 34
    assert params["PHASE16_STAGE1_TOP_N"] >= 16
    assert params["PHASE16_MAX_STAGE2_EVALS"] >= 8


def test_phase17_params_tighten_in_downside_recovery() -> None:
    params = module._recommend_phase17_params(
        control_mode="DOWNSIDE_RECOVERY",
        downside_regression_streak=1,
        baseline_min_season_edge=-0.014,
    )
    assert params["PHASE17_MIN_POSITIVE_RATIO"] >= 0.90
    assert params["PHASE17_MAX_NEGATIVE_SEASON_RATIO"] <= 0.20
    assert params["PHASE17_MAX_EDGE_DROP_VS_BASELINE"] <= 0.0005


def test_update_state_tracks_stagnation_and_downside_streaks() -> None:
    before = module._default_state()
    before.update(
        {
            "iteration": 4,
            "stagnationStreak": 1,
            "downsideRegressionStreak": 1,
            "strongGapStreak": 2,
            "lastBestEdge": 0.0200,
        }
    )
    metrics = {
        "phase16BestEdge": 0.0202,  # below min improvement threshold in this test
        "phase16StrongGap": 0.009,
        "phase17DownsideMinSeasonEdgeDelta": -0.002,
    }
    after = module._update_state(before, metrics, min_edge_improvement=0.0005)
    assert after["iteration"] == 5
    assert after["stagnationStreak"] == 2
    assert after["downsideRegressionStreak"] == 2
    assert after["strongGapStreak"] == 3


def test_env_command_has_stable_sorted_keys() -> None:
    cmd = module._build_env_command(
        "scripts/run_phase16_adaptive_learning_loop.py",
        {"B_KEY": 2, "A_KEY": 1},
    )
    assert cmd.startswith("A_KEY=1 B_KEY=2 python3 scripts/run_phase16_adaptive_learning_loop.py")
