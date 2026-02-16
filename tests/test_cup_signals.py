"""Tests for supplemental Cup signal features."""

import math

from superhuman.cup_signal_loader import (
    calculate_goalie_injury_playoff_impact,
    calculate_market_close_movement_signal,
    calculate_series_history_signal,
)
from superhuman.data_models import FeatureVector


def test_feature_vector_includes_new_cup_signals():
    names = FeatureVector.feature_names()
    assert "series_history_signal" in names
    assert "market_close_movement_signal" in names
    assert "goalie_injury_playoff_impact" in names

    vector = FeatureVector(team="TST", season=2026)
    arr = vector.to_array()
    assert len(arr) == len(names)


def test_series_history_signal_is_finite():
    value = calculate_series_history_signal("FLA", 2024)
    assert math.isfinite(value)


def test_market_movement_signal_is_finite():
    value = calculate_market_close_movement_signal("COL", 2024)
    assert math.isfinite(value)


def test_goalie_injury_impact_signal_is_finite():
    value = calculate_goalie_injury_playoff_impact("BUF", 2026, current_gsax=0.0)
    assert math.isfinite(value)

