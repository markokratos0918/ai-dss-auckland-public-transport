import streamlit as st

from components.operator_charts import action_bar
from components.operator_layout import page_header
from services.drilldown_data import intervention_logic
from services.operator_data import decision_summary, operator_action_summary


service_type, include_special, analysis_day, analysis_hour = page_header("decision_engine")

st.subheader("Decision Engine")
st.info("The Decision Engine translates AI risk categories into recommended operator actions.")

decision = decision_summary(service_type, include_special, analysis_day, analysis_hour)
summary = operator_action_summary(service_type, include_special, analysis_day, analysis_hour)

if decision.empty:
    st.warning("Decision Engine summary is unavailable for the current filter.")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Most Common AI Action", summary["common"])
    c2.metric("AI Severe Risk Count", summary["severe"])
    c3.metric("AI High + Severe Share", summary["risk_pct"])
    st.altair_chart(action_bar(decision), use_container_width=True)
    st.dataframe(decision, use_container_width=True, hide_index=True)

logic = intervention_logic()
st.subheader("Intervention Logic")
if logic.empty:
    st.warning("Intervention logic output is unavailable.")
else:
    st.dataframe(logic, use_container_width=True, hide_index=True)
