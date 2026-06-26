from __future__ import annotations

import streamlit as st

from components.operator_layout import page_header
from components.weather_impact import (
    inject_weather_css,
    render_operator_note,
    render_rain_panel,
    render_route_watchlist,
    render_weather_kpis,
    section_title,
    weather_condition_chart,
)
from services.weather_data import (
    rain_severity_breakdown,
    weather_context_summary,
    weather_integration_summary,
    weather_route_examples,
)


service_type, include_special, analysis_day, analysis_hour = page_header("weather_impact")
inject_weather_css()

st.subheader("Weather Impact")
st.caption("Weather conditions matched to GTFS-Realtime records for operational review.")

summary = weather_integration_summary(service_type, include_special, analysis_day, analysis_hour)
context = weather_context_summary()
severity = rain_severity_breakdown(service_type, include_special, analysis_day, analysis_hour)
route_examples = weather_route_examples(
    service_type,
    include_special,
    analysis_day,
    analysis_hour,
    8,
)

render_weather_kpis(summary)

# Critical spacer: prevents the chart row from overlapping the KPI cards.
st.markdown("<div class='weather-row-spacer'></div>", unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="small")

with left:
    with st.container(border=True, height=330):
        section_title("Weather Condition Distribution")
        if context.empty:
            st.warning("Weather context summary is unavailable.")
        else:
            st.altair_chart(weather_condition_chart(context), use_container_width=True)

with right:
    render_rain_panel(severity)

render_route_watchlist(route_examples)
render_operator_note()