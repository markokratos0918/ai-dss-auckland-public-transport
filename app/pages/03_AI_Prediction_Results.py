import altair as alt
import streamlit as st

from components.operator_layout import page_header
from services.drilldown_data import (
    actionable_risk_comparison,
    ai_prediction_summary,
    balanced_prediction_examples,
    model_evidence_summary,
    model_metrics,
    reliability_timing_mix,
    risk_category_cards,
)


service_type, include_special, analysis_day, analysis_hour = page_header("ai_prediction_results")

st.subheader("AI Prediction Results")
st.info(
    "AI-predicted risk in this prototype refers to schedule-reliability risk. This includes "
    "late-running risk and early-running reliability concerns where the model identifies operational "
    "attention may be needed."
)

summary = ai_prediction_summary(service_type, include_special, analysis_day, analysis_hour)
for col, (label, value) in zip(st.columns(len(summary)), summary.items()):
    col.metric(label, value)

left, right = st.columns(2)
with left.container(border=True):
    st.subheader("AI vs Observed Actionable Risk")
    comparison = actionable_risk_comparison(service_type, include_special, analysis_day, analysis_hour)
    if comparison.empty:
        st.warning("Actionable risk comparison is unavailable for the current filter.")
    else:
        chart = (
            alt.Chart(comparison)
            .mark_bar(color="#4db7e9")
            .encode(
                x=alt.X("Records:Q", title=None, axis=alt.Axis(format="~s")),
                y=alt.Y("Signal:N", title=None, sort="-x", axis=alt.Axis(labelLimit=260)),
                tooltip=["Signal:N", "Records:Q"],
            )
            .properties(height=210)
        )
        st.altair_chart(chart, use_container_width=True)
        st.caption("The AI layer produces its own risk signal rather than only copying observed labels.")

with right.container(border=True):
    st.subheader("Early vs Late Reliability")
    timing = reliability_timing_mix(service_type, include_special, analysis_day, analysis_hour)
    chart = (
        alt.Chart(timing)
        .mark_bar(color="#4db7e9")
        .encode(
            x=alt.X("records:Q", title=None, axis=alt.Axis(format="~s")),
            y=alt.Y("timing_band:N", title=None, sort=["Early-running", "Near on-time", "Late-running"]),
            tooltip=["timing_band:N", "records:Q", "share_pct:Q"],
        )
        .properties(height=210)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("Early-running can still reduce reliability because passengers may miss services.")

st.subheader("Risk Categories and Recommended Actions")
risk_cards = risk_category_cards(service_type, include_special, analysis_day, analysis_hour)
for column, risk in zip(st.columns(4), ["Low", "Medium", "High", "Severe"]):
    row = risk_cards[risk_cards["ai_delay_risk"].astype(str) == risk]
    if row.empty:
        records, share, action = 0, 0, "Unavailable"
    else:
        item = row.iloc[0]
        records, share, action = int(item["records"]), float(item["share_pct"]), str(item["recommended_action"])
    with column.container(border=True):
        st.metric(risk, f"{records:,}", f"{share:.2f}%")
        st.caption(action)

st.subheader("Model Evidence Summary")
evidence = model_evidence_summary()
for col, (label, value) in zip(st.columns(4), evidence.items()):
    col.metric(label, value)

metrics = model_metrics()
if not metrics.empty:
    with st.expander("Detailed model evidence"):
        st.dataframe(metrics, use_container_width=True, hide_index=True)

examples = balanced_prediction_examples(service_type, include_special, analysis_day, analysis_hour)
st.subheader("Prediction Example Mix")
if examples.empty:
    st.warning("AI prediction examples are unavailable for the current filter.")
else:
    display = examples.copy()
    if "ai_probability" in display.columns:
        display["ai_probability"] = display["ai_probability"].map(lambda value: f"{value:.1%}")
    display = display.rename(
        columns={
            "collection_date": "Date",
            "corridor_name": "Route / Corridor",
            "observed_delay": "Observed Delay",
            "predicted_delay": "Predicted Delay",
            "ai_probability": "AI Probability",
            "ai_delay_risk": "AI Risk",
            "ai_recommended_action": "Recommended Action",
            "timing_band": "Reliability Timing",
        }
    )
    columns = [
        "Date",
        "Route / Corridor",
        "Observed Delay",
        "Predicted Delay",
        "AI Probability",
        "AI Risk",
        "Reliability Timing",
        "Recommended Action",
    ]
    st.dataframe(display[[column for column in columns if column in display.columns]], use_container_width=True, hide_index=True)
