"""Contract checks for NHL standings fallback provider behavior."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (PROJECT_ROOT / rel_path).read_text(encoding="utf-8")


def test_fetch_nhl_api_declares_backup_provider_chain() -> None:
    source = _read("scripts/fetch_nhl_api.py")
    assert "BACKUP_STANDINGS_URLS" in source
    assert "EXPECTED_STATIC_FALLBACK" in source
    assert "cache_snapshot" in source
    assert "BACKUP_PROVIDER_USED" in source


def test_refresh_data_maps_expected_static_success_to_expected_static_health() -> None:
    source = _read("scripts/refresh_data.py")
    assert "expected-static fallback check-in" in source
    assert "\"expected_static\"" in source
