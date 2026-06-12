"""Configuration for the AI-DSS modeling checkpoint."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PARQUET_DIR = ROOT / "data" / "processed" / "parquet"
MODEL_BASELINE_DIR = ROOT / "data" / "processed" / "outputs" / "model_baseline"
INPUT_PARQUET = PARQUET_DIR / "decision_engine_model_baseline.parquet"
INPUT_CSV = MODEL_BASELINE_DIR / "decision_engine_output.csv"
SUMMARY_DIR = ROOT / "data" / "processed" / "summaries"
METRICS_CSV = SUMMARY_DIR / "ai_model_metrics.csv"
IMPORTANCE_CSV = SUMMARY_DIR / "ai_feature_importance.csv"
PREDICTION_SAMPLE_CSV = SUMMARY_DIR / "ai_prediction_sample.csv"
MANIFEST_MD = ROOT / "docs" / "ai_modeling_manifest.md"
AI_PREDICTIONS_MODEL_BASELINE_PARQUET = PARQUET_DIR / "ai_predictions_model_baseline.parquet"
AI_PREDICTIONS_TEST_SET_PARQUET = PARQUET_DIR / "ai_predictions_test_set.parquet"

RANDOM_STATE = 42
MAX_MODEL_ROWS = 200_000
MAX_SHAP_ROWS = 1_000
PREDICTION_SAMPLE_ROWS = 200
TEST_DATE_SHARE = 0.2

USE_COLUMNS = [
    "collection_time_utc",
    "collection_date",
    "collection_day_status",
    "collection_coverage_hours",
    "is_partial_day",
    "is_model_baseline_day",
    "route_id",
    "route_short_name",
    "route_type",
    "service_type",
    "route_display_name",
    "route_corridor_name",
    "is_special_route",
    "direction_id",
    "delay_minutes",
    "delay_risk",
    "recommended_action",
    "trip_hour",
    "weekday",
    "day_of_month",
    "temperature_2m",
    "precipitation",
    "rain",
    "relative_humidity_2m",
    "wind_speed_10m",
]

CATEGORICAL_FEATURES = [
    "route_id",
    "route_display_name",
    "route_corridor_name",
    "service_type",
    "route_type",
    "direction_id",
    "is_special_route",
]
NUMERIC_FEATURES = [
    "trip_hour",
    "weekday",
    "day_of_month",
    "temperature_2m",
    "precipitation",
    "rain",
    "relative_humidity_2m",
    "wind_speed_10m",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
PREDICTION_CONTEXT_COLUMNS = [
    "collection_time_utc",
    "collection_date",
    "route_id",
    "route_short_name",
    "route_display_name",
    "route_corridor_name",
    "service_type",
    "route_type",
    "direction_id",
    "is_special_route",
    "delay_minutes",
    "delay_risk",
    "recommended_action",
    "trip_hour",
    "weekday",
    "day_of_month",
    "temperature_2m",
    "precipitation",
    "rain",
    "relative_humidity_2m",
    "wind_speed_10m",
    "collection_day_status",
    "collection_coverage_hours",
    "is_partial_day",
    "is_model_baseline_day",
]
