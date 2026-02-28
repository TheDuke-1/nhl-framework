"""Interaction-focused regression tests for dashboard JS modules."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (PROJECT_ROOT / rel_path).read_text(encoding="utf-8")


def test_rankings_sorting_no_inline_onclick() -> None:
    source = _read("js/rankings.js")
    assert 'onclick="Utils.sortTable' not in source
    assert "data-sort-col" in source


def test_betting_has_american_odds_validation() -> None:
    source = _read("js/betting.js")
    assert "function normalizeOdds" in source
    assert "Math.abs(odds) < 100" in source
    assert "odds-input-invalid" in source


def test_performance_includes_checkpoint_proof_markers() -> None:
    source = _read("js/performance.js")
    assert "Games 0 (G0)" in source
    assert "Games 20 (G20)" in source
    assert "Games 40 (G40)" in source
    assert "Games 60 (G60)" in source


def test_app_has_stale_data_banner_logic() -> None:
    source = _read("js/app.js")
    assert "updateDataStatusBanner" in source
    assert "staleThresholdDays" in source
    assert "embedded-fallback" in source
    assert "reports/phase7_release_cycle_latest.json" in source
    assert "reports/dashboard_feedback_loop_latest.json" in source


def test_mission_control_shows_strict_and_advisory_release_status() -> None:
    source = _read("js/mission-control.js")
    assert "Release Ready (Strict)" in source
    assert "Release Cycle (Strict)" in source
    assert "Local Advisory Status" in source
    assert "Release Decision Trace (Strict)" in source
    assert "Finalization Gate (Dashboard Feedback)" in source


def test_phase16_learning_loop_markers_present() -> None:
    mission = _read("js/mission-control.js")
    performance = _read("js/performance.js")
    assert "Adaptive Learning Loop" in mission
    assert "Learning Blockers (Phase 16-18)" in mission
    assert "Phase 16 target tier" in performance
    assert "phase16" in performance
    assert "Phase 17 downside lane" in performance
    assert "Phase 18 feedback loop" in performance


def test_bracket_has_coherent_path_rendering_guards() -> None:
    source = _read("js/bracket.js")
    assert "projected.coherentPath || buildCoherentPath(projected)" in source
    assert "Most-Likely Path Champion" in source
    assert "selectMatchingMatchup(" in source


def test_performance_shows_distinct_baseline_note() -> None:
    source = _read("js/performance.js")
    assert "comparison.skippedIdenticalRuns" in source
    assert "last distinct snapshot" in source


def test_mission_overflow_css_guards_present() -> None:
    source = _read("css/style.css")
    assert ".mission-trace-row code" in source
    assert "overflow-wrap: anywhere;" in source
    assert "word-break: break-word;" in source
    assert "flex-wrap: wrap;" in source
