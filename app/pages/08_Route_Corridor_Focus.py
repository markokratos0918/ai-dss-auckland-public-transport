import streamlit as st

from components.drilldown_visuals import route_weather_cards
from components.operator_layout import page_header
from components.route_maps import scheduled_route_map
from services.drilldown_data import route_focus, route_prediction_examples
from services.drilldown_enhancements import format_route_label, route_options_by_risk


SUMMARY_COLORS = {
    "Observed Records": "#38bdf8",
    "Avg Observed Delay": "#facc15",
    "Avg Predicted Delay": "#fb7185",
    "AI Probability": "#22c55e",
}


def _metric_tile(label: str, value: str, color: str) -> str:
    return (
        f'<div style="border:1px solid rgba(93,125,160,.45);border-radius:.5rem;padding:.75rem .85rem;">'
        f'<div style="color:{color};font-size:.78rem;font-weight:850;">{label}</div>'
        f'<div style="color:#fff;font-size:1.75rem;line-height:1.2;">{value}</div>'
        f'</div>'
    )


service_type, include_special, analysis_day, analysis_hour = page_header("route_corridor_focus")

st.subheader("Route / Corridor Focus")
st.info("This drill-down connects observed delay evidence, AI-predicted risk, and the recommended action for one route.")

options = route_options_by_risk("All", service_type, include_special, analysis_day, analysis_hour)
if options.empty:
    st.warning("Route options are unavailable for the current filter.")
else:
    route_labels = [
        format_route_label(str(row["route_id"]), str(row.get("route_corridor_name", "") or ""))
        for _, row in options.iterrows()
    ]
    selected_label = st.selectbox("Route", route_labels)
    selected = str(options.iloc[route_labels.index(selected_label)]["route_id"])

    focus = route_focus(selected, service_type, include_special, analysis_day, analysis_hour)
    examples = route_prediction_examples(selected, 250, service_type, include_special, analysis_day, analysis_hour)

    if focus.empty:
        st.warning("Route focus data is unavailable for the selected route.")
    else:
        row = focus.iloc[0]
        metric_values = {
            "Observed Records": f"{int(row['records']):,}",
            "Avg Observed Delay": f"{row['avg_observed_delay']:.2f} min",
            "Avg Predicted Delay": f"{row['avg_predicted_delay']:.2f} min",
            "AI Probability": f"{row['avg_ai_probability_pct']:.1f}%",
        }
        cols = st.columns(4)
        for col, (label, value) in zip(cols, metric_values.items()):
            with col:
                st.html(_metric_tile(label, value, SUMMARY_COLORS[label]))

        st.write(f"**Recommended Action:** {row['recommended_action']}")
        st.write(f"**Corridor:** {row['corridor_name']}")
        route_weather_cards(row)

        st.subheader("Scheduled Route Map")
        scheduled_route_map(selected, height=360, zoom=10.0)
        st.caption("Scheduled route alignment from GTFS Static. This is a visual route reference, not live vehicle tracking.")

    st.subheader("Route Prediction Examples")
    if examples.empty:
        st.warning("No prediction examples are available for the selected route and filter.")
    else:
        st.dataframe(examples, use_container_width=True, hide_index=True, height=460)
