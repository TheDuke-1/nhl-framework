"""Tests for superhuman model output (dashboard_data.json)."""

import pytest

VALID_TIERS = {"Elite", "Contender", "Bubble", "Longshot"}

EXPECTED_TIER_COLORS = {
    "Elite": "#10b981",
    "Contender": "#3b82f6",
    "Bubble": "#f59e0b",
    "Longshot": "#ef4444",
}


class TestDashboardData:
    def test_has_32_teams(self, dashboard_data):
        assert len(dashboard_data["teams"]) == 32

    def test_cup_probabilities_sum_to_100(self, dashboard_data):
        total = sum(t["cupProbability"] for t in dashboard_data["teams"])
        assert abs(total - 100) < 5, f"Cup probabilities sum to {total}, expected ~100"

    def test_playoff_probabilities_in_range(self, dashboard_data):
        for team in dashboard_data["teams"]:
            prob = team["playoffProbability"]
            assert 0 <= prob <= 100, (
                f"{team['code']} playoffProbability={prob} outside [0, 100]"
            )

    def test_valid_tiers(self, dashboard_data):
        for team in dashboard_data["teams"]:
            assert team["tier"] in VALID_TIERS, (
                f"{team['code']} has invalid tier '{team['tier']}'"
            )

    def test_tier_colors_match(self, dashboard_data):
        for team in dashboard_data["teams"]:
            expected_color = EXPECTED_TIER_COLORS[team["tier"]]
            assert team["tierColor"] == expected_color, (
                f"{team['code']} tier '{team['tier']}' has color "
                f"'{team['tierColor']}', expected '{expected_color}'"
            )

    def test_meta_section(self, dashboard_data):
        meta = dashboard_data["meta"]
        assert "season" in meta
        assert "modelVersion" in meta
        assert "generated" in meta
