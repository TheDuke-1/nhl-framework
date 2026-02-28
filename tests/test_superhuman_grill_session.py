"""Unit tests for limiting-factor accountability in grill session report."""

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "run_superhuman_grill_session.py"

spec = importlib.util.spec_from_file_location("run_superhuman_grill_session", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_limiting_factors_include_model_release_dashboard_controls() -> None:
    snapshot = {
        "benchmark": {"edge": 0.02, "strongTarget": 0.03},
        "phase16": {"strongGap": 0.01},
        "phase17": {"downsideMinSeasonEdgeDelta": -0.001, "recommendation": "KEEP_BASELINE"},
        "phase18": {"controlMode": "TARGET_CLOSURE"},
        "phase7": {"strictStatus": "FAIL"},
        "dashboardFeedback": {"status": "FAIL", "errors": ["Bracket mismatch"]},
        "benchmarkComparison": {"skippedIdenticalRuns": 2},
    }
    factors = module._build_limiting_factors(snapshot)
    ids = {row["id"] for row in factors}
    assert {"LF-01", "LF-02", "LF-03", "LF-04", "LF-05"}.issubset(ids)


def test_limiting_factors_emit_fallback_when_all_clear() -> None:
    snapshot = {
        "benchmark": {"edge": 0.031, "strongTarget": 0.03},
        "phase16": {"strongGap": 0.0},
        "phase17": {"downsideMinSeasonEdgeDelta": 0.0, "recommendation": "USE_PHASE17_CANDIDATE"},
        "phase18": {"controlMode": "TARGET_CLOSURE"},
        "phase7": {"strictStatus": "PASS"},
        "dashboardFeedback": {"status": "PASS", "errors": []},
        "benchmarkComparison": {"skippedIdenticalRuns": 0},
    }
    factors = module._build_limiting_factors(snapshot)
    assert len(factors) == 1
    assert factors[0]["id"] == "LF-00"
