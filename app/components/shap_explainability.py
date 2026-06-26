from __future__ import annotations

from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from components.shap_explainability_data import (
    classify_feature,
    clean_feature_label,
    prepare_features,
)
from components.shap_explainability_styles import CATEGORY_COLORS, inject_shap_css


__all__ = [
    "classify_feature",
    "clean_feature_label",
    "prepare_features",
    "inject_shap_css",
    "shap_driver_chart",
    "render_top_driver_cards",
    "render_interpretation",
    "render_feature_table",
    "render_shap_page",
]


def shap_driver_chart(features: pd.DataFrame) -> alt.Chart:
    chart_df = features.head(10).copy()
    sort_order = chart_df["display_feature"].tolist()

    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                "importance:Q",
                title="Mean |SHAP value|",
                axis=alt.Axis(format=".2f", tickCount=6),
            ),
            y=alt.Y(
                "display_feature:N",
                sort=sort_order,
                title=None,
                axis=alt.Axis(labelLimit=340),
            ),
            color=alt.Color(
                "category:N",
                scale=alt.Scale(
                    domain=list(CATEGORY_COLORS),
                    range=list(CATEGORY_COLORS.values()),
                ),
                title="Driver type",
            ),
            tooltip=[
                alt.Tooltip("display_feature:N", title="Feature"),
                alt.Tooltip("category:N", title="Type"),
                alt.Tooltip("importance:Q", title="Importance", format=".3f"),
            ],
        )
        .properties(height=340)
    )


def render_top_driver_cards(features: pd.DataFrame) -> None:
    cards = features.head(3)
    cols = st.columns(3)

    for idx, (_, row) in enumerate(cards.iterrows(), start=1):
        color = CATEGORY_COLORS.get(row["category"], CATEGORY_COLORS["Other"])

        with cols[idx - 1]:
            st.markdown(
                f"""
                <div class="driver-card">
                    <div class="driver-rank">TOP DRIVER #{idx}</div>
                    <div class="driver-feature">{escape(row["display_feature"])}</div>
                    <div class="driver-meta">
                        <span style="color:{color};">{escape(row["category"])}</span>
                        <span>{escape(row["importance_label"])}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_interpretation(features: pd.DataFrame) -> None:
    top_category = features["category"].value_counts().index[0] if not features.empty else "Route"

    st.markdown(
        f"""
        <div class="interpretation-card">
            <h4>AI Interpretation Summary</h4>
            <div class="interpretation-row">
                <span>①</span>
                <span><strong>{escape(top_category)} factors</strong> were the strongest contributors in this SHAP checkpoint.</span>
            </div>
            <div class="interpretation-row">
                <span>②</span>
                <span>Higher importance means the AI used that signal more strongly when assigning delay-risk predictions.</span>
            </div>
            <div class="interpretation-row">
                <span>③</span>
                <span>SHAP explains model behavior. It supports interpretation but does not prove direct causation.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feature_table(features: pd.DataFrame) -> None:
    table = features.copy()
    table["Operational Meaning"] = table["category"].map(
        {
            "Route": "Route or corridor pattern influenced the prediction.",
            "Service": "Transport mode or service type influenced the prediction.",
            "Time": "Time/date pattern influenced the prediction.",
            "Weather": "Weather condition influenced the prediction.",
            "Direction": "Travel direction influenced the prediction.",
            "Other": "Grouped model feature influenced the prediction.",
        }
    )

    display = table.rename(
        columns={
            "display_feature": "Feature",
            "category": "Driver Type",
            "importance": "Importance",
            "source": "Model Source",
        }
    )

    columns = ["Feature", "Driver Type", "Importance", "Operational Meaning"]
    if "Model Source" in display.columns:
        columns.append("Model Source")

    st.dataframe(display[columns], use_container_width=True, hide_index=True)


def render_shap_page(features: pd.DataFrame) -> None:
    inject_shap_css()
    st.subheader("Top Factors Influencing AI Delay Prediction")

    if features.empty:
        st.warning("AI explainability summary is unavailable.")
        return

    prepared = prepare_features(features)

    render_top_driver_cards(prepared)
    st.write("")

    left, right = st.columns([2.2, 1])
    with left:
        st.altair_chart(shap_driver_chart(prepared), use_container_width=True)
    with right:
        render_interpretation(prepared)

    st.subheader("Feature Importance Details")
    render_feature_table(prepared)
