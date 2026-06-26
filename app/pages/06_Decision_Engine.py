from __future__ import annotations

import pandas as pd
import streamlit as st

from components.operator_charts import action_lollipop
from components.operator_layout import page_header
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
            <div class="flow-step risk">Risk Category</div>
            <div class="flow-arrow">→</div>
            <div class="flow-step rule">Decision Rule</div>
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

    if decision.empty:
        st.warning("Decision Engine summary is unavailable for the current filter.")
        return

    

    c1, c2, c3 = st.columns(3)
    c1.metric("Most Common AI Action", summary["common"])
    c2.metric("AI Severe Risk Count", summary["severe"])
    c3.metric("AI High + Severe Share", summary["risk_pct"])

    st.altair_chart(action_lollipop(decision), use_container_width=True)
    st.dataframe(decision, use_container_width=True, hide_index=True)


def render_logic_table(logic: pd.DataFrame) -> None:
    st.subheader("How Risk Becomes Action")
    st.markdown(
        """
        <div class="decision-note">
            The AI model assigns a delay-risk category. The Decision Engine applies
            transparent rules to convert that risk into an operator action.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_decision_flow()

    with st.expander("View Decision Rule Table", expanded=True):
        if logic.empty:
            st.warning("Decision rule table is unavailable.")
            return

        display_logic = logic.rename(
            columns={
                "delay_risk": "Delay Risk",
                "delay_minutes_rule": "Rule",
                "recommended_action": "Recommended Action",
                "operational_meaning": "Operator Meaning",
            }
        )
        st.dataframe(display_logic, use_container_width=True, hide_index=True)


service_type, include_special, analysis_day, analysis_hour = page_header("decision_engine")
inject_decision_engine_css()

st.subheader("Decision Engine")
st.info("The Decision Engine translates AI risk categories into recommended operator actions.")

render_decision_summary(service_type, include_special, analysis_day, analysis_hour)

logic = normalize_logic_table(intervention_logic())
render_logic_table(logic)