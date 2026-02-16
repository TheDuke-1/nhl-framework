"""Regression tests for strict verification fallback guardrails."""

from types import SimpleNamespace

import numpy as np
import pytest

from superhuman.models import EnsemblePredictor, MonteCarloSimulator
import superhuman.playoff_series_model as playoff_series_model
import superhuman.validation as validation
from superhuman.data_models import TeamSeason


def test_strict_mode_rejects_in_sample_cup_calibration(monkeypatch):
    model = EnsemblePredictor(
        use_cup_calibration=True,
        strict_verification=True,
        require_oof_cup_calibration_in_strict_mode=True,
    )

    monkeypatch.setattr(
        model,
        "_generate_cup_oof_predictions",
        lambda training_data: (np.array([]), np.array([])),
    )

    with pytest.raises(RuntimeError, match="out-of-fold Cup calibration"):
        model._fit_cup_calibrator(training_data=[], train_features=[])


def test_strict_mode_requires_series_training_data(monkeypatch):
    # Simulate missing/untrained series model regardless of local data files.
    monkeypatch.setattr(
        playoff_series_model,
        "get_series_predictor",
        lambda: SimpleNamespace(is_fitted=False),
    )

    with pytest.raises(RuntimeError, match="playoff series training data"):
        MonteCarloSimulator(
            n_simulations=10,
            use_enhanced_model=True,
            require_series_data=True,
        )


def test_backtest_skips_early_strict_oof_windows(monkeypatch):
    teams = [f"T{i:02d}" for i in range(16)]
    historical = []
    for season in range(2010, 2017):
        for idx, team in enumerate(teams):
            historical.append(
                TeamSeason(
                    team=team,
                    season=season,
                    games_played=82,
                    points=100 - idx,
                    made_playoffs=idx < 8,
                    won_cup=idx == 0,
                )
            )

    class _DummyModel:
        def __init__(self, **kwargs):
            self.strict = bool(kwargs.get("strict_verification", False))
            self.require_oof = bool(
                kwargs.get("require_oof_cup_calibration_in_strict_mode", False)
            )

        def fit(self, train_data):
            train_seasons = {t.season for t in train_data}
            # This should never trigger after the early-window skip guard.
            if self.strict and self.require_oof and len(train_seasons) < 5:
                raise AssertionError("strict OOF underpowered window was not skipped")

        def predict(self, test_data):
            return [
                SimpleNamespace(
                    team=t.team,
                    playoff_probability=0.60 if t.made_playoffs else 0.40,
                    cup_win_probability=0.08 if t.team == "T00" else 0.02,
                )
                for t in test_data
            ]

    monkeypatch.setattr(validation, "EnsemblePredictor", _DummyModel)

    report = validation.generate_backtest_report(
        historical_data=historical,
        cache_path=None,
        force_refresh=True,
        model_overrides={
            "strict_verification": True,
            "require_oof_cup_calibration_in_strict_mode": True,
        },
    )
    skipped = report.get("walkForwardAudit", {}).get("skippedSplits", [])
    oof_skipped_seasons = sorted(
        item["heldOutSeason"]
        for item in skipped
        if item.get("reason") == "insufficient_oof_cup_history"
    )
    assert oof_skipped_seasons == [2014]
