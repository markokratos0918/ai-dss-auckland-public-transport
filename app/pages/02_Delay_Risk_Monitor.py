import streamlit as st

from components.operator_layout import page_header
from services.operator_data import ALL_HOURS
from services.drilldown_data import (
    OBSERVED_SOURCE_BASELINE,
    OBSERVED_SOURCE_FULL,
    observed_daily,
    top_observed_routes,
)


def observed_routes_display(routes):
    display = routes.copy()
    rename_map = {
        "route_id": "Route ID",
        "service_type": "Service Type",
        "corridor_name": "Corridor Name",
        "route_display_name": "Route Name",
        "route_name": "Route Name",
        "records": "Records",
        "avg_observed_delay": "Avg Observed Delay",
        "max_observed_delay": "Max Observed Delay",
        "high_severe_cases": "High/Severe Cases",
    }
    display = display.rename(columns=rename_map)
    if "Corridor Name" not in display.columns and "Route Name" in display.columns:
        display["Corridor Name"] = display["Route Name"]
    if "Service Type" not in display.columns:
        display["Service Type"] = "Unavailable"
    columns = [
        "Route ID",
        "Service Type",
        "Corridor Name",
        "Route Name",
        "Records",
        "Avg Observed Delay",
        "Max Observed Delay",
        "High/Severe Cases",
    ]
    display = display[[column for column in columns if column in display.columns]]
    for column in ["Records", "High/Severe Cases"]:
        if column in display.columns:
            display[column] = display[column].map(lambda value: f"{int(value):,}" if value == value else "")
    for column in ["Avg Observed Delay", "Max Observed Delay"]:
        if column in display.columns:
            display[column] = display[column].map(lambda value: f"{float(value):.2f} min" if value == value else "")
    return display


service_type, include_special, analysis_day, analysis_hour = page_header("delay_risk_monitor", sticky=True)

st.subheader("Observed Delay Risk Monitor")
st.caption("Observed delay shows what happened in the collected GTFS-Realtime data.")
source_mode = st.radio(
    "Observed data source",
    [OBSERVED_SOURCE_FULL, OBSERVED_SOURCE_BASELINE],
    horizontal=True,
    key="delay_risk_monitor_observed_source",
)
if source_mode == OBSERVED_SOURCE_FULL and analysis_hour != ALL_HOURS:
    st.info("Observed storage summaries are daily outputs, so the hour filter is not applied on this page.")

daily = observed_daily(service_type, include_special, analysis_day, analysis_hour, source_mode)
routes = top_observed_routes(50, service_type, include_special, analysis_day, analysis_hour, source_mode)

if daily.empty:
    st.warning("Observed daily delay evidence is unavailable for the current filter.")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Observation Days", f"{daily['collection_date'].nunique():,}")
    c2.metric("Total Observations", f"{int(daily['records'].sum()):,}")
    c3.metric("Avg Observed Delay", f"{daily['avg_observed_delay'].mean():.2f} min")
    if "high_severe_cases" in daily.columns:
        c4.metric("Observed High/Severe", f"{int(daily['high_severe_cases'].sum()):,}")
    else:
        c4.metric("Max Observed Delay", f"{daily['max_observed_delay'].max():.2f} min")
    st.line_chart(
        daily.set_index("collection_date")[["avg_observed_delay", "max_observed_delay"]],
        color=["#4db7e9", "#ef4444"],
        height=260,
    )

st.subheader("Top Observed Delayed Routes")
if routes.empty:
    st.warning("Observed route delay evidence is unavailable for the current filter.")
else:
    st.dataframe(observed_routes_display(routes), use_container_width=True, hide_index=True, height=560)
