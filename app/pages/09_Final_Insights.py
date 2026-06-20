import streamlit as st

from components.operator_layout import page_header
from services.drilldown_data import top_observed_routes
from services.operator_data import attention_summary, operator_action_summary
from services.support_data import sumo_summary, top_features


service_type, include_special, analysis_day, analysis_hour = page_header("final_insights")

st.subheader("Final Insights")
st.info("This page summarizes the dashboard's decision-support answers for presentation and assessment.")

observed = top_observed_routes(1, service_type, include_special, analysis_day, analysis_hour)
ai = attention_summary(service_type, include_special, analysis_day, analysis_hour)
action = operator_action_summary(service_type, include_special, analysis_day, analysis_hour)
sumo, sumo_details = sumo_summary()
features = top_features(1)

if not observed.empty:
    row = observed.iloc[0]
    st.write(
        f"**Observed evidence:** `{row['route_id']}` has the strongest observed-delay signal "
        f"for the current filter, with average observed delay of {row['avg_observed_delay']:.2f} minutes."
    )

st.write(f"**AI prediction:** `{ai['route_id']}` is the top AI-risk route for the current filter.")
st.write(f"**Recommended action:** `{action['common']}` is the most common AI recommended action.")

if not sumo.empty:
    st.write(
        f"**SUMO scenario evidence:** saved Route `{sumo_details['route_id']}` outputs show "
        f"a scenario-estimated improvement of {sumo_details['improvement']}."
    )

if not features.empty:
    st.write(f"**Explainability:** top saved SHAP feature is `{features.iloc[0]['feature']}`.")

st.warning("This dashboard supports operator judgement and does not automatically control transport services.")
