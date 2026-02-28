"""Timeout safety tests for orchestration scripts."""

import importlib.util
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_module(rel_path: str, module_name: str):
    module_path = PROJECT_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_team_cycle_run_returns_timeout_record(monkeypatch) -> None:
    module = _load_module("scripts/run_superhuman_team_cycle.py", "run_superhuman_team_cycle_timeout")
    monkeypatch.setattr(module, "STEP_TIMEOUT_SECONDS", 7)

    def _timeout(*_args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=kwargs.get("args", "cmd"), timeout=kwargs.get("timeout", 7), output="partial")

    monkeypatch.setattr(module.subprocess, "run", _timeout)
    result = module._run(["python3", "scripts/noop.py"])

    assert result["returncode"] == 124
    assert result["timedOut"] is True
    assert "Timed out after 7s" in result["stderr"]


def test_phase18_recommended_steps_mark_timeouts(monkeypatch) -> None:
    module = _load_module("scripts/run_phase18_feedback_control_loop.py", "run_phase18_feedback_control_loop_timeout")
    monkeypatch.setattr(module, "RECOMMENDED_STEP_TIMEOUT_SECONDS", 5)

    def _timeout(*_args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=kwargs.get("args", "cmd"), timeout=kwargs.get("timeout", 5), output="partial")

    monkeypatch.setattr(module.subprocess, "run", _timeout)
    results = module._run_recommended({}, {})

    assert len(results) == 2
    assert all(row["returncode"] == 124 for row in results)
    assert all(row["timedOut"] is True for row in results)
    assert all("Timed out after 5s" in row["stderr"] for row in results)


def test_phases_3_to_7_returns_timeout_exit_code(monkeypatch) -> None:
    module = _load_module("scripts/run_phases_3_to_7.py", "run_phases_3_to_7_timeout")
    monkeypatch.setattr(module, "PHASE_TIMEOUT_SECONDS", 9)

    def _timeout(*_args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=kwargs.get("args", "cmd"), timeout=kwargs.get("timeout", 9))

    monkeypatch.setattr(module.subprocess, "run", _timeout)

    assert module.main() == 124
