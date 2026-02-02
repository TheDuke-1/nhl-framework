"""
Superhuman NHL Prediction System
================================
A data-driven approach to NHL playoff and Stanley Cup prediction.

Modules:
    config - System configuration and constants
    data_models - Dataclasses for structured data
    data_loader - Load historical and current data
    feature_engineering - Create orthogonal features via PCA
    models - Ensemble prediction models
    validation - Cross-validation and calibration
    predictor - Main prediction interface
"""

from .config import (
    TRAINING_SEASONS,
    TEST_SEASONS,
    ALL_TEAMS,
    N_SIMULATIONS
)

from .data_models import (
    TeamSeason,
    FeatureVector,
    PredictionResult
)

from .data_loader import (
    load_current_season_data,
    load_training_data,
    validate_data
)

from .feature_engineering import (
    FeatureEngineer,
    create_feature_matrix,
    get_feature_correlations
)

from .models import (
    WeightOptimizer,
    PlayoffClassifier,
    CupPredictor,
    MonteCarloSimulator,
    EnsemblePredictor
)

from .validation import (
    ValidationFramework,
    ValidationResult,
    benchmark_against_baseline
)

from .predictor import SuperhumanPredictor

__version__ = "1.0.0"
__all__ = [
    "TeamSeason",
    "FeatureVector",
    "PredictionResult",
    "FeatureEngineer",
    "load_current_season_data",
    "load_training_data",
    "validate_data",
    "create_feature_matrix",
    "get_feature_correlations",
    "WeightOptimizer",
    "PlayoffClassifier",
    "CupPredictor",
    "MonteCarloSimulator",
    "EnsemblePredictor",
    "ValidationFramework",
    "ValidationResult",
    "benchmark_against_baseline",
    "SuperhumanPredictor",
]
