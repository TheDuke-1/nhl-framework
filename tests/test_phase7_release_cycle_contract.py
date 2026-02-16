"""Contract checks for dual-track Phase 7 release-cycle artifacts."""

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "run_phase7_release_cycle.py"

spec = importlib.util.spec_from_file_location("run_phase7_release_cycle", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_latest_report_schema_derives_ship_gate_from_strict() -> None:
    strict = {"status": "FAIL", "mode": "strict", "truthTier": "ship_gate"}
    advisory = {"status": "PASS", "mode": "advisory", "truthTier": "local_advisory"}
    latest = module._build_latest_report(strict, advisory)
    assert latest["shipGateStatus"] == "FAIL"
    assert latest["localAdvisoryStatus"] == "PASS"
    assert latest["strict"]["truthTier"] == "ship_gate"
    assert latest["advisory"]["truthTier"] == "local_advisory"


def test_failure_reason_extracts_concrete_validate_data_stale_reason() -> None:
    output = (
        "❌ VALIDATION FAILED - 1 issue(s) found:\n"
        "  ⚠️  NST: Data is 10 days old (fetched: 2026-02-05)\n"
        "⚠️  Strict mode treats warnings as failures."
    )
    reason = module._extract_failure_reason("python3 scripts/validate_data.py --strict", output, "")
    assert reason == "NST: Data is 10 days old (fetched: 2026-02-05)"


def test_script_declares_dual_track_output_paths() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "phase7_release_cycle_strict.json" in source
    assert "phase7_release_cycle_advisory.json" in source
    assert "phase7_release_cycle_latest.json" in source
    assert "data_refresh_heartbeat.json" in source
    assert "phase7.refresh_health_gate" in source
    assert "--mode" in source
    assert "\"ship_gate\"" in source
    assert "\"local_advisory\"" in source


def test_refresh_health_gate_fails_when_critical_sources_unhealthy() -> None:
    refresh_meta = {
        "heartbeat": {
            "overall": {"criticalHealthy": False},
            "sources": {
                "nhl_api": {"critical": True, "health": "down", "message": "dns failure"},
                "nst": {"critical": True, "health": "healthy", "message": "ok"},
            },
        }
    }
    run = module._build_refresh_health_gate_run("strict", refresh_meta)
    assert run["returncode"] == 1
    assert "HEALTH_FAIL" in run["stderr"]
