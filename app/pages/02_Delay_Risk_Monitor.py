import altair as alt
import pandas as pd
import streamlit as st

from components.operator_layout import page_header
from components.page_summary import set_summary
from services.operator_data import ALL_HOURS
from services.drilldown_data import (
    OBSERVED_SOURCE_BASELINE,
    OBSERVED_SOURCE_FULL,
    observed_daily,
    observed_delay_distribution,
    top_observed_routes,
)


def avg_delay_area_chart(daily, height: int = 260) -> alt.Chart:
    """Avg observed delay on its own zero-anchored axis.

    Area shaded blue when early (below 0) and red when late (above 0), so the
    near-zero variation is readable instead of flat against the max-delay scale.
    """
    df = daily[["collection_date", "avg_observed_delay"]].copy()
    df["avg_observed_delay"] = pd.to_numeric(df["avg_observed_delay"], errors="coerce").fillna(0.0)
    df["collection_date"] = pd.to_datetime(df["collection_date"], errors="coerce")
    df["early"] = df["avg_observed_delay"].clip(upper=0)
    df["late"] = df["avg_observed_delay"].clip(lower=0)
    x = alt.X("collection_date:T", title=None, axis=alt.Axis(format="%b %d", labelAngle=-45))
    base = alt.Chart(df)
    early_area = base.mark_area(color="#4db7e9", opacity=0.55).encode(
        x=x, y=alt.Y("early:Q", title="Avg observed delay (min)")
    )
    late_area = base.mark_area(color="#ef4444", opacity=0.55).encode(x=x, y=alt.Y("late:Q", title=None))
    line = base.mark_line(color="#cbd5e1", strokeWidth=1.5).encode(
        x=x,
        y=alt.Y("avg_observed_delay:Q", title=None),
        tooltip=[
            alt.Tooltip("collection_date:T", title="Date"),
            alt.Tooltip("avg_observed_delay:Q", title="Avg delay (min)", format=".2f"),
        ],
    )
    zero = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(color="#5d7da0", strokeDash=[3, 3])
        .encode(y="y:Q")
    )
    return (early_area + late_area + line + zero).properties(height=height).configure_view(stroke=None)


def delay_distribution_chart(dist, height: int = 240) -> alt.Chart:
    """Histogram of observed delay, bars coloured by early / on-time / late band."""
    order = ["Early-running", "Near on-time", "Late-running"]
    colors = {"Early-running": "#4db7e9", "Near on-time": "#8fa3b8", "Late-running": "#ef4444"}
    df = dist.copy()
    df["lo"] = df["bin_mid"] - 1
    df["hi"] = df["bin_mid"] + 1
    base = alt.Chart(df)
    bars = base.mark_bar().encode(
        x=alt.X("lo:Q", title="Observed delay (min, +late / −early)", scale=alt.Scale(domain=[-30, 30])),
        x2="hi:Q",
        y=alt.Y("count:Q", title="Count"),
        color=alt.Color(
            "band:N",
            scale=alt.Scale(domain=order, range=[colors[band] for band in order]),
            legend=alt.Legend(title=None, orient="top"),
        ),
        tooltip=[
            alt.Tooltip("bin_mid:Q", title="Delay (min)"),
            alt.Tooltip("count:Q", title="Count"),
            alt.Tooltip("band:N", title="Band"),
        ],
    )
    zero = (
        alt.Chart(pd.DataFrame({"x": [0]}))
        .mark_rule(color="#5d7da0", strokeDash=[3, 3])
        .encode(x="x:Q")
    )
    return (bars + zero).properties(height=height).configure_view(stroke=None)


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

st.subheader("Observed Delay Monitor")
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
    set_summary("Observed Delay Monitor", 'Observed GTFS-Realtime records indicate that overall services operated close to schedule throughout the monitoring period. Although average delay remained low, several isolated disruption events produced high maximum delays. These observed patterns establish the operational baseline used by the subsequent AI prediction and decision-support modules.')
    left_chart, right_chart = st.columns(2)
    with left_chart:
        st.caption("Max Observed Delay (min)")
        st.line_chart(
            daily.set_index("collection_date")[["max_observed_delay"]],
            color=["#ef4444"],
            height=260,
        )
    with right_chart:
        st.caption("Avg Observed Delay (min) — early (−) vs late (+)")
        st.altair_chart(avg_delay_area_chart(daily), use_container_width=True)

    st.subheader("Observed Delay Distribution")
    distribution = observed_delay_distribution(service_type, include_special, analysis_day, analysis_hour, source_mode)
    if distribution.empty:
        st.warning("Delay distribution is unavailable for the current filter.")
    else:
        st.altair_chart(delay_distribution_chart(distribution), use_container_width=True)
        st.caption(
            "Observed delay distribution, clipped to ±30 min. Storage-summary mode bins route-day "
            "averages; baseline mode bins individual records."
        )

st.subheader("Top Observed Delayed Routes")
if routes.empty:
    st.warning("Observed route delay evidence is unavailable for the current filter.")
else:
    st.dataframe(observed_routes_display(routes), use_container_width=True, hide_index=True, height=560)
