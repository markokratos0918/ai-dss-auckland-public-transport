from __future__ import annotations

import pandas as pd


def delayed_routes_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    table = df.copy()
    if "route_display_name" in table.columns:
        table["Route Name"] = table["route_display_name"].fillna(table["route_id"])
    elif "route_long_name" in table.columns:
        table["Route Name"] = table["route_long_name"].fillna(table["route_short_name"]).fillna(table["route_id"])
    table = table.rename(
        columns={
            "route_id": "Route ID",
            "service_type": "Service Type",
            "route_corridor_name": "Route / Corridor",
            "recommended_action": "Recommended Action",
            "avg_predicted_delay_min": "Average Delay",
            "avg_delay_minutes": "Average Delay",
            "max_delay_minutes": "Maximum Delay",
            "avg_ai_probability": "Avg Prediction Probability",
            "avg_prediction_probability": "Avg Prediction Probability",
            "records": "Records",
        }
    )
    columns = [
        "Service Type",
        "Route Name",
        "Route / Corridor",
        "Route ID",
        "Recommended Action",
        "Average Delay",
        "Maximum Delay",
        "Avg Prediction Probability",
        "Records",
    ]
    table = table[[column for column in columns if column in table.columns]]
    if "Recommended Action" in table.columns:
        table["Recommended Action"] = table["Recommended Action"].replace(
            {"No operational action required": "No action required"}
        )
    for column in ("Average Delay", "Maximum Delay", "Avg Prediction Probability"):
        if column in table.columns:
            table[column] = table[column].round(2)
    return table
