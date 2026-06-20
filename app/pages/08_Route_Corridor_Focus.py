import streamlit as st

from components.operator_layout import page_header
from services.drilldown_data import route_focus, route_options, route_prediction_examples


service_type, include_special, analysis_day, analysis_hour = page_header("route_corridor_focus")

st.subheader("Route / Corridor Focus")
st.info("This drill-down connects observed delay evidence, AI-predicted risk, and the recommended action for one route.")

options = route_options(service_type, include_special, analysis_day, analysis_hour)
if options.empty:
    st.warning("Route options are unavailable for the current filter.")
else:
    selected = st.selectbox("Route", options["route_id"].astype(str).tolist())
    focus = route_focus(selected, service_type, include_special, analysis_day, analysis_hour)
    examples = route_prediction_examples(selected, 250, service_type, include_special, analysis_day, analysis_hour)

    if focus.empty:
        st.warning("Route focus data is unavailable for the selected route.")
    else:
        row = focus.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Observed Records", f"{int(row['records']):,}")
        c2.metric("Avg Observed Delay", f"{row['avg_observed_delay']:.2f} min")
        c3.metric("Avg Predicted Delay", f"{row['avg_predicted_delay']:.2f} min")
        c4.metric("AI Probability", f"{row['avg_ai_probability_pct']:.1f}%")
        st.write(f"**Recommended Action:** {row['recommended_action']}")
        st.write(f"**Corridor:** {row['corridor_name']}")

    st.subheader("Route Prediction Examples")
    if examples.empty:
        st.warning("No prediction examples are available for the selected route and filter.")
    else:
        st.dataframe(examples, use_container_width=True, hide_index=True, height=460)
