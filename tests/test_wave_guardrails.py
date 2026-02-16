"""Regression checks for superhuman wave guardrails and prevention controls."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (PROJECT_ROOT / rel_path).read_text(encoding="utf-8")


def test_phase_search_scripts_carry_market_blend() -> None:
    for rel in (
        "scripts/run_phase10_ab_top1_recovery.py",
        "scripts/run_phase11_constrained_edge_batch.py",
        "scripts/run_phase12_goal_gap_closure.py",
        "scripts/run_phase13_eligible_feature_push.py",
    ):
        source = _read(rel)
        assert "cup_market_prior_blend" in source, f"{rel} must include market blend in candidate overrides"


def test_validate_data_defaults_to_strict() -> None:
    source = _read("scripts/validate_data.py")
    assert "default=True" in source
    assert "--allow-warnings" in source


def test_workflow_enforces_strict_validation() -> None:
    source = _read(".github/workflows/update-stats.yml")
    assert "run: python scripts/validate_data.py --strict" in source


def test_workflow_does_not_silence_core_fetch_or_model_failures() -> None:
    source = _read(".github/workflows/update-stats.yml")
    core_blocks = (
        "Fetch NHL API data",
        "Fetch MoneyPuck data",
        "Scrape Natural Stat Trick",
        "Generate superhuman predictions",
    )
    for block in core_blocks:
        marker = f"- name: {block}"
        idx = source.find(marker)
        assert idx >= 0, f"missing workflow step: {block}"
        segment = source[idx: idx + 280]
        assert "continue-on-error: true" not in segment, f"{block} should fail loudly"


def test_phase8_14_orchestrator_runs_actual_phase10_to_13_pipeline() -> None:
    source = _read("scripts/run_phases_8_to_14.py")
    required = (
        "scripts/run_phase8_vegas_truth_lock.py",
        "scripts/run_phase9_cup_edge_optimization.py",
        "scripts/run_phase10_ab_top1_recovery.py",
        "scripts/run_phase11_constrained_edge_batch.py",
        "scripts/run_phase12_goal_gap_closure.py",
        "scripts/run_phase13_eligible_feature_push.py",
        "scripts/verify_benchmark_contract.py",
        "scripts/run_phase7_release_cycle.py",
    )
    for marker in required:
        assert marker in source, f"phase8-14 orchestrator missing required step: {marker}"
    assert "PHASE_TIMEOUT_SECONDS" in source
    assert "timeout=PHASE_TIMEOUT_SECONDS" in source
    assert "_clean_output(exc.stdout)" in source
    assert "\"timeoutSeconds\": PHASE_TIMEOUT_SECONDS" in source


def test_phase13_uses_adaptive_frontier_when_prefilter_is_empty() -> None:
    source = _read("scripts/run_phase13_eligible_feature_push.py")
    assert "adaptive_frontier_active = False" in source
    assert "adaptiveFrontierEvaluated" in source
    assert "BLOCKED_BY_POSITIVE_RATIO_FLOOR_FRONTIER_EVALUATED" in source
    assert "and not adaptive_frontier_active" in source


def test_verify_model_performance_enforces_strict_fallback_guards() -> None:
    source = _read("scripts/verify_model_performance.py")
    assert "--require-series-data" in source
    assert "--require-oof-cup-calibration" in source
    assert "\"strict_verification\": True" in source
    assert "\"require_series_data_in_strict_mode\"" in source
    assert "\"require_oof_cup_calibration_in_strict_mode\"" in source
