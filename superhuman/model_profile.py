"""
Model profile loading for production predictor settings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE_PATH = PROJECT_ROOT / "data" / "model_profile.json"


DEFAULT_PROFILE: Dict[str, Any] = {
    "profileVersion": "default-2026-02-07",
    "use_neural_network": True,
    "use_recency_weighting": True,
    "use_cup_calibration": True,
    "recency_decay_rate": 0.15,
    "cup_winner_boost": 2.0,
    "cup_market_prior_blend": 0.0,
    "cup_ensemble_weights": {
        "gradient_boosting": 0.30,
        "neural_network": 0.30,
        "monte_carlo": 0.40,
    },
}


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = float(sum(max(0.0, float(v)) for v in weights.values()))
    if total <= 0:
        return DEFAULT_PROFILE["cup_ensemble_weights"].copy()
    return {k: max(0.0, float(v)) / total for k, v in weights.items()}


def load_active_model_profile(path: Path = DEFAULT_PROFILE_PATH) -> Dict[str, Any]:
    profile = DEFAULT_PROFILE.copy()
    profile["cup_ensemble_weights"] = DEFAULT_PROFILE["cup_ensemble_weights"].copy()

    if not path.exists():
        return profile

    try:
        with open(path) as f:
            payload = json.load(f)
    except Exception:
        return profile

    for key in (
        "profileVersion",
        "use_neural_network",
        "use_recency_weighting",
        "use_cup_calibration",
        "recency_decay_rate",
        "cup_winner_boost",
    ):
        if key in payload:
            profile[key] = payload[key]

    if "cup_market_prior_blend" in payload:
        try:
            blend = float(payload["cup_market_prior_blend"])
        except (TypeError, ValueError):
            blend = float(DEFAULT_PROFILE["cup_market_prior_blend"])
        profile["cup_market_prior_blend"] = max(0.0, min(1.0, blend))

    if "cup_ensemble_weights" in payload and isinstance(payload["cup_ensemble_weights"], dict):
        profile["cup_ensemble_weights"] = _normalize_weights(payload["cup_ensemble_weights"])

    return profile
