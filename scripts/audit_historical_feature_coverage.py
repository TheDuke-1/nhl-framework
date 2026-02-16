#!/usr/bin/env python3
"""
Audit historical advanced-feature override coverage.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superhuman.real_data_loader import get_advanced_override_coverage


REPORT_JSON = PROJECT_ROOT / "reports" / "feature_coverage_latest.json"
REPORT_MD = PROJECT_ROOT / "reports" / "FEATURE_COVERAGE_LATEST.md"


def _write_markdown(report: dict) -> None:
    lines = [
        "# Historical Advanced Feature Coverage",
        "",
        f"Generated: `{report['generatedAt']}`",
        "",
        "## Summary",
        "",
        f"- Accepted seasons: {report['acceptedSeasons']}/{report['totalSeasons']}",
        f"- Accepted season ratio: {report['acceptedSeasonRatio']:.3f}",
        f"- Raw team coverage ratio: {report['rawTeamCoverageRatio']:.3f}",
        f"- Accepted team coverage ratio: {report['acceptedTeamCoverageRatio']:.3f}",
        f"- Minimum team coverage threshold per season: {report['minTeamCoverage']}",
        "",
        "## Per-Season Coverage",
        "",
        "| Season | Override File | Raw Team Count | Accepted |",
        "|---|---:|---:|---:|",
    ]

    for row in report["seasons"]:
        lines.append(
            f"| {row['season']} | {'Yes' if row['fileExists'] else 'No'} | "
            f"{row['teamCountRaw']} | {'Yes' if row['accepted'] else 'No'} |"
        )

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n")


def main() -> int:
    coverage = get_advanced_override_coverage(start_season=2010, end_season=2024)
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        **coverage,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2))
    _write_markdown(report)

    print(f"Coverage JSON: {REPORT_JSON}")
    print(f"Coverage MD: {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
