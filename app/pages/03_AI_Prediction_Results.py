import streamlit as st
from html import escape

from components.drilldown_visuals import diverging_reliability_chart
from components.operator_charts import actionable_observed_vs_predicted
from components.operator_layout import page_header
from components.page_summary import set_summary
from theme.colors import CARD_COLORS
from services.drilldown_data import (
    ai_prediction_summary,
    balanced_prediction_examples,
    model_evidence_summary,
    model_metrics,
    reliability_timing_mix,
    risk_category_cards,
)
from services.prediction_comparison_data import route_actionable_signal_scatter


def metric_card(label: str, value: str, caption: str = "") -> None:
    color = CARD_COLORS.get(label, "#38bdf8")
    st.html(
        f"""<div style="border:1px solid rgba(93,125,160,.55);border-radius:.55rem;
padding:.85rem 1rem;background:rgba(12,16,24,.36);min-height:6.1rem;">
    <div style="color:{color};font-size:.78rem;font-weight:850;">{escape(label)}</div>
    <div style="color:#fff;font-size:1.65rem;font-weight:850;line-height:1.2;margin-top:.2rem;">{escape(value)}</div>
    <div style="color:#a8b3c5;font-size:.78rem;font-weight:700;margin-top:.55rem;">{escape(caption)}</div>
</div>"""
    )


def metric_lookup(metrics, model_text: str, metric_name: str):
    rows = metrics[
        metrics["model"].astype(str).str.contains(model_text, case=False, regex=False)
        & (metrics["metric"].astype(str).str.lower() == metric_name.lower())
    ]
    if rows.empty:
        return None
    return float(rows.iloc[0]["value"])


def extra_model_evidence(metrics) -> dict[str, str]:
    values = {
        "Baseline Accuracy": metric_lookup(metrics, "Most frequent baseline", "accuracy"),
        "XGBoost Precision": metric_lookup(metrics, "XGBoost classifier", "precision"),
        "XGBoost RMSE": metric_lookup(metrics, "XGBoost regressor", "rmse"),
        "ARIMA Hourly RMSE": metric_lookup(metrics, "ARIMA", "rmse"),
    }
    return {
        label: ("Unavailable" if value is None else (f"{value:.1%}" if "Accuracy" in label or "Precision" in label else f"{value:.2f}"))
        for label, value in values.items()
    }


service_type, include_special, analysis_day, analysis_hour = page_header("ai_prediction_results")

st.subheader("AI Prediction Results")
st.info(
    "AI-predicted risk in this prototype refers to schedule-reliability risk. This includes "
    "late-running risk and early-running reliability concerns where the model identifies operational "
    "attention may be needed."
)

summary = ai_prediction_summary(service_type, include_special, analysis_day, analysis_hour)
set_summary("AI Prediction Results", 'The AI model extends observed operational data by identifying services with elevated schedule-reliability risk before intervention is required. It is intentionally optimized for higher recall so that more potentially disruptive services are detected, supporting proactive monitoring and operational decision-making.')
for col, (label, value) in zip(st.columns(len(summary)), summary.items()):
    with col:
        metric_card(label, value)

left, right = st.columns(2)
with left.container(border=True):
    st.subheader("AI vs Observed Actionable Risk")
    comparison = route_actionable_signal_scatter(service_type, include_special, analysis_day, analysis_hour)
    if comparison.empty:
        st.warning("Actionable risk comparison is unavailable for the current filter.")
    else:
        st.altair_chart(actionable_observed_vs_predicted(comparison), use_container_width=True)
        st.caption(
            "Each dot is a route: observed actionable trips (x) vs AI-flagged (y). Dots above the "
            "dashed line are routes the AI flags more often than observed — its recall-favouring "
            "over-flagging (more real cases caught, but more false alarms)."
        )

with right.container(border=True):
    st.subheader("Early vs Late Reliability")
    timing = reliability_timing_mix(service_type, include_special, analysis_day, analysis_hour)
    st.altair_chart(diverging_reliability_chart(timing), use_container_width=True)
    st.caption(
        "Diverging from the centre: early-running (left) vs late-running (right), with near "
        "on-time straddling the centre. Early-running can still reduce reliability because "
        "passengers may miss services."
    )

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
        metric_card(risk, f"{records:,}", f"{share:.2f}% | {action}")

st.subheader("Model Evidence Summary")
st.info(
    "How to read these: the AI is tuned to catch problems, not to be precise. It correctly catches "
    "about 76% of genuinely actionable trips (recall) but only ~33% of its flags are correct "
    "(precision) — the rest are false alarms. A do-nothing baseline scores 77% accuracy yet catches "
    "0% of real cases (recall 0%), which is why accuracy alone is misleading here."
)
evidence = model_evidence_summary()
for col, (label, value) in zip(st.columns(4), evidence.items()):
    with col:
        metric_card(label, value)

metrics = model_metrics()
if not metrics.empty:
    for col, (label, value) in zip(st.columns(4), extra_model_evidence(metrics).items()):
        with col:
            metric_card(label, value)
    st.caption(
        "ARIMA Hourly RMSE measures hourly-average delay (a different target), so it is not directly "
        "comparable to the row-level XGBoost RMSE above."
    )
if not metrics.empty:
    with st.expander("Detailed model evidence"):
        st.dataframe(metrics, use_container_width=True, hide_index=True)

examples = balanced_prediction_examples(service_type, include_special, analysis_day, analysis_hour)
st.subheader("Prediction Example Mix")
st.caption(
    "A balanced illustrative sample (one row per risk × timing combination), not the real "
    "frequency mix. Probabilities look rounded because the sample picks band-representative trips; "
    "the full model produces thousands of distinct probability values."
)
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
            "service_type": "Service Type",
            "observed_delay": "Observed Delay",
            "predicted_delay": "Predicted Delay",
            "ai_probability": "AI Probability",
            "ai_delay_risk": "AI Risk",
            "ai_recommended_action": "Recommended Action",
            "timing_band": "Reliability Timing",
        }
    )
    columns = [
        "Date", "Route / Corridor", "Service Type", "Observed Delay",
        "Predicted Delay", "AI Probability", "AI Risk", "Reliability Timing", "Recommended Action",
    ]
    st.dataframe(
        display[[col for col in columns if col in display.columns]],
        use_container_width=True,
        hide_index=True,
    )
