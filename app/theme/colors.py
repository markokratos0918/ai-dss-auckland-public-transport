"""Centralized color definitions for the AI DSS dashboard."""

RISK = {
    "low": "#2e7d32",
    "medium": "#f9a825",
    "high": "#ef6c00",
    "severe": "#c62828",
}

FEATURE = {
    "route": "#38bdf8",
    "service": "#2dd4bf",
    "time": "#facc15",
    "direction": "#a78bfa",
    "weather": "#60a5fa",
    "other": "#94a3b8",
}

SUMO = {
    "baseline": "#38bdf8",
    "disruption": "#ef4444",
    "intervention": "#22c55e",
}

ACTION = {
    "monitor": "#26c6da",
    "no_action": "#48c774",
    "adjust_headway": "#ff9800",
    "deploy_standby": "#ff4b4b",
    "default": "#4db7e9",
}

METRIC = {
    "records": "#38bdf8",
    "probability": "#a855f7",
    "predicted_delay": "#facc15",
    "predicted_actionable": "#fb923c",
    "observed_actionable": "#1687f8",
    "baseline_recall": "#94a3b8",
    "baseline_accuracy": "#94a3b8",
    "xgboost_recall": "#38bdf8",
    "xgboost_precision": "#22c55e",
    "xgboost_f1": "#a855f7",
    "xgboost_rmse": "#facc15",
    "arima_rmse": "#fb923c",
    "rmse_improvement": "#22c55e",
}

SIGNAL = {
    "observed": "#1687f8",
    "predicted": "#a855f7",
}

WEATHER = {
    "no_rain": "#22c55e",
    "light_rain": "#38bdf8",
    "moderate_rain": "#f59e0b",
    "heavy_rain": "#ef4444",
}

CHART_DEFAULT = "#38bdf8"
CHART_ACCENT = "#4db7e9"

# Legacy aliases for backward compatibility
RISK_COLORS = {
    "Low": RISK["low"],
    "Medium": RISK["medium"],
    "High": RISK["high"],
    "Severe": RISK["severe"],
}

FEATURE_COLORS = {
    "Route": FEATURE["route"],
    "Service": FEATURE["service"],
    "Time": FEATURE["time"],
    "Direction": FEATURE["direction"],
    "Weather": FEATURE["weather"],
    "Other": FEATURE["other"],
}

SUMO_COLORS = {
    "Baseline Operations": SUMO["baseline"],
    "Disruption Scenario": SUMO["disruption"],
    "Intervention Scenario": SUMO["intervention"],
}

ACTION_COLORS = {
    "Monitor route conditions": ACTION["monitor"],
    "No action required": ACTION["no_action"],
    "Adjust service headway": ACTION["adjust_headway"],
    "Deploy standby bus / supervisor review": ACTION["deploy_standby"],
}

CARD_COLORS = {
    "Records": METRIC["records"],
    "Avg Probability": METRIC["probability"],
    "Avg Predicted Delay": METRIC["predicted_delay"],
    "Predicted Actionable": METRIC["predicted_actionable"],
    "Observed Actionable": METRIC["observed_actionable"],
    "Low": RISK["low"],
    "Medium": RISK["medium"],
    "High": RISK["high"],
    "Severe": RISK["severe"],
    "Baseline Recall": METRIC["baseline_recall"],
    "Baseline Accuracy": METRIC["baseline_accuracy"],
    "XGBoost Recall": METRIC["xgboost_recall"],
    "XGBoost Precision": METRIC["xgboost_precision"],
    "XGBoost F1": METRIC["xgboost_f1"],
    "XGBoost RMSE": METRIC["xgboost_rmse"],
    "ARIMA Hourly RMSE": METRIC["arima_rmse"],
    "RMSE Improvement": METRIC["rmse_improvement"],
}
