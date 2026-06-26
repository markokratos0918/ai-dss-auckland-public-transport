from __future__ import annotations

import pandas as pd

from services.operator_data import from_primary, top_non_special_routes


def route_options(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    return top_non_special_routes(100, service_type, include_special, day, hour)


def route_focus(route_id: str, service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = f"""
        WITH base AS (
            SELECT *
            FROM {{source}}
            {{where}}
        )
        SELECT
            route_id,
            REGEXP_REPLACE(COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id), '^[A-Z0-9]+ - ', '') AS corridor_name,
            COALESCE(mode(NULLIF(service_type, '')), 'School/Special or unmatched services') AS service_type,
            COUNT(*) AS records,
            ROUND(AVG(TRY_CAST(delay_minutes AS DOUBLE)), 3) AS avg_observed_delay,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 3) AS avg_predicted_delay,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_ai_probability_pct,
            SUM(CASE WHEN ai_delay_risk IN ('High', 'Severe') THEN 1 ELSE 0 END) AS ai_high_severe_cases,
            COALESCE(mode(ai_recommended_action), 'Unavailable') AS recommended_action,
            ROUND(AVG(CASE WHEN COALESCE(TRY_CAST(rain AS DOUBLE), 0) > 0 THEN 100 ELSE 0 END), 1) AS avg_rain_pct,
            ROUND(MAX(TRY_CAST(wind_speed_10m AS DOUBLE)), 1) AS max_wind_speed,
            ROUND(AVG(TRY_CAST(precipitation AS DOUBLE)), 2) AS avg_precipitation
        FROM base
        WHERE route_id = '{route_id.replace("'", "''")}'
        GROUP BY ALL
    """
    return from_primary(query, service_type, include_special, day, hour)
