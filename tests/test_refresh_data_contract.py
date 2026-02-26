"""Contracts for refresh_data source freshness helpers."""

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MODULE_PATH = SCRIPTS_DIR / "refresh_data.py"


def _load_module(name: str):
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_check_moneypuck_freshness_force_mode_reports_fresh(monkeypatch) -> None:
    module = _load_module("refresh_data_contract")

    monkeypatch.setattr(module, "check_data_freshness", lambda *_args, **_kwargs: (True, 0.1, 48))

    ok, message = module.check_moneypuck_freshness(force=True)

    assert ok is True
    assert "fresh" in message
