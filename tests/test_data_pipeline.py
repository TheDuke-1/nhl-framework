"""Tests for the data pipeline output (teams.json)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from config import ALL_TEAMS, TEAM_INFO, VALID_RANGES


REQUIRED_FIELDS = ["team", "name", "conf", "div", "gp", "w", "l", "pts", "weight"]


class TestTeamsJson:
    def test_has_32_teams(self, teams_list):
        assert len(teams_list) == 32

    def test_required_fields_present(self, teams_list):
        for team in teams_list:
            for field in REQUIRED_FIELDS:
                assert field in team, f"{team.get('team', '???')} missing '{field}'"

    def test_weight_field_is_numeric(self, teams_list):
        for team in teams_list:
            assert isinstance(team["weight"], (int, float)), (
                f"{team['team']} weight is not a number: {type(team['weight'])}"
            )
            assert 0 <= team["weight"] <= 1000, (
                f"{team['team']} weight {team['weight']} outside reasonable range 0-1000"
            )

    def test_all_team_abbreviations_present(self, teams_list):
        abbrevs = {t["team"] for t in teams_list}
        assert abbrevs == set(ALL_TEAMS)

    def test_conference_division_assignments(self, teams_list):
        for team in teams_list:
            abbrev = team["team"]
            expected = TEAM_INFO[abbrev]
            assert team["conf"] == expected["conf"], (
                f"{abbrev} conf: expected {expected['conf']}, got {team['conf']}"
            )
            assert team["div"] == expected["div"], (
                f"{abbrev} div: expected {expected['div']}, got {team['div']}"
            )

    def test_no_duplicate_teams(self, teams_list):
        abbrevs = [t["team"] for t in teams_list]
        assert len(abbrevs) == len(set(abbrevs))

    def test_metadata_present(self, teams_data):
        meta = teams_data["_metadata"]
        assert "version" in meta
        assert "generatedAt" in meta
        assert "sources" in meta
        assert isinstance(meta["sources"], dict)

    def test_numeric_fields_in_valid_ranges(self, teams_list):
        for team in teams_list:
            for field, (lo, hi) in VALID_RANGES.items():
                if field in team and team[field] is not None:
                    val = team[field]
                    # PDO in data is ratio (0.95-1.05), config range is pct (95-105)
                    if field == "pdo" and val < 2:
                        val = val * 100
                    assert lo <= val <= hi, (
                        f"{team['team']} {field}={val} outside [{lo}, {hi}]"
                    )
