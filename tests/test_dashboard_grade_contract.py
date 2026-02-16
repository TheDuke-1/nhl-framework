"""Tests for dashboard grading truth alignment with release and Cup-goal status."""

import importlib.util
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "grade_model_dashboard.py"

spec = importlib.util.spec_from_file_location("grade_model_dashboard", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def _dashboard_fixture() -> dict:
    return {
        "teams": [{"team": f"T{i}"} for i in range(32)],
        "playoffPicture": {"ok": True},
        "bracket": {"ok": True},
        "backtest": {"ok": True},
        "glossary": {"ok": True},
        "featureWeights": {"ok": True},
        "roundAdvancement": {"ok": True},
        "meta": {"generated": datetime.now(timezone.utc).isoformat()},
    }


def test_dashboard_score_is_capped_when_release_fails() -> None:
    dashboard = _dashboard_fixture()
    phase7 = {"status": "FAIL"}
    benchmark = {"vegas": {"cup_target": {"goal_met": False}}}
    score, detail = module._score_dashboard(dashboard, phase7, benchmark)
    assert score <= 82.0
    assert detail["release_status"] == "FAIL"
    assert detail["cup_goal_met"] is False


def test_dashboard_score_can_be_high_only_when_release_and_goal_pass() -> None:
    dashboard = _dashboard_fixture()
    phase7 = {"status": "PASS"}
    benchmark = {"vegas": {"cup_target": {"goal_met": True}}}
    score, detail = module._score_dashboard(dashboard, phase7, benchmark)
    assert score >= 90.0
    assert detail["release_status"] == "PASS"
    assert detail["cup_goal_met"] is True


def test_ship_gate_resolution_prefers_strict_status_from_latest_bundle() -> None:
    phase7_bundle = {
        "shipGateStatus": "FAIL",
        "localAdvisoryStatus": "PASS",
        "strict": {"status": "FAIL", "commands": []},
        "advisory": {"status": "PASS", "commands": []},
    }
    resolved = module._resolve_ship_gate_phase7(phase7_bundle)
    assert resolved["status"] == "FAIL"

    dashboard = _dashboard_fixture()
    benchmark = {"vegas": {"cup_target": {"goal_met": True}}}
    score, detail = module._score_dashboard(dashboard, resolved, benchmark)
    assert score <= 82.0
    assert detail["release_status"] == "FAIL"
