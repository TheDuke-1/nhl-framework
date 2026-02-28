"""Regression checks for phase18 feedback-loop integration surfaces."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (PROJECT_ROOT / rel_path).read_text(encoding="utf-8")


def test_team_cycle_runs_and_snapshots_phase18() -> None:
    source = _read("scripts/run_superhuman_team_cycle.py")
    assert "scripts/run_phase18_feedback_control_loop.py" in source
    assert "phase18Summary" in source
    assert "_load_phase18_snapshot" in source
    assert "scripts/run_dashboard_feedback_loop.py" in source
    assert "scripts/run_superhuman_grill_session.py" in source
    assert "dashboardFeedback" in source


def test_dashboard_generator_loads_phase18() -> None:
    source = _read("superhuman/dashboard_generator.py")
    assert "PHASE18_PATH" in source
    assert "\"phase18\": phase18" in source
    assert "edgeResearchTimestamp\": (phase18" in source


def test_app_fetches_phase18_report() -> None:
    source = _read("js/app.js")
    assert "reports/phase18_feedback_control_loop.json" in source
    assert "phase18 = {" in source
    assert "phase18 ? { phase18 } : {}" in source


def test_app_fetches_dashboard_feedback_report() -> None:
    source = _read("js/app.js")
    assert "loadDashboardFeedbackData" in source
    assert "reports/dashboard_feedback_loop_latest.json" in source
    assert "payload.dashboardFeedback = dashboardFeedback" in source


def test_mission_control_uses_phase18_feedback_signals() -> None:
    source = _read("js/mission-control.js")
    assert "phase18Summary" in source
    assert "phase18Actions" in source
    assert "Learning Blockers (Phase 16-18)" in source
    assert "Feedback mode:" in source
    assert "Finalization Gate (Dashboard Feedback)" in source
    assert "finalizationStatus" in source


def test_performance_tab_surfaces_phase18_snapshot() -> None:
    source = _read("js/performance.js")
    assert "Phase 18 feedback loop" in source
    assert "phase18Summary" in source


def test_grill_session_includes_feedback_controller_round() -> None:
    source = _read("scripts/run_superhuman_grill_session.py")
    assert "PHASE18_PATH" in source
    assert "\"challenger\": \"Feedback Controller\"" in source
    assert "\"phase18\":" in source
