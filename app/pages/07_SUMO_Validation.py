import streamlit as st

from components.drilldown_visuals import sumo_colored_chart
from components.operator_layout import page_header
from components.page_summary import set_summary
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
    c4.metric("Scenario Time-Loss Reduction", details["improvement"])
    set_summary("SUMO Validation", 'A representative SUMO scenario showed a 45.6% reduction in simulated time loss after applying the recommended intervention. These results provide scenario-based validation evidence rather than proof of real-world performance.')

    st.subheader("Scheduled Scenario Route")
    scheduled_route_map(details["route_id"], height=300, zoom=10.0)
    st.caption("GTFS scheduled route shape for reference.")

    st.altair_chart(sumo_colored_chart(sumo), use_container_width=True)
    st.caption(
        "Bars are simulated average delay per scenario - sub-minute SUMO indicators, not real-world "
        "delay minutes. Completed trips differ by scenario (Baseline 78, Disruption 238, "
        "Intervention 123), so this is a scenario-level comparison, not a like-for-like experiment. "
        "The time-loss reduction is relative between the Disruption and Intervention scenarios."
    )

    ref_cols = [c for c in ["scenario_name", "congestion_index", "queue_impact", "service_reliability"] if c in sumo.columns]
    st.dataframe(sumo[ref_cols], use_container_width=True, hide_index=True)

    if "validation_interpretation" in sumo.columns:
        with st.expander("Scenario interpretation notes"):
            for _, r in sumo.iterrows():
                st.markdown(f"**{r['scenario_name']}** - {r['validation_interpretation']}")

    sumo_disclaimer()
