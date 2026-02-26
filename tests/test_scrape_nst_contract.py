"""Contracts for scrape_nst exit status behavior."""

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MODULE_PATH = SCRIPTS_DIR / "scrape_nst.py"


def _load_module(name: str):
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_main_returns_nonzero_when_no_teams(monkeypatch) -> None:
    module = _load_module("scrape_nst_contract_empty")
    monkeypatch.setattr(module, "fetch_and_parse_nst", lambda: {})

    assert module.main() == 1


def test_main_returns_nonzero_on_fetch_exception(monkeypatch) -> None:
    module = _load_module("scrape_nst_contract_error")

    def _boom():
        raise RuntimeError("network down")

    monkeypatch.setattr(module, "fetch_and_parse_nst", _boom)

    assert module.main() == 1
