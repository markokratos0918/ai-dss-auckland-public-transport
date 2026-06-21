from __future__ import annotations

import pandas as pd

from services.operator_data import from_primary, load_dataset, numeric


def weather_context(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = """
        SELECT
            CASE WHEN COALESCE(TRY_CAST(rain AS DOUBLE), 0) > 0 THEN 'Rain detected' ELSE 'No rain detected' END AS weather_condition,
            COUNT(*) AS records,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_ai_probability_pct,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS avg_observed_delay,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 3) AS avg_predicted_delay,
            ROUND(AVG(TRY_CAST(wind_speed_10m AS DOUBLE)), 2) AS avg_wind_speed,
            ROUND(AVG(TRY_CAST(precipitation AS DOUBLE)), 2) AS avg_precipitation
        FROM {source}
        {where}
        GROUP BY weather_condition
        ORDER BY records DESC
    """
    return from_primary(query, service_type, include_special, day, hour)


def model_metrics() -> pd.DataFrame:
    return numeric(load_dataset("model_metrics"), ["value"])


def model_evidence_summary() -> dict[str, str]:
    metrics = model_metrics()
    if metrics.empty:
        return {
            "Baseline Recall": "Unavailable",
            "XGBoost Recall": "Unavailable",
            "XGBoost F1": "Unavailable",
            "RMSE Improvement": "Unavailable",
        }

    def value(model: str, metric: str) -> float | None:
        rows = metrics[(metrics["model"] == model) & (metrics["metric"] == metric)]
        if rows.empty or pd.isna(rows.iloc[0]["value"]):
            return None
        return float(rows.iloc[0]["value"])

    baseline_recall = value("Most frequent baseline", "recall")
    xgb_recall = value("XGBoost classifier", "recall")
    xgb_f1 = value("XGBoost classifier", "f1")
    baseline_rmse = value("Median baseline", "rmse")
    xgb_rmse = value("XGBoost regressor", "rmse")
    improvement = None
    if baseline_rmse and xgb_rmse is not None:
        improvement = (baseline_rmse - xgb_rmse) / baseline_rmse * 100
    return {
        "Baseline Recall": "Unavailable" if baseline_recall is None else f"{baseline_recall:.1%}",
        "XGBoost Recall": "Unavailable" if xgb_recall is None else f"{xgb_recall:.1%}",
        "XGBoost F1": "Unavailable" if xgb_f1 is None else f"{xgb_f1:.1%}",
        "RMSE Improvement": "Unavailable" if improvement is None else f"{improvement:.1f}%",
    }


def intervention_logic() -> pd.DataFrame:
    return load_dataset("intervention_logic")
