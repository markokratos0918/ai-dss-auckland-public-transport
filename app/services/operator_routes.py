from __future__ import annotations

import pandas as pd

from services.operator_constants import ALL_DAYS, ALL_HOURS, SPECIAL_SERVICE_LABEL
from services.operator_io import from_primary


def top_non_special_routes(
    limit: int = 10,
    service_type: str = "All",
    include_special: bool = False,
    analysis_day: str = ALL_DAYS,
    analysis_hour: str = ALL_HOURS,
) -> pd.DataFrame:
    query = f"""
        SELECT
            CASE
                WHEN COALESCE(CAST(is_special_route AS BOOLEAN), starts_with(upper(route_id), 'S')) THEN '{SPECIAL_SERVICE_LABEL}'
                ELSE COALESCE(NULLIF(service_type, ''), '{SPECIAL_SERVICE_LABEL}')
            END AS service_type,
            COALESCE(NULLIF(route_display_name, ''), route_short_name, route_id) AS route_display_name,
            COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id) AS route_corridor_name,
            route_id,
            COALESCE(CAST(is_special_route AS BOOLEAN), starts_with(upper(route_id), 'S')) AS is_special_route,
            COUNT(*) AS records,
            SUM(COALESCE(TRY_CAST(predicted_actionable_delay_risk AS INTEGER), 0)) AS actionable_records,
            COALESCE(mode(ai_recommended_action), 'Unavailable') AS recommended_action,
            ROUND(AVG(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 3) AS avg_delay_minutes,
            ROUND(MAX(TRY_CAST(predicted_delay_minutes AS DOUBLE)), 3) AS max_delay_minutes,
            ROUND(AVG(TRY_CAST(predicted_actionable_probability AS DOUBLE)), 3) AS avg_prediction_probability
        FROM {{source}}
        {{where}}
        GROUP BY ALL
        ORDER BY actionable_records DESC, avg_delay_minutes DESC
        LIMIT {int(limit)}
    """
    return from_primary(query, service_type, include_special, analysis_day, analysis_hour)
