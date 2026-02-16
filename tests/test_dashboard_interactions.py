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


def test_mission_control_shows_strict_and_advisory_release_status() -> None:
    source = _read("js/mission-control.js")
    assert "Release Ready (Strict)" in source
    assert "Release Cycle (Strict)" in source
    assert "Local Advisory Status" in source
    assert "Release Decision Trace (Strict)" in source
