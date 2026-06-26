from __future__ import annotations

import pandas as pd

from services.operator_data import from_primary, top_non_special_routes


RISK_FILTERS = ["All", "Low", "Medium", "High", "Severe"]


def format_route_label(route_id: str, corridor_name: str, max_length: int = 30) -> str:
    if corridor_name and corridor_name != route_id:
        return f"{route_id} \u2014 {corridor_name}"
    return route_id



def search_routes(routes_df: pd.DataFrame, search_text: str) -> pd.DataFrame:
    """Filter routes by search text matching route_id or corridor name."""
    if not search_text.strip():
        return routes_df
    search_lower = search_text.lower()
    return routes_df[
        routes_df["route_id"].str.lower().str.contains(search_lower, na=False)
        | routes_df["route_corridor_name"].str.lower().str.contains(search_lower, na=False)
    ]


def route_options_by_risk(
    risk: str,
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
) -> pd.DataFrame:
    risk = risk or "All"
    if risk == "All":
        return top_non_special_routes(100, service_type, include_special, day, hour)
    safe_risk = str(risk).replace("'", "''")
    query = f"""
        WITH base AS (
            SELECT * FROM {{source}} {{where}}
        )
        SELECT
            COALESCE(NULLIF(service_type, ''), 'School/Special or unmatched services') AS service_type,
            route_id,
            REGEXP_REPLACE(COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id), '^[A-Z0-9]+ - ', '') AS route_corridor_name,
            COUNT(*) AS records,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 2) AS avg_delay_minutes,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)) * 100, 2) AS avg_prediction_probability,
            COALESCE(mode(ai_recommended_action), 'Unavailable') AS recommended_action
        FROM base
        WHERE ai_delay_risk = '{safe_risk}'
        GROUP BY ALL
        ORDER BY records DESC, avg_prediction_probability DESC
        LIMIT 100
    """
    return from_primary(query, service_type, include_special, day, hour)


def table_without_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return df.drop(columns=[column for column in columns if column in df.columns])
