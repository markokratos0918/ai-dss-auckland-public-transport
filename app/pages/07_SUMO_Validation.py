import streamlit as st

from components.drilldown_visuals import sumo_colored_chart
from components.operator_layout import page_header
from components.operator_sections import sumo_disclaimer
from components.route_maps import scheduled_route_map
from services.support_data import sumo_summary


page_header("sumo_validation_detail")

st.subheader("SUMO Scenario Evidence")
st.info(
    "SUMO is saved scenario-estimated evidence for Route 128-202. "
    "It is one selected validation scenario, not a live recommendation for every route. "
    "It does not validate the current top AI-risk route and does not prove real-world operational outcomes."
)

sumo, details = sumo_summary()
if sumo.empty:
    st.warning("SUMO scenario validation outputs are unavailable.")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scenario Route", details["route_id"])
    c2.metric("Route Name", details["route_name"])
    c3.metric("Scenario Date", details["scenario_date"])
    c4.metric("Estimated Improvement", details["improvement"])

    st.subheader("Scheduled Scenario Route")
    scheduled_route_map(details["route_id"], height=300, zoom=10.0)
    st.caption("GTFS scheduled route shape for reference.")

    st.altair_chart(sumo_colored_chart(sumo), use_container_width=True)
    st.dataframe(sumo, use_container_width=True, hide_index=True)
    sumo_disclaimer()
