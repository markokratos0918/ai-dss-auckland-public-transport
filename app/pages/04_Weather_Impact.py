from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from components.operator_layout import page_header
from components.operator_weather import display_table
from services.weather_data import (
    rain_severity_breakdown,
    weather_context_summary,
    weather_integration_summary,
    weather_route_examples,
)


def _bar_chart(df: pd.DataFrame, x: str, y: str, tooltip: list[str], height: int = 260) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(color="#4db7e9")
        .encode(
            x=alt.X(x, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(y, title=None),
            tooltip=tooltip,
        )
        .properties(height=height)
    )


def _rain_severity_tiles(df: pd.DataFrame) -> None:
    order = ["No rain", "Light rain", "Moderate rain", "Heavier rain"]
    values = {row["rain_band"]: row for _, row in df.iterrows()}
    columns = st.columns(4)
    for column, label in zip(columns, order):
        row = values.get(label)
        pct = 0 if row is None else float(row["record_pct"])
        records = 0 if row is None else int(row["records"])
        with column:
            with st.container(border=True):
                st.metric(label, f"{pct:.1f}%")
                st.caption(f"{records:,} records")


service_type, include_special, analysis_day, analysis_hour = page_header("weather_impact")

st.subheader("Weather Context")
st.caption("Weather conditions matched to GTFS-Realtime records for operational review.")

summary = weather_integration_summary(service_type, include_special, analysis_day, analysis_hour)
context = weather_context_summary()
severity = rain_severity_breakdown(service_type, include_special, analysis_day, analysis_hour)
route_examples = weather_route_examples(service_type, include_special, analysis_day, analysis_hour, 8)

with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Weather Match Rate", summary["Match Rate"])
    with c2:
        st.html(
            f"""<div style="text-align:center;">
    <div style="font-size:0.78rem;font-weight:800;color:#ffffff;margin-bottom:0.35rem;">Dataset Period</div>
    <div style="font-size:1.75rem;line-height:1.2;color:#ffffff;">{summary["Period"]}</div>
</div>"""
        )
    c3.metric("Days", summary["Days"])
    c4.metric("Records", summary["Records"])

left, right = st.columns([1, 1])

with left.container(border=True, height=330):
    st.markdown("#### Weather Condition Mix")
    if context.empty:
        st.warning("Weather context summary is unavailable.")
    else:
        chart_data = context.copy()
        chart_data["context_label"] = chart_data["weather_rule"].replace(
            {"No adverse weather flag": "Normal weather"}
        )
        st.altair_chart(
            _bar_chart(
                chart_data,
                "context_label:N",
                "record_pct:Q",
                ["context_label:N", "records:Q", "record_pct:Q", "avg_observed_delay:Q"],
            ),
            use_container_width=True,
        )

with right.container(border=True, height=330):
    st.markdown("#### Rain Severity Mix")
    if severity.empty:
        st.warning("Rain severity is unavailable for the current filter.")
    else:
        _rain_severity_tiles(severity)
        st.info("Most records occurred with no rain or light rain, so severe-weather exposure was limited.")

st.markdown("#### Weather-Context Route Watchlist")
st.caption("Routes below had observed delay during rain or high-wind records. Treat as review signals, not proof of weather causation.")
if route_examples.empty:
    st.warning("Weather-context route examples are unavailable for the current filter.")
else:
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

st.info(
    "Operator interpretation: most records were collected under normal or light-weather conditions. "
    "Weather is useful context for route review, but route, service, time, and direction patterns were stronger AI signals."
)
