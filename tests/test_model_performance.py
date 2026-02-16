"""Performance regression checks for strict walk-forward backtest outputs."""

from superhuman.data_loader import load_training_data
from superhuman.validation import generate_backtest_report, generate_checkpoint_backtest_report
from superhuman.validation import _predict_playoff_field_nhl
from superhuman.data_models import PredictionResult
from superhuman.config import get_team_conference
from superhuman.model_profile import load_active_model_profile


def _load_or_generate_report() -> dict:
    profile = load_active_model_profile()
    overrides = {
        "use_neural_network": bool(profile.get("use_neural_network", True)),
        "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
        "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
        "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
        "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
        "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
        "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
    }
    return generate_backtest_report(
        load_training_data(allow_synthetic_fallback=False),
        cache_path=None,
        force_refresh=True,
        model_overrides=overrides,
    )


class TestModelPerformance:
    def test_backtest_schema_and_mode(self):
        report = _load_or_generate_report()
        assert report.get("evaluationMode") == "strict_walk_forward"
        assert report.get("walkForwardAudit", {}).get("leakageFree") is True

        summary = report.get("summary", {})
        required = {
            "topPickAccuracy",
            "top5Accuracy",
            "averageWinnerRank",
            "averagePlayoffF1",
            "totalSeasons",
        }
        assert required.issubset(summary.keys())

    def test_backtest_regression_thresholds(self):
        report = _load_or_generate_report()
        summary = report.get("summary", {})

        # Guardrails against silent degradation.
        assert summary.get("topPickAccuracy", 0) >= 10.0
        assert summary.get("top5Accuracy", 0) >= 40.0
        assert summary.get("averageWinnerRank", 999) <= 8.0
        assert summary.get("averagePlayoffF1", 0) >= 0.88

    def test_checkpoint_backtest_schema(self):
        data = load_training_data()
        checkpoint = generate_checkpoint_backtest_report(data, checkpoints=[0, 20, 40, 60])
        assert checkpoint.get("mode") == "checkpoint_backtest"

        rows = checkpoint.get("checkpoints", [])
        assert len(rows) == 4
        expected = {0, 20, 40, 60}
        seen = {r.get("checkpointGames") for r in rows}
        assert seen == expected

        for row in rows:
            assert "averagePlayoffF1" in row
            assert 0 <= row["averagePlayoffF1"] <= 1

    def test_predicted_playoff_field_uses_nhl_structure(self, dashboard_data):
        predictions = [
            PredictionResult(
                team=t["code"],
                season=dashboard_data["meta"]["season"],
                playoff_probability=float(t["playoffProbability"]) / 100.0,
            )
            for t in dashboard_data["teams"]
        ]
        predicted = _predict_playoff_field_nhl(predictions)
        assert len(predicted) == 16
        east = sum(1 for code in predicted if get_team_conference(code) == "East")
        west = sum(1 for code in predicted if get_team_conference(code) == "West")
        assert east == 8
        assert west == 8

    def test_active_profile_cup_ranking_meets_contract_floor(self, tmp_path):
        profile = load_active_model_profile()
        overrides = {
            "use_neural_network": bool(profile.get("use_neural_network", True)),
            "use_recency_weighting": bool(profile.get("use_recency_weighting", True)),
            "use_cup_calibration": bool(profile.get("use_cup_calibration", True)),
            "recency_decay_rate": float(profile.get("recency_decay_rate", 0.15)),
            "cup_winner_boost": float(profile.get("cup_winner_boost", 2.0)),
            "cup_market_prior_blend": float(profile.get("cup_market_prior_blend", 0.0)),
            "cup_ensemble_weights": profile.get("cup_ensemble_weights"),
        }
        report = generate_backtest_report(
            load_training_data(allow_synthetic_fallback=False),
            cache_path=str(tmp_path / "backtest_profile_cache.json"),
            force_refresh=True,
            model_overrides=overrides,
        )
        summary = report.get("summary", {})
        assert summary.get("topPickAccuracy", 0.0) >= 12.0
        assert summary.get("top5Accuracy", 0.0) >= 45.0
