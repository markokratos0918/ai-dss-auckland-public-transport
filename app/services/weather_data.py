from __future__ import annotations

import pandas as pd

from services.operator_data import SUMMARY_DIR, from_primary, load_csv


WEATHER_FEATURES = [
    "temperature_2m",
    "rain",
    "precipitation",
    "relative_humidity_2m",
    "wind_speed_10m",
]

def weather_integration_summary(service_type: str, include_special: bool, day: str, hour: str) -> dict[str, str]:
    fields_sql = " AND ".join(f"{field} IS NOT NULL" for field in WEATHER_FEATURES)
    query = f"""
        SELECT
            COUNT(*) AS records,
            COUNT(DISTINCT collection_date) AS days,
            MIN(CAST(collection_date AS VARCHAR)) AS start_date,
            MAX(CAST(collection_date AS VARCHAR)) AS end_date,
            ROUND(100.0 * SUM(CASE WHEN {fields_sql} THEN 1 ELSE 0 END) / COUNT(*), 2) AS match_pct
        FROM {{source}}
        {{where}}
    """
    df = from_primary(query, service_type, include_special, day, hour)
    if df.empty:
        return {
            "Weather Source": "Open-Meteo hourly weather",
            "Match Rate": "Unavailable",
            "Weather Fields": "temperature, rain, precipitation, humidity, wind speed",
            "Records": "Unavailable",
            "Days": "Unavailable",
            "Period": "Unavailable",
        }
    row = df.iloc[0]
    records = int(row["records"]) if pd.notna(row["records"]) else 0
    days = int(row["days"]) if pd.notna(row["days"]) else 0
    start = row.get("start_date", "")
    end = row.get("end_date", "")
    return {
        "Weather Source": "Open-Meteo hourly weather",
        "Match Rate": f"{row['match_pct']:.1f}%" if pd.notna(row["match_pct"]) else "Unavailable",
        "Weather Fields": "temperature, rain, precipitation, humidity, wind speed",
        "Records": f"{records:,}",
        "Days": f"{days}",
        "Period": f"{start} to {end}",
    }


def rain_severity_breakdown(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = """
        SELECT
            CASE
                WHEN COALESCE(TRY_CAST(rain AS DOUBLE), 0) = 0 THEN 'No rain'
                WHEN TRY_CAST(rain AS DOUBLE) <= 0.5 THEN 'Light rain'
                WHEN TRY_CAST(rain AS DOUBLE) <= 2.0 THEN 'Moderate rain'
                ELSE 'Heavier rain'
            END AS rain_band,
            COUNT(*) AS records,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS record_pct,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS avg_observed_delay,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_ai_probability_pct
        FROM {source}
        {where}
        GROUP BY rain_band
        ORDER BY CASE rain_band
            WHEN 'No rain' THEN 1
            WHEN 'Light rain' THEN 2
            WHEN 'Moderate rain' THEN 3
            ELSE 4
        END
    """
    return from_primary(query, service_type, include_special, day, hour)


def daily_weather_events(service_type: str, include_special: bool, day: str, hour: str, limit: int = 10) -> pd.DataFrame:
    query = f"""
        SELECT
            CAST(collection_date AS VARCHAR) AS collection_date,
            COUNT(*) AS records,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 2) AS avg_observed_delay,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 2) AS avg_predicted_delay,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_ai_probability_pct,
            ROUND(MAX(TRY_CAST(rain AS DOUBLE)), 2) AS max_rain,
            ROUND(MAX(TRY_CAST(precipitation AS DOUBLE)), 2) AS max_precipitation,
            ROUND(MAX(TRY_CAST(wind_speed_10m AS DOUBLE)), 2) AS max_wind_speed,
            ROUND(AVG(TRY_CAST(wind_speed_10m AS DOUBLE)), 2) AS avg_wind_speed
        FROM {{source}}
        {{where}}
        GROUP BY collection_date
        ORDER BY max_precipitation DESC, max_wind_speed DESC
        LIMIT {int(limit)}
    """
    return from_primary(query, service_type, include_special, day, hour)


def service_type_weather_view(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = """
        SELECT
            COALESCE(NULLIF(service_type, ''), 'School/Special or unmatched services') AS service_type,
            CASE WHEN COALESCE(TRY_CAST(rain AS DOUBLE), 0) > 0 THEN 'Rain detected' ELSE 'No rain detected' END AS weather_condition,
            COUNT(*) AS records,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS avg_observed_delay,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_ai_probability_pct,
            ROUND(AVG(TRY_CAST(wind_speed_10m AS DOUBLE)), 2) AS avg_wind_speed
        FROM {source}
        {where}
        GROUP BY service_type, weather_condition
        ORDER BY service_type, weather_condition
    """
    return from_primary(query, service_type, include_special, day, hour)


def weather_route_examples(
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
    limit: int = 10,
) -> pd.DataFrame:
    query = f"""
        WITH base AS (
            SELECT *,
                CASE WHEN COALESCE(TRY_CAST(rain AS DOUBLE), 0) > 0
                          OR COALESCE(TRY_CAST(wind_speed_10m AS DOUBLE), 0) >= 30
                     THEN 1 ELSE 0 END AS is_weather_exposed
            FROM {{source}}
            {{where}}
        )
        SELECT
            route_id,
            COALESCE(NULLIF(service_type, ''), 'School/Special or unmatched services') AS service_type,
            REGEXP_REPLACE(COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id), '^[A-Z0-9]+ - ', '') AS corridor_name,
            COUNT(*) FILTER (WHERE is_weather_exposed = 1) AS weather_context_records,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)) FILTER (WHERE is_weather_exposed = 1), 2) AS avg_observed_delay,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)) FILTER (WHERE is_weather_exposed = 0), 2) AS avg_dry_delay,
            ROUND(
                AVG(TRY_CAST(delay_minutes AS DOUBLE)) FILTER (WHERE is_weather_exposed = 1)
                - AVG(TRY_CAST(delay_minutes AS DOUBLE)) FILTER (WHERE is_weather_exposed = 0), 2
            ) AS weather_delay_delta,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)) FILTER (WHERE is_weather_exposed = 1), 2) AS avg_predicted_delay,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) FILTER (WHERE is_weather_exposed = 1) * 100, 2) AS avg_ai_probability_pct,
            ROUND(MAX(TRY_CAST(rain AS DOUBLE)) FILTER (WHERE is_weather_exposed = 1), 2) AS max_rain,
            ROUND(MAX(TRY_CAST(wind_speed_10m AS DOUBLE)) FILTER (WHERE is_weather_exposed = 1), 2) AS max_wind_speed,
            COALESCE(mode(ai_recommended_action) FILTER (WHERE is_weather_exposed = 1), 'Unavailable') AS common_ai_action
        FROM base
        GROUP BY ALL
        HAVING COUNT(*) FILTER (WHERE is_weather_exposed = 1) >= 50
        ORDER BY weather_delay_delta DESC, weather_context_records DESC
        LIMIT {int(limit)}
    """
    return from_primary(query, service_type, include_special, day, hour)


def weather_context_summary() -> pd.DataFrame:
    df = load_csv(str(SUMMARY_DIR / "weather_delay_risk_summary.csv"))
    if df.empty:
        return df
    df = df.copy()
    df["records"] = pd.to_numeric(df["records"], errors="coerce").fillna(0)
    df["avg_delay_minutes"] = pd.to_numeric(df["avg_delay_minutes"], errors="coerce")
    df["weighted_delay"] = df["records"] * df["avg_delay_minutes"]
    grouped = (
        df.groupby(["weather_context", "weather_rule"], as_index=False)
        .agg(
            records=("records", "sum"),
            weighted_delay=("weighted_delay", "sum"),
            max_delay_minutes=("max_delay_minutes", "max"),
        )
    )
    grouped["record_pct"] = (grouped["records"] / grouped["records"].sum() * 100).round(2)
    grouped["avg_observed_delay"] = (grouped["weighted_delay"] / grouped["records"]).round(3)
    return grouped[["weather_context", "weather_rule", "records", "record_pct", "avg_observed_delay", "max_delay_minutes"]]


def weather_shap_features() -> pd.DataFrame:
    df = load_csv(str(SUMMARY_DIR / "ai_feature_explanation_lookup.csv"))
    if df.empty or "feature" not in df.columns:
        return pd.DataFrame()
    mask = df["feature"].astype(str).isin(WEATHER_FEATURES)
    weather = df[mask & (df["explainability_type"] == "mean_abs_shap")].copy()
    if weather.empty:
        return weather
    weather["importance"] = pd.to_numeric(weather["importance"], errors="coerce")
    weather = weather.sort_values("importance", ascending=False)
    return weather[["feature", "importance", "operator_explanation"]].head(8)
