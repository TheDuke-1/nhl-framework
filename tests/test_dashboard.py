"""Tests for the production dashboard (index.html)."""

import pytest


class TestDashboardHTML:
    def test_nav_tabs_present(self, dashboard_soup):
        """New dashboard uses JS-rendered tabs. Check the tab buttons in HTML."""
        nav_text = dashboard_soup.get_text()
        for tab in ["Rankings", "Playoff Race", "Betting Value", "Bracket", "Model Performance", "Insights"]:
            assert tab in nav_text, f"Nav tab '{tab}' not found in dashboard"

    def test_tab_buttons_have_data_attributes(self, dashboard_soup):
        """Each tab button should have a data-tab attribute for JS routing."""
        tabs = dashboard_soup.find_all("button", class_="tab")
        assert len(tabs) == 6, f"Expected 6 tab buttons, found {len(tabs)}"
        expected = {"rankings", "playoff-race", "betting", "bracket", "performance", "insights"}
        actual = {btn.get("data-tab") for btn in tabs}
        assert actual == expected, f"Tab data attributes mismatch: {actual}"

    def test_tab_content_container_present(self, dashboard_soup):
        """The main content container must exist for JS to render into."""
        container = dashboard_soup.find(id="tab-content")
        assert container is not None, "No #tab-content container found"

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
