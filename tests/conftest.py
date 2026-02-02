"""Shared fixtures for NHL Playoff Framework tests."""

import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@pytest.fixture(scope="session")
def teams_data():
    """Load data/teams.json once for the entire test session."""
    path = DATA_DIR / "teams.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def teams_list(teams_data):
    """Just the teams array from teams.json."""
    return teams_data["teams"]


@pytest.fixture(scope="session")
def dashboard_data():
    """Load dashboard_data.json once for the entire test session."""
    path = PROJECT_ROOT / "dashboard_data.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def dashboard_soup():
    """Parse index.html with BeautifulSoup."""
    path = PROJECT_ROOT / "index.html"
    with open(path) as f:
        return BeautifulSoup(f.read(), "lxml")
