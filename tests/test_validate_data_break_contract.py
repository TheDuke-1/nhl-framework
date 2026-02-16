"""Break-aware validation contract checks for data freshness handling."""

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "scripts" / "validate_data.py"

spec = importlib.util.spec_from_file_location("validate_data", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def _iso(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def test_break_heartbeat_allows_expected_static_source() -> None:
    context = {
        "activityState": "scheduled_break",
        "windowName": "Olympic break",
        "heartbeatMaxAgeHours": 30,
    }
    heartbeat = {
        "generatedAt": _iso(2),
        "sources": {
            "nhl_api": {"health": "expected_static"},
        },
    }
    assert module._source_heartbeat_allows_stale("NHL API", "nhl_api", context, heartbeat)


def test_break_heartbeat_rejects_stale_or_unhealthy_source() -> None:
    context = {
        "activityState": "scheduled_break",
        "windowName": "Olympic break",
        "heartbeatMaxAgeHours": 30,
    }
    stale_heartbeat = {
        "generatedAt": _iso(48),
        "sources": {"nhl_api": {"health": "healthy"}},
    }
    unhealthy_heartbeat = {
        "generatedAt": _iso(1),
        "sources": {"nhl_api": {"health": "down"}},
    }

    assert not module._source_heartbeat_allows_stale("NHL API", "nhl_api", context, stale_heartbeat)
    assert not module._source_heartbeat_allows_stale("NHL API", "nhl_api", context, unhealthy_heartbeat)

