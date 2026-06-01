"""Configuration for the AI-DSS modeling checkpoint."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = ROOT / "data" / "processed" / "decision_engine_output.csv"
INPUT_PARQUET = ROOT / "data" / "processed" / "decision_engine_output.parquet"
SUMMARY_DIR = ROOT / "data" / "processed" / "summaries"
METRICS_CSV = SUMMARY_DIR / "ai_model_metrics.csv"
IMPORTANCE_CSV = SUMMARY_DIR / "ai_feature_importance.csv"
PREDICTION_SAMPLE_CSV = SUMMARY_DIR / "ai_prediction_sample.csv"
MANIFEST_MD = ROOT / "docs" / "ai_modeling_manifest.md"

RANDOM_STATE = 42
MAX_MODEL_ROWS = 200_000
MAX_SHAP_ROWS = 1_000
PREDICTION_SAMPLE_ROWS = 200
TEST_DATE_SHARE = 0.2

USE_COLUMNS = [
    "collection_time_utc",
    "collection_date",
    "route_id",
    "route_short_name",
    "route_type",
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

CATEGORICAL_FEATURES = ["route_id", "route_short_name", "route_type", "direction_id"]
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
