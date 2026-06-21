import streamlit as st
import pydeck as pdk

from components.operator_layout import page_header
from services.drilldown_data import route_focus, route_options, route_prediction_examples
from services.route_map_data import route_shape_path


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

        st.subheader("Scheduled Route Map")
        route_path = route_shape_path(selected)
        if route_path.empty:
            st.info("Scheduled GTFS route shape is unavailable for this selected route.")
        else:
            map_row = route_path.iloc[0]
            layer = pdk.Layer(
                "PathLayer",
                route_path,
                get_path="path",
                get_color=[77, 183, 233],
                width_scale=18,
                width_min_pixels=4,
                pickable=True,
            )
            view_state = pdk.ViewState(
                latitude=float(map_row["latitude"]),
                longitude=float(map_row["longitude"]),
                zoom=10,
                pitch=0,
            )
            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip={"text": "Route {route_id}\nGTFS shape {shape_id}"},
                    map_style=None,
                ),
                use_container_width=True,
                height=360,
            )
            st.caption("Scheduled route alignment from GTFS Static. This is a visual route reference, not live vehicle tracking.")

    st.subheader("Route Prediction Examples")
    if examples.empty:
        st.warning("No prediction examples are available for the selected route and filter.")
    else:
        st.dataframe(examples, use_container_width=True, hide_index=True, height=460)
