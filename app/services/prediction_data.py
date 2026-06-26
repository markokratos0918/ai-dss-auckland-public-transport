from __future__ import annotations

import pandas as pd

from services.operator_data import from_primary


def actionable_risk_comparison(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = """
        SELECT
            SUM(COALESCE(TRY_CAST(actual_actionable_delay_risk AS INTEGER), 0)) AS observed_actionable,
            SUM(COALESCE(TRY_CAST(predicted_actionable_delay_risk AS INTEGER), 0)) AS ai_predicted_actionable
        FROM {source}
        {where}
    """
    df = from_primary(query, service_type, include_special, day, hour)
    if df.empty:
        return pd.DataFrame(columns=["Signal", "Records"])
    row = df.iloc[0]
    return pd.DataFrame(
        {
            "Signal": ["Observed actionable records", "AI-predicted actionable records"],
            "Records": [
                0 if pd.isna(row.get("observed_actionable")) else int(row.get("observed_actionable")),
                0 if pd.isna(row.get("ai_predicted_actionable")) else int(row.get("ai_predicted_actionable")),
            ],
        }
    )


def reliability_timing_mix(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = """
        WITH labelled AS (
            SELECT
                CASE
                    WHEN TRY_CAST(delay_minutes AS DOUBLE) < -1 THEN 'Early-running'
                    WHEN TRY_CAST(delay_minutes AS DOUBLE) > 1 THEN 'Late-running'
                    ELSE 'Near on-time'
                END AS timing_band
            FROM {source}
            {where}
        ),
        grouped AS (
            SELECT timing_band, COUNT(*) AS records
            FROM labelled
            GROUP BY timing_band
        ),
        totals AS (SELECT SUM(records) AS total_records FROM grouped)
        SELECT timing_band, records, ROUND(records * 100.0 / NULLIF(total_records, 0), 2) AS share_pct
        FROM grouped, totals
    """
    df = from_primary(query, service_type, include_special, day, hour)
    order = ["Early-running", "Near on-time", "Late-running"]
    if df.empty:
        return pd.DataFrame({"timing_band": order, "records": [0, 0, 0], "share_pct": [0, 0, 0]})
    df["timing_band"] = pd.Categorical(df["timing_band"], order, ordered=True)
    return df.sort_values("timing_band")


def ai_prediction_summary(service_type: str, include_special: bool, day: str, hour: str) -> dict[str, str]:
    query = """
        SELECT
            COUNT(*) AS records,
            AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) AS avg_probability,
            AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)) AS avg_predicted_delay,
            SUM(COALESCE(TRY_CAST(predicted_actionable_delay_risk AS INTEGER), 0)) AS predicted_actionable,
            SUM(COALESCE(TRY_CAST(actual_actionable_delay_risk AS INTEGER), 0)) AS actual_actionable
        FROM {source}
        {where}
    """
    df = from_primary(query, service_type, include_special, day, hour)
    if df.empty:
        return {"Records": "Unavailable", "Avg Probability": "Unavailable", "Avg Predicted Delay": "Unavailable"}
    row = df.iloc[0]
    records = 0 if pd.isna(row.get("records")) else int(row.get("records"))
    avg_probability = row.get("avg_probability")
    avg_delay = row.get("avg_predicted_delay")
    predicted = 0 if pd.isna(row.get("predicted_actionable")) else int(row.get("predicted_actionable"))
    actual = 0 if pd.isna(row.get("actual_actionable")) else int(row.get("actual_actionable"))
    return {
        "Records": f"{records:,}",
        "Avg Probability": "Unavailable" if pd.isna(avg_probability) else f"{avg_probability * 100:.1f}%",
        "Avg Predicted Delay": "Unavailable" if pd.isna(avg_delay) else f"{avg_delay:.2f} min",
        "Predicted Actionable": f"{predicted:,}",
        "Observed Actionable": f"{actual:,}",
    }


def risk_category_cards(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = """
        WITH grouped AS (
            SELECT
                COALESCE(NULLIF(ai_delay_risk, ''), 'Unknown') AS ai_delay_risk,
                COALESCE(mode(ai_recommended_action), 'Unavailable') AS recommended_action,
                COUNT(*) AS records
            FROM {source}
            {where}
            GROUP BY ai_delay_risk
        ),
        totals AS (SELECT SUM(records) AS total_records FROM grouped)
        SELECT
            ai_delay_risk,
            recommended_action,
            records,
            ROUND(records * 100.0 / NULLIF(total_records, 0), 2) AS share_pct
        FROM grouped, totals
    """
    df = from_primary(query, service_type, include_special, day, hour)
    order = ["Low", "Medium", "High", "Severe"]
    if df.empty:
        return pd.DataFrame({"ai_delay_risk": order, "recommended_action": "Unavailable", "records": 0, "share_pct": 0})
    df["ai_delay_risk"] = pd.Categorical(df["ai_delay_risk"], order, ordered=True)
    return df.sort_values("ai_delay_risk")
