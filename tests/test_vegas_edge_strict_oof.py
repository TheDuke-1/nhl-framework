"""Regression tests for strict OOF Cup calibration behavior in Vegas diagnostics."""

from types import SimpleNamespace

from superhuman import vegas_edge
from superhuman.betting_odds_loader import TeamOdds
from superhuman.data_models import TeamSeason


def _historical_fixture() -> tuple[list[TeamSeason], list[str]]:
    teams = [f"T{i:02d}" for i in range(16)]
    rows: list[TeamSeason] = []
    for season in range(2010, 2016):
        for idx, team in enumerate(teams):
            rows.append(
                TeamSeason(
                    team=team,
                    season=season,
                    games_played=82,
                    points=100 - idx,
                    made_playoffs=idx < 8,
                    won_cup=idx == 0,
                )
            )
    return rows, teams


def _vegas_fixture(teams: list[str], season: int) -> dict[str, TeamOdds]:
    return {
        team: TeamOdds(
            team=team,
            season=season,
            cup_odds_american=900,
            cup_implied_prob=0.08 if team == "T00" else 0.02,
            playoff_odds_american=130,
            playoff_implied_prob=0.62 if team.startswith("T0") else 0.38,
            actual_made_playoffs=team.startswith("T0"),
            actual_won_cup=(team == "T00"),
        )
        for team in teams
    }


class _StrictAwareDummyModel:
    def __init__(self, **kwargs):
        self.strict = bool(kwargs.get("strict_verification", False))
        self.require_oof = bool(
            kwargs.get("require_oof_cup_calibration_in_strict_mode", False)
        )

    def fit(self, train_data: list[TeamSeason]) -> None:
        train_seasons = {t.season for t in train_data}
        if self.strict and self.require_oof and len(train_seasons) < 5:
            raise RuntimeError(
                "Strict verification requires out-of-fold Cup calibration data; "
                "got samples=0, positives=0"
            )

    def predict(self, test_data: list[TeamSeason]) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                team=t.team,
                playoff_probability=(0.60 if t.made_playoffs else 0.40),
                cup_win_probability=(0.08 if t.team == "T00" else 0.02),
            )
            for t in test_data
        ]


class _RandomizedDummyModel:
    def __init__(self, **kwargs):
        self.strict = bool(kwargs.get("strict_verification", False))
        self.require_oof = bool(
            kwargs.get("require_oof_cup_calibration_in_strict_mode", False)
        )

    def fit(self, train_data: list[TeamSeason]) -> None:
        train_seasons = {t.season for t in train_data}
        if self.strict and self.require_oof and len(train_seasons) < 5:
            raise RuntimeError(
                "Strict verification requires out-of-fold Cup calibration data; "
                "got samples=0, positives=0"
            )

    def predict(self, test_data: list[TeamSeason]) -> list[SimpleNamespace]:
        cup_probs = vegas_edge.np.random.random(len(test_data))
        cup_probs = cup_probs / max(float(cup_probs.sum()), 1e-9)
        return [
            SimpleNamespace(
                team=t.team,
                playoff_probability=(0.60 if t.made_playoffs else 0.40),
                cup_win_probability=float(cup_prob),
            )
            for t, cup_prob in zip(test_data, cup_probs)
        ]


def test_strict_vegas_rows_skip_underpowered_windows(monkeypatch) -> None:
    historical_data, teams = _historical_fixture()

    monkeypatch.setattr(
        vegas_edge,
        "load_vegas_odds",
        lambda season: _vegas_fixture(teams, season),
    )
    monkeypatch.setattr(vegas_edge, "EnsemblePredictor", _StrictAwareDummyModel)

    rows = vegas_edge.build_model_vs_vegas_rows(
        historical_data=historical_data,
        model_overrides={
            "strict_verification": True,
            "require_oof_cup_calibration_in_strict_mode": True,
        },
        start_season=2010,
        end_season=2015,
    )

    assert rows
    compared_seasons = sorted({row.season for row in rows})
    # 2014 is skipped due to strict OOF coverage insufficiency; 2015 is eligible.
    assert compared_seasons == [2015]


def test_vegas_edge_eval_is_seed_deterministic(monkeypatch) -> None:
    historical_data, teams = _historical_fixture()
    overrides = {
        "strict_verification": True,
        "require_oof_cup_calibration_in_strict_mode": True,
    }

    monkeypatch.setattr(
        vegas_edge,
        "load_vegas_odds",
        lambda season: _vegas_fixture(teams, season),
    )
    monkeypatch.setattr(vegas_edge, "EnsemblePredictor", _RandomizedDummyModel)

    d1 = vegas_edge.evaluate_model_vs_vegas_edge(
        historical_data=historical_data,
        model_overrides=overrides,
        start_season=2010,
        end_season=2015,
        n_bootstrap=100,
        random_seed=1234,
    )
    d2 = vegas_edge.evaluate_model_vs_vegas_edge(
        historical_data=historical_data,
        model_overrides=overrides,
        start_season=2010,
        end_season=2015,
        n_bootstrap=100,
        random_seed=1234,
    )
    d3 = vegas_edge.evaluate_model_vs_vegas_edge(
        historical_data=historical_data,
        model_overrides=overrides,
        start_season=2010,
        end_season=2015,
        n_bootstrap=100,
        random_seed=4321,
    )

    edge1 = d1.get("cup", {}).get("relative_brier_edge")
    edge2 = d2.get("cup", {}).get("relative_brier_edge")
    edge3 = d3.get("cup", {}).get("relative_brier_edge")
    assert edge1 == edge2
    assert edge1 != edge3
