from __future__ import annotations

import pandas as pd
import streamlit as st

from components.operator_charts import action_lollipop
from components.operator_layout import page_header
from components.page_summary import set_summary
from services.drilldown_data import intervention_logic
from services.operator_data import decision_summary, operator_action_summary


def inject_decision_engine_css() -> None:
    st.markdown(
        """
        <style>
        .decision-flow {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin: 0.8rem 0 1rem 0;
        }

        .flow-step {
            border: 1px solid rgba(120, 150, 190, 0.25);
            border-radius: 10px;
            background: rgba(21, 36, 58, 0.85);
            padding: 0.7rem 1rem;
            color: #ffffff;
            font-weight: 800;
            text-align: center;
            min-width: 155px;
        }

        .flow-step.ai { border-color: rgba(77, 183, 255, 0.55); }
        .flow-step.risk { border-color: rgba(255, 200, 87, 0.65); }
        .flow-step.rule { border-color: rgba(255, 159, 67, 0.65); }
        .flow-step.action { border-color: rgba(57, 211, 83, 0.60); }

        .flow-arrow {
            color: #58c7ff;
            font-size: 1.35rem;
            font-weight: 900;
        }

        .decision-note {
            color: #aebacc;
            font-size: 0.9rem;
            margin-top: 0.2rem;
            margin-bottom: 0.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_logic_table(logic: pd.DataFrame) -> pd.DataFrame:
    if logic.empty:
        return logic

    df = logic.copy()
    df = df.rename(
        columns={
            "Delay Risk": "delay_risk",
            "Rule": "delay_minutes_rule",
            "Recommended Action": "recommended_action",
            "Meaning": "operational_meaning",
            "risk": "delay_risk",
            "rule": "delay_minutes_rule",
            "action": "recommended_action",
            "meaning": "operational_meaning",
        }
    )

    required = [
        "delay_risk",
        "delay_minutes_rule",
        "recommended_action",
        "operational_meaning",
    ]

    for col in required:
        if col not in df.columns:
            df[col] = ""

    return df[required]


def render_decision_flow() -> None:
    st.markdown(
        """
        <div class="decision-flow">
            <div class="flow-step ai">AI Prediction</div>
            <div class="flow-arrow">→</div>
            <div class="flow-step risk">Probability Band</div>
            <div class="flow-arrow">→</div>
            <div class="flow-step rule">Band Rule</div>
            <div class="flow-arrow">→</div>
            <div class="flow-step action">Operator Action</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_summary(
    service_type: str,
    include_special: bool,
    analysis_day: str,
    analysis_hour: str,
) -> None:
    decision = decision_summary(service_type, include_special, analysis_day, analysis_hour)
    summary = operator_action_summary(service_type, include_special, analysis_day, analysis_hour)
    set_summary("Decision Engine", 'AI risk probabilities are translated into four operational response levels. Most trips require either no action or routine monitoring, while only a small fraction progress to service adjustments or supervisor intervention.')

    if decision.empty:
        st.warning("Decision Engine summary is unavailable for the current filter.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Most Common AI Action", summary["common"])
    c2.metric("AI Severe Risk Count", summary["severe"])
    c3.metric("AI High + Severe Share", summary["risk_pct"])

    st.altair_chart(action_lollipop(decision), use_container_width=True)
    st.dataframe(decision, use_container_width=True, hide_index=True)


AI_BAND_RULES = pd.DataFrame(
    [
        {"AI Risk Band": "Low", "Probability of actionable delay": "< 50%",
         "Recommended Action": "No operational action required",
         "Meaning": "Unlikely to need attention."},
        {"AI Risk Band": "Medium", "Probability of actionable delay": "50% - 70%",
         "Recommended Action": "Monitor route conditions",
         "Meaning": "Watch for emerging disruption."},
        {"AI Risk Band": "High", "Probability of actionable delay": "70% - 85%",
         "Recommended Action": "Adjust service headway",
         "Meaning": "Likely actionable; consider spacing or dispatch."},
        {"AI Risk Band": "Severe", "Probability of actionable delay": ">= 85%",
         "Recommended Action": "Deploy standby bus or supervisor review",
         "Meaning": "High chance of disruption; active review."},
    ]
)


def render_logic_table(logic: pd.DataFrame) -> None:
    st.subheader("How Risk Becomes Action")
    st.markdown(
        """
        <div class="decision-note">
            The AI model outputs a probability that a trip is an actionable case. The Decision
            Engine maps that probability band to a fixed operator action.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_decision_flow()

    with st.expander("AI decision rule (probability band -> action)", expanded=True):
        st.dataframe(AI_BAND_RULES, use_container_width=True, hide_index=True)
        st.caption(
            "AI risk is a probability band (chance a trip is actionable), not minutes late. "
            "This band-to-action mapping is exactly what the engine applies at runtime."
        )

    with st.expander("Observed-delay reference (separate minute-based scale)", expanded=False):
        if logic.empty:
            st.warning("Observed-delay reference is unavailable.")
        else:
            display_logic = logic.rename(
                columns={
                    "delay_risk": "Band label",
                    "delay_minutes_rule": "Observed delay rule",
                    "recommended_action": "Reference action",
                    "operational_meaning": "Meaning",
                }
            )
            st.dataframe(display_logic, use_container_width=True, hide_index=True)
        st.caption(
            "This minute-based scale describes observed delay magnitude. It reuses the same "
            "Low/Medium/High/Severe words but is NOT how the AI assigns its probability band."
        )


service_type, include_special, analysis_day, analysis_hour = page_header("decision_engine")
inject_decision_engine_css()

st.subheader("Decision Engine")
st.info("The Decision Engine maps the AI probability band of each trip to a recommended operator action.")

render_decision_summary(service_type, include_special, analysis_day, analysis_hour)

logic = normalize_logic_table(intervention_logic())
render_logic_table(logic)