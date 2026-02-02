#!/usr/bin/env python3
"""
Validate verified historical NHL data files.

Cross-references each season's JSON for:
- Team count matches expected
- Cup winner matches known results
- PP% and PK% are populated and in valid ranges
- CF% in valid range (if advanced stats present)
- Correct number of playoff teams (16, or 24 for 2020 bubble)
- playoffRoundsWon sanity (exactly 1 team with 4, 1 with 3, etc.)

Usage:
    python scripts/validate_historical.py
"""

import json
import sys
from pathlib import Path

# Import ground truth from the fetch script (single source of truth)
sys.path.insert(0, str(Path(__file__).parent))
from fetch_historical import CUP_RESULTS, EXPECTED_TEAMS

VERIFIED_DIR = Path(__file__).parent.parent / "data" / "historical" / "verified"


def validate_season(year, data):
    """Validate a single season's data. Returns list of issue strings."""
    issues = []
    teams = data.get("teams", {})
    meta = data.get("_metadata", {})

    # Team count
    expected_count = EXPECTED_TEAMS.get(year, 30)
    if len(teams) != expected_count:
        issues.append(f"Team count: {len(teams)} (expected {expected_count})")

    # Cup winner
    cup_info = CUP_RESULTS.get(year, {})
    expected_winner = cup_info.get("winner")
    if expected_winner:
        actual_winner = meta.get("cupWinner", "")
        if actual_winner != expected_winner:
            issues.append(f"Cup winner mismatch: {actual_winner} (expected {expected_winner})")
        winners = [a for a, t in teams.items() if t.get("wonCup")]
        if len(winners) != 1:
            issues.append(f"wonCup flag: {len(winners)} teams (expected 1)")
        elif winners[0] != expected_winner:
            issues.append(f"wonCup team {winners[0]} != expected {expected_winner}")

    # Playoff teams
    playoff_teams = {a for a, t in teams.items() if t.get("madePlayoffs")}
    expected_playoff = 24 if year == 2020 else 16
    if len(playoff_teams) != expected_playoff:
        issues.append(f"Playoff teams: {len(playoff_teams)} (expected {expected_playoff})")

    # Rounds won sanity
    rounds = [t.get("playoffRoundsWon", 0) for a, t in teams.items() if t.get("madePlayoffs")]
    cup_winners = sum(1 for r in rounds if r == 4)
    finalists = sum(1 for r in rounds if r == 3)
    if cup_winners != 1:
        issues.append(f"Teams with 4 rounds won: {cup_winners} (expected 1)")
    if finalists != 1:
        issues.append(f"Teams with 3 rounds won: {finalists} (expected 1)")

    # PP% / PK% ranges (8-35 PP%, 65-95 PK% — ANA 2021 had 8.9% PP)
    pp_missing = sum(1 for t in teams.values() if t.get("ppPct", 0) == 0)
    pk_missing = sum(1 for t in teams.values() if t.get("pkPct", 0) == 0)
    if pp_missing > 0:
        issues.append(f"PP% missing for {pp_missing} teams")
    if pk_missing > 0:
        issues.append(f"PK% missing for {pk_missing} teams")

    for abbrev, t in teams.items():
        pp = t.get("ppPct", 0)
        pk = t.get("pkPct", 0)
        if pp > 0 and (pp < 8 or pp > 35):
            issues.append(f"{abbrev}: PP% = {pp} out of range (8-35)")
        if pk > 0 and (pk < 65 or pk > 95):
            issues.append(f"{abbrev}: PK% = {pk} out of range (65-95)")

    # CF% range (only if advanced stats present)
    for abbrev, t in teams.items():
        if not t.get("hasAdvanced"):
            continue
        cf = t.get("cfPct", 50)
        if cf < 35 or cf > 65:
            issues.append(f"{abbrev}: CF% = {cf} out of range (35-65)")

    return issues


def main():
    files = sorted(VERIFIED_DIR.glob("season_*.json"))
    if not files:
        print(f"No verified season files found in {VERIFIED_DIR}")
        sys.exit(1)

    total_issues = 0
    print(f"Validating {len(files)} seasons in {VERIFIED_DIR}\n")

    for filepath in files:
        try:
            year = int(filepath.stem.split("_")[1])
        except (ValueError, IndexError):
            print(f"  SKIP: Could not parse year from {filepath.name}")
            continue

        with open(filepath) as f:
            data = json.load(f)

        issues = validate_season(year, data)
        teams = data.get("teams", {})
        playoff_count = sum(1 for t in teams.values() if t.get("madePlayoffs"))
        pp_count = sum(1 for t in teams.values() if t.get("ppPct", 0) > 0)
        adv_count = sum(1 for t in teams.values() if t.get("hasAdvanced"))

        status = "PASS" if not issues else "FAIL"
        print(f"  {year} ({len(teams)} teams, {playoff_count} playoff, {pp_count} PP%, {adv_count} adv): {status}")

        if issues:
            for issue in issues:
                print(f"    - {issue}")
            total_issues += len(issues)

    print(f"\nTotal: {len(files)} seasons, {total_issues} issues")
    sys.exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()
