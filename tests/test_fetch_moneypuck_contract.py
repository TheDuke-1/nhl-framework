"""Contracts for MoneyPuck fetch behavior."""

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MODULE_PATH = SCRIPTS_DIR / "fetch_moneypuck.py"


class _DummyResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            err = requests.HTTPError(f"HTTP {self.status_code}")
            err.response = self
            raise err


def _load_module(name: str):
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_fetch_tries_start_year_then_fallback(monkeypatch) -> None:
    module = _load_module("fetch_moneypuck_contract_fallback")
    calls = []

    def _fake_get(url, headers=None, timeout=0):
        calls.append(url)
        if "/2025/" in url:
            return _DummyResponse(200, "team,situation\nANA,5on5\n")
        return _DummyResponse(404, "")

    monkeypatch.setattr(module.requests, "get", _fake_get)

    csv_text, season, url = module.fetch_moneypuck_csv()

    assert season == 2025
    assert "/2025/" in url
    assert csv_text.startswith("team,situation")
    assert len(calls) >= 1


def test_main_returns_nonzero_on_fetch_failure(monkeypatch) -> None:
    module = _load_module("fetch_moneypuck_contract_fail")

    def _boom():
        raise RuntimeError("forbidden")

    monkeypatch.setattr(module, "fetch_moneypuck_csv", _boom)

    assert module.main() == 1
