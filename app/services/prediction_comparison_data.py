from __future__ import annotations

import pandas as pd

from services.operator_data import from_primary


def route_actionable_signal_scatter(
    service_type: str,
    include_special: bool,
    day: str,
    hour: str,
    limit: int = 45,
) -> pd.DataFrame:
    query = f"""
        WITH route_counts AS (
            SELECT
                route_id,
                COALESCE(NULLIF(route_corridor_name, ''), NULLIF(route_display_name, ''), route_id) AS corridor_name,
                SUM(COALESCE(TRY_CAST(actual_actionable_delay_risk AS INTEGER), 0)) AS observed_records,
                SUM(COALESCE(TRY_CAST(predicted_actionable_delay_risk AS INTEGER), 0)) AS ai_records
            FROM {{source}}
            {{where}}
            GROUP BY route_id, corridor_name
        )
        SELECT *
        FROM route_counts
        WHERE observed_records > 0 OR ai_records > 0
        ORDER BY GREATEST(observed_records, ai_records) DESC, route_id
        LIMIT {int(limit)}
    """
    wide = from_primary(query, service_type, include_special, day, hour)
    if wide.empty:
        return pd.DataFrame(columns=["route_id", "corridor_name", "Signal", "Records", "x_pos"])
    observed = wide[["route_id", "corridor_name", "observed_records"]].rename(columns={"observed_records": "Records"})
    observed["Signal"] = "Observed Evidence"
    observed["x_pos"] = 1
    ai = wide[["route_id", "corridor_name", "ai_records"]].rename(columns={"ai_records": "Records"})
    ai["Signal"] = "AI Predicted Risk"
    ai["x_pos"] = 2
    return pd.concat([observed, ai], ignore_index=True)
