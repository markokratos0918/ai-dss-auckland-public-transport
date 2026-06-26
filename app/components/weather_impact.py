from __future__ import annotations

from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from components.operator_weather import display_table
from components.weather_impact_rain import render_rain_panel
from components.weather_impact_styles import (
    WEATHER_COLORS,
    inject_weather_css,
    section_title,
)


__all__ = [
    "inject_weather_css",
    "section_title",
    "render_rain_panel",
    "render_weather_kpis",
    "prepare_weather_context",
    "weather_condition_chart",
    "render_route_watchlist",
    "render_operator_note",
]


def render_weather_kpis(summary: dict[str, str]) -> None:
    items = [
        ("Weather Match Rate", summary["Match Rate"]),
        ("Dataset Period", summary["Period"]),
        ("Days", summary["Days"]),
        ("Records", summary["Records"]),
    ]
    cols = st.columns(4)

    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div class="weather-kpi-card">
                    <div class="weather-kpi-label">{escape(label)}</div>
                    <div class="weather-kpi-value">{escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def prepare_weather_context(context: pd.DataFrame) -> pd.DataFrame:
    df = context.copy()
    df["context_label"] = df["weather_rule"].replace(
        {"No adverse weather flag": "Normal weather"}
    )
    df["context_label"] = df["context_label"].fillna("Other")
    return df


def weather_condition_chart(context: pd.DataFrame) -> alt.Chart:
    chart_df = prepare_weather_context(context)

    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("context_label:N", title=None, sort="-y", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("record_pct:Q", title="Share of Records (%)"),
            color=alt.Color(
                "context_label:N",
                scale=alt.Scale(
                    domain=list(WEATHER_COLORS),
                    range=list(WEATHER_COLORS.values()),
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("context_label:N", title="Weather Context"),
                alt.Tooltip("records:Q", title="Records", format=","),
                alt.Tooltip("record_pct:Q", title="Share (%)", format=".1f"),
                alt.Tooltip("avg_observed_delay:Q", title="Avg Delay", format=".2f"),
            ],
        )
        .properties(height=255)
    )


def render_route_watchlist(route_examples: pd.DataFrame) -> None:
    st.markdown("### Weather-Exposed Route Watchlist")
    st.caption(
        "Routes below had observed delay during rain or high-wind records. Treat as review signals, not proof of weather causation."
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
        height=330,
    )


def render_operator_note() -> None:
    st.markdown(
        """
        <div class="operator-note">
            <strong>Operator Note:</strong>
            Weather indicators provide operational context only. Rainfall and wind observations
            were matched with GTFS-Realtime operational records and should not be interpreted
            as direct causes of transport delay. They are supporting evidence used by the AI model
            when estimating delay risk.
        </div>
        """,
        unsafe_allow_html=True,
    )
