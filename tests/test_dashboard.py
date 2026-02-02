"""Tests for the production dashboard (index.html)."""

import pytest


class TestDashboardHTML:
    def test_nav_tabs_present(self, dashboard_soup):
        nav_text = dashboard_soup.get_text()
        for tab in ["Full Matrix", "HDCF%", "Playoff Odds", "Weights"]:
            assert tab in nav_text, f"Nav tab '{tab}' not found in dashboard"

    def test_conference_filter_buttons(self, dashboard_soup):
        text = dashboard_soup.get_text()
        assert "Eastern" in text or "East" in text
        assert "Western" in text or "West" in text

    def test_tier_legend_present(self, dashboard_soup):
        text = dashboard_soup.get_text()
        for tier in ["Elite", "Contender", "Bubble", "Longshot"]:
            assert tier in text, f"Tier '{tier}' not found in dashboard"

    def test_page_title_contains_nhl(self, dashboard_soup):
        title = dashboard_soup.find("title")
        assert title is not None, "No <title> tag found"
        assert "NHL" in title.string or "nhl" in title.string.lower()

    def test_no_unclosed_tags(self, dashboard_soup):
        html_str = str(dashboard_soup)
        for tag in ["div", "section", "script", "style"]:
            open_count = html_str.count(f"<{tag}")
            close_count = html_str.count(f"</{tag}>")
            assert open_count == close_count, (
                f"Unclosed <{tag}>: {open_count} opened, {close_count} closed"
            )

    def test_data_freshness_element(self, dashboard_soup):
        freshness = (
            dashboard_soup.find(id="lastUpdated")
            or dashboard_soup.find(class_="last-updated")
            or dashboard_soup.find(string=lambda s: s and "last updated" in s.lower())
            or dashboard_soup.find(string=lambda s: s and "as of" in s.lower())
        )
        assert freshness is not None, "No data freshness indicator found"
