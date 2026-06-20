from __future__ import annotations

import pandas as pd
import streamlit as st


def format_records(value: object) -> str:
    if pd.isna(value):
        return "0"
    return f"{int(value):,}"


def display_table(df: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    if df.empty:
        return df
    table = df.rename(columns=columns).copy()
    for column in table.columns:
        if "records" in column.lower():
            table[column] = table[column].map(format_records)
        elif table[column].dtype.kind in "fc":
            table[column] = table[column].round(2)
    return table


def route_examples_section(route_examples: pd.DataFrame) -> None:
    st.markdown("#### Weather-Context Route Examples")
    st.caption(
        "Routes listed here had observed delay during rain or high-wind records. "
        "This is a signal for review, not proof of weather causation."
    )
    if route_examples.empty:
        st.warning("Weather-context route examples are unavailable for the current filter.")
        return
    st.dataframe(
        display_table(
            route_examples,
            {
                "route_id": "Route ID",
                "service_type": "Service Type",
                "corridor_name": "Corridor Name",
                "weather_context_records": "Weather Context Records",
                "avg_observed_delay": "Avg Observed Delay",
                "avg_predicted_delay": "Avg Predicted Delay",
                "avg_ai_probability_pct": "Avg AI Risk Probability",
                "max_rain": "Max Rain",
                "max_wind_speed": "Max Wind Speed",
                "common_ai_action": "Common AI Action",
            },
        ),
        use_container_width=True,
        hide_index=True,
    )
