import streamlit as st

from components.operator_cards import network_card_row
from components.operator_charts import action_lollipop, risk_donut, shap_bar
from components.drilldown_visuals import sumo_colored_chart
from components.operator_layout import page_header
from components.operator_tables import delayed_routes_table
from components.overview_panels import (
    overview_action_footer,
    overview_risk_footer,
    overview_risk_legend,
    overview_routes_style,
    overview_routes_table,
)
from components.overview_story import render_decision_story
from services.operator_data import (
    attention_summary,
    decision_summary,
    high_severe_risk_percentage,
    network_kpis,
    operator_action_summary,
    risk_percentages,
    top_non_special_routes,
)
from services.support_data import sumo_summary, top_features
from theme import load_dashboard_styles
from components.page_summary import set_summary


load_dashboard_styles()
service_type, include_special, analysis_day, analysis_hour = page_header("overview")

network = network_kpis(service_type, include_special, analysis_day, analysis_hour)
attention = attention_summary(service_type, include_special, analysis_day, analysis_hour)
decision = decision_summary(service_type, include_special, analysis_day, analysis_hour)
summary = operator_action_summary(service_type, include_special, analysis_day, analysis_hour)
sumo, details = sumo_summary()
_top = top_non_special_routes(1, service_type, include_special, analysis_day, analysis_hour)
_top_route = ""
if not _top.empty:
    _r0 = _top.iloc[0]
    _top_route = str(_r0.get("route_corridor_name") or _r0.get("route_id") or "").strip()
set_summary(
    "Overview",
    "The network is operating with generally stable service reliability. "
    f"Most AI recommendations advise '{summary['common']}' rather than immediate intervention, "
    f"while only {summary['risk_pct']} of services fall into the High or Severe risk categories."
    + (f" The highest predicted operational priority for review is {_top_route}." if _top_route else ""),
)

network_card_row(network)
render_decision_story(network, attention, summary, service_type, include_special, analysis_day, analysis_hour)

if decision.empty:
    st.warning("AI-DSS summary is unavailable for the current filter.")
else:
    left, middle, right = st.columns([1, 1, 1])
    with left:
        with st.container(border=True, height=510):
            st.subheader("AI Delay Risk Forecast")
            chart_col, legend_col = st.columns([1.6, 1])
            with chart_col:
                st.altair_chart(risk_donut(decision, 68, 114, 305), use_container_width=True)
            with legend_col:
                overview_risk_legend(risk_percentages(service_type, include_special, analysis_day, analysis_hour))
            overview_risk_footer(
                high_severe_risk_percentage(service_type, include_special, analysis_day, analysis_hour)
            )

    with middle:
        with st.container(border=True, height=510):
            st.subheader("At-Risk Routes")
            source_routes = top_non_special_routes(10, service_type, include_special, analysis_day, analysis_hour)
            routes = delayed_routes_table(source_routes)
            st.dataframe(
                overview_routes_style(overview_routes_table(routes)),
                use_container_width=True,
                hide_index=True,
                height=410,
            )

    with right:
        with st.container(border=True, height=510):
            st.subheader("Recommended Actions")
            st.altair_chart(action_lollipop(decision, height=305), use_container_width=True)
            overview_action_footer(summary)

    lower_left, lower_right = st.columns([1, 1])
    with lower_left:
        with st.container(border=True, height=455):
            st.subheader("SUMO Scenario Snapshot")
            if sumo.empty:
                st.info("SUMO scenario outputs are unavailable.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Route", details["route_id"])
                c2.metric("Scenario Date", details["scenario_date"])
                c3.metric("Estimated Impact", details["improvement"])
                st.altair_chart(sumo_colored_chart(sumo), use_container_width=True)
                st.html('<p style="color:#f59e0b; font-size:0.875rem;">⚠ SUMO results represent scenario-estimated impacts and do not guarantee operational outcomes</p>')

    with lower_right:
        features = top_features(5)
        with st.container(border=True, height=455):
            st.subheader("Explainability Snapshot")
            if features.empty:
                st.info("SHAP feature summary is unavailable.")
            else:
                st.altair_chart(shap_bar(features), use_container_width=True)
                st.info(
                    "Top explanation features show which route, service, time, or weather patterns shaped the AI risk signal."
                )
