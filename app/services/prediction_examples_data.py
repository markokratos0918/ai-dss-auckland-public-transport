from __future__ import annotations

import pandas as pd

from services.operator_data import from_primary


def ai_prediction_examples(limit: int, service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = f"""
        SELECT
            CAST(collection_date AS VARCHAR) AS collection_date,
            route_id,
            COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id) AS corridor_name,
            ROUND(TRY_CAST(delay_minutes AS DOUBLE), 3) AS observed_delay,
            ROUND(TRY_CAST(predicted_delay_minutes AS DOUBLE), 3) AS predicted_delay,
            ROUND(TRY_CAST(predicted_actionable_probability AS DOUBLE), 3) AS ai_probability,
            COALESCE(NULLIF(ai_delay_risk, ''), 'Unknown') AS ai_delay_risk,
            COALESCE(NULLIF(ai_recommended_action, ''), 'Unavailable') AS ai_recommended_action
        FROM {{source}}
        {{where}}
        ORDER BY ai_probability DESC NULLS LAST
        LIMIT {int(limit)}
    """
    return from_primary(query, service_type, include_special, day, hour)


def balanced_prediction_examples(service_type: str, include_special: bool, day: str, hour: str) -> pd.DataFrame:
    query = """
        WITH base AS (
            SELECT
                CAST(collection_date AS VARCHAR) AS collection_date,
                route_id,
                REGEXP_REPLACE(COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id), '^[A-Z0-9]+ - ', '') AS corridor_name,
                ROUND(TRY_CAST(delay_minutes AS DOUBLE), 3) AS observed_delay,
                ROUND(TRY_CAST(predicted_delay_minutes AS DOUBLE), 3) AS predicted_delay,
                ROUND(TRY_CAST(predicted_actionable_probability AS DOUBLE), 3) AS ai_probability,
                COALESCE(NULLIF(ai_delay_risk, ''), 'Unknown') AS ai_delay_risk,
                COALESCE(NULLIF(ai_recommended_action, ''), 'Unavailable') AS ai_recommended_action,
                CASE
                    WHEN TRY_CAST(delay_minutes AS DOUBLE) < -1 THEN 'Early-running'
                    WHEN TRY_CAST(delay_minutes AS DOUBLE) > 1 THEN 'Late-running'
                    ELSE 'Near on-time'
                END AS timing_band
            FROM {source}
            {where}
        ),
        ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY ai_delay_risk, timing_band
                    ORDER BY ai_probability DESC NULLS LAST, route_id
                ) AS row_rank
            FROM base
            WHERE ai_delay_risk IN ('Low', 'Medium', 'High', 'Severe')
        )
        SELECT *
        FROM ranked
        WHERE row_rank = 1
        ORDER BY
            CASE ai_delay_risk WHEN 'Low' THEN 1 WHEN 'Medium' THEN 2 WHEN 'High' THEN 3 WHEN 'Severe' THEN 4 ELSE 5 END,
            CASE timing_band WHEN 'Early-running' THEN 1 WHEN 'Near on-time' THEN 2 ELSE 3 END
    """
    df = from_primary(query, service_type, include_special, day, hour)
    return df.drop(columns=["row_rank"], errors="ignore").head(12)


def route_prediction_examples(
    route_id: str,
    limit: int,
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
) -> pd.DataFrame:
    from services.operator_constants import ALL_DAYS
    date_filter = "AND collection_date = (SELECT MAX(collection_date) FROM base)" if day == ALL_DAYS else ""
    safe_route = route_id.replace("'", "''")
    query = f"""
        WITH base AS (
            SELECT *
            FROM {{source}}
            {{where}}
        )
        SELECT
            CAST(collection_date AS VARCHAR) AS collection_date,
            route_id,
            COALESCE(NULLIF(service_type, ''), 'School/Special or unmatched services') AS service_type,
            REGEXP_REPLACE(COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id), '^[A-Z0-9]+ - ', '') AS corridor_name,
            ROUND(TRY_CAST(delay_minutes AS DOUBLE), 3) AS observed_delay,
            ROUND(TRY_CAST(predicted_delay_minutes AS DOUBLE), 3) AS predicted_delay,
            ROUND(TRY_CAST(predicted_actionable_probability AS DOUBLE), 3) AS ai_probability,
            COALESCE(NULLIF(ai_delay_risk, ''), 'Unknown') AS ai_delay_risk,
            COALESCE(NULLIF(ai_recommended_action, ''), 'Unavailable') AS ai_recommended_action
        FROM base
        WHERE route_id = '{safe_route}'
        {date_filter}
        ORDER BY ai_probability DESC NULLS LAST
        LIMIT {int(limit)}
    """
    return from_primary(query, service_type, include_special, day, hour)
