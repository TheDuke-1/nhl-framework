#!/usr/bin/env python3
"""
League calendar context used by freshness and release gates.

The goal is to distinguish:
- normal periods where data should refresh frequently
- scheduled pauses where older stats can be expected
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SCHEDULED_BREAK_WINDOWS: List[Dict[str, Any]] = [
    {
        "name": "2026 Winter Olympics Break",
        "start": "2026-02-06T00:00:00Z",
        "end": "2026-02-24T23:59:59Z",
        "reason": "nhl_olympic_break",
        # During planned league pauses we still require daily health check-ins.
        "heartbeatMaxAgeHours": 30,
    }
]


def _parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def get_data_activity_context(now: Optional[datetime] = None) -> Dict[str, Any]:
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    for window in SCHEDULED_BREAK_WINDOWS:
        start = _parse_utc(str(window["start"]))
        end = _parse_utc(str(window["end"]))
        if start <= now_utc <= end:
            return {
                "activityState": "scheduled_break",
                "windowName": window["name"],
                "reason": window["reason"],
                "heartbeatMaxAgeHours": int(window["heartbeatMaxAgeHours"]),
                "windowStart": start.isoformat(),
                "windowEnd": end.isoformat(),
                "evaluatedAt": now_utc.isoformat(),
            }
    return {
        "activityState": "regular_season",
        "windowName": None,
        "reason": None,
        "heartbeatMaxAgeHours": None,
        "windowStart": None,
        "windowEnd": None,
        "evaluatedAt": now_utc.isoformat(),
    }
