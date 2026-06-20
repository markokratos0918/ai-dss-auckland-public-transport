import streamlit as st

from components.operator_layout import page_header
from services.drilldown_data import ai_prediction_examples, ai_prediction_summary, model_metrics


service_type, include_special, analysis_day, analysis_hour = page_header("ai_prediction_results")

st.subheader("AI Prediction Results")
st.info("AI-predicted risk shows where the model expects operational attention may be needed.")

summary = ai_prediction_summary(service_type, include_special, analysis_day, analysis_hour)
cols = st.columns(len(summary))
for col, (label, value) in zip(cols, summary.items()):
    col.metric(label, value)

metrics = model_metrics()
if not metrics.empty:
    st.subheader("Saved Model Metrics")
    st.dataframe(metrics, use_container_width=True, hide_index=True)

examples = ai_prediction_examples(250, service_type, include_special, analysis_day, analysis_hour)
st.subheader("Prediction Examples")
if examples.empty:
    st.warning("AI prediction examples are unavailable for the current filter.")
else:
    display = examples.copy()
    if "ai_probability" in display.columns:
        display["ai_probability"] = display["ai_probability"].map(lambda value: f"{value:.1%}")
    st.dataframe(display, use_container_width=True, hide_index=True, height=560)
