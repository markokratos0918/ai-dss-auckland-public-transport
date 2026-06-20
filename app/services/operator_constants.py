from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SUMMARY_DIR = PROCESSED_DIR / "summaries"
PRIMARY_PARQUET = PROCESSED_DIR / "parquet" / "ai_decision_support_model_baseline.parquet"

DATA_SOURCES = {
    "ai_decision_summary": SUMMARY_DIR / "ai_decision_recommendation_summary.csv",
    "ai_route_actions": SUMMARY_DIR / "ai_decision_route_recommendation_counts.csv",
    "feature_importance": SUMMARY_DIR / "ai_feature_importance.csv",
    "model_metrics": SUMMARY_DIR / "ai_model_metrics.csv",
    "prediction_sample": SUMMARY_DIR / "ai_prediction_sample.csv",
    "sumo_scenarios": PROCESSED_DIR / "sumo_scenarios.csv",
    "sumo_validation": PROCESSED_DIR / "sumo_validation_results.csv",
    "intervention_logic": PROCESSED_DIR / "intervention_logic.csv",
}

SPECIAL_SERVICE_LABEL = "School/Special Services"
SERVICE_TYPES = ["All", "Bus", "Train / Rail", "Ferry", SPECIAL_SERVICE_LABEL]
RISK_ORDER = ["Low", "Medium", "High", "Severe"]
ALL_DAYS = "All days"
ALL_HOURS = "All hours"
