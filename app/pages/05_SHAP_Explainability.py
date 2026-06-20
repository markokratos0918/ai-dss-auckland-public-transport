import streamlit as st

from components.operator_charts import shap_bar
from components.operator_layout import page_header
from components.operator_sections import explainability_panel
from services.support_data import top_features


page_header("shap_explainability")

st.subheader("SHAP Explainability")
features = top_features(15)
if features.empty:
    st.warning("AI explainability summary is unavailable.")
else:
    left, right = st.columns([2, 1])
    with left:
        st.altair_chart(shap_bar(features), use_container_width=True)
    with right:
        explainability_panel()
    st.dataframe(features, use_container_width=True, hide_index=True)
    st.caption("SHAP values explain model behaviour; they do not automatically prescribe an intervention.")
