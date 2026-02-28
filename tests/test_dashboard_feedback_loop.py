"""Unit tests for dashboard feedback-loop blocking checks."""

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "run_dashboard_feedback_loop.py"

spec = importlib.util.spec_from_file_location("run_dashboard_feedback_loop", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def _conf_fixture(prefix: str) -> dict:
    return {
        "round1": [
            {"higher": f"{prefix}1", "lower": f"{prefix}8", "higherWinProb": 60.0},
            {"higher": f"{prefix}2", "lower": f"{prefix}7", "higherWinProb": 55.0},
            {"higher": f"{prefix}3", "lower": f"{prefix}6", "higherWinProb": 45.0},
            {"higher": f"{prefix}4", "lower": f"{prefix}5", "higherWinProb": 58.0},
        ],
        "round2": [
            {
                "slot": 0,
                "matchups": [
                    {"teamA": f"{prefix}1", "teamB": f"{prefix}2", "teamAWinProb": 52.0, "matchupProb": 11.0}
                ],
            },
            {
                "slot": 1,
                "matchups": [
                    {"teamA": f"{prefix}6", "teamB": f"{prefix}4", "teamAWinProb": 49.0, "matchupProb": 9.0}
                ],
            },
        ],
        "confFinal": [
            {"teamA": f"{prefix}1", "teamB": f"{prefix}4", "teamAWinProb": 51.0, "matchupProb": 6.0}
        ],
    }


def test_bracket_coherence_passes_for_consistent_path() -> None:
    dashboard = {
        "bracket": {
            "projected": {
                "East": _conf_fixture("E"),
                "West": _conf_fixture("W"),
                "coherentPath": {
                    "cupFinalSelected": {"teamA": "E1", "teamB": "W1", "teamAWinProb": 52.0, "matchupProb": 2.0}
                },
            }
        }
    }
    result = module._check_bracket_coherence(dashboard)
    assert result["errors"] == []


def test_bracket_coherence_fails_without_coherent_path() -> None:
    dashboard = {
        "bracket": {
            "projected": {
                "East": _conf_fixture("E"),
                "West": _conf_fixture("W"),
            }
        }
    }
    result = module._check_bracket_coherence(dashboard)
    assert any("coherentPath.cupFinalSelected is missing" in err for err in result["errors"])


def test_scorecard_sanity_fails_on_identical_without_metadata() -> None:
    current = {"core": {"top1_accuracy_pct": 20.0}}
    benchmark = {"current": current, "previous": {"core": {"top1_accuracy_pct": 20.0}}}
    result = module._check_scorecard_sanity(benchmark)
    assert result["errors"]
    assert "identical" in result["errors"][0]


def test_scorecard_sanity_warns_when_identical_runs_are_tracked() -> None:
    current = {"core": {"top1_accuracy_pct": 20.0}}
    benchmark = {
        "current": current,
        "previous": {"core": {"top1_accuracy_pct": 20.0}},
        "comparison": {"skippedIdenticalRuns": 3},
    }
    result = module._check_scorecard_sanity(benchmark)
    assert result["errors"] == []
    assert result["warnings"]


def test_mission_overflow_and_bracket_guard_tokens_exist() -> None:
    result = module._check_mission_overflow_controls()
    assert result["errors"] == []
