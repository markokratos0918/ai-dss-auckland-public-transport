from __future__ import annotations

import streamlit as st

from components.operator_layout import page_header
from components.page_summary import set_summary
from components.weather_impact import (
    inject_weather_css,
    render_operator_note,
    render_rain_panel,
    render_route_watchlist,
    render_weather_kpis,
    section_title,
    weather_condition_chart,
    weather_delay_impact_chart,
    weather_shap_chart,
)
from services.weather_data import (
    rain_severity_breakdown,
    weather_context_summary,
    weather_integration_summary,
    weather_route_examples,
    weather_shap_features,
)


service_type, include_special, analysis_day, analysis_hour = page_header("weather_impact")
inject_weather_css()

st.subheader("Weather Context")
st.caption("Weather conditions matched to GTFS-Realtime records for operational review.")

summary = weather_integration_summary(service_type, include_special, analysis_day, analysis_hour)
context = weather_context_summary()
severity = rain_severity_breakdown(service_type, include_special, analysis_day, analysis_hour)
set_summary("Weather Context", [
    f"Weather match: {summary.get('Match Rate','-')} over {summary.get('Days','-')} days",
    "Little measured effect on delay across rain bands",
    "Retained as context, not a proven driver",
])
route_examples = weather_route_examples(
    service_type,
    include_special,
    analysis_day,
    analysis_hour,
    8,
)
shap_features = weather_shap_features()

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

st.subheader("Does Weather Change Delay?")
if severity.empty:
    st.warning("Weather impact comparison is unavailable for the current filter.")
else:
    st.altair_chart(weather_delay_impact_chart(severity), use_container_width=True)
st.info(
    "Across the collected period, weather shows little measurable effect on delay: average observed "
    "delay stays close to zero across rain bands and AI risk probability barely moves; high-wind "
    "records even run slightly early. Weather is therefore retained as supporting context, not a "
    "proven driver of delay — useful, defensible limitations evidence rather than a causal claim."
)

st.subheader("How the AI Model Weights Weather (SHAP)")
if shap_features.empty:
    st.warning("Weather SHAP importances are unavailable.")
else:
    st.altair_chart(weather_shap_chart(shap_features), use_container_width=True)
    st.caption(
        "Mean absolute SHAP importance of weather features in the AI model. Weather contributes "
        "modestly and is treated as contextual evidence, not proof of causation."
    )

render_route_watchlist(route_examples)
render_operator_note()
