from __future__ import annotations

from html import escape

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from components.shap_explainability_data import (
    classify_feature,
    clean_feature_label,
    group_by_category,
    prepare_features,
)
from components.shap_explainability_styles import CATEGORY_COLORS, inject_shap_css
from components.page_summary import set_summary


__all__ = [
    "classify_feature",
    "clean_feature_label",
    "group_by_category",
    "prepare_features",
    "inject_shap_css",
    "shap_category_chart",
    "shap_beeswarm_chart",
    "render_interpretation",
    "render_feature_table",
    "render_shap_page",
]


def shap_category_chart(category_df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(category_df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("share_pct:Q", title="Share of total SHAP importance (%)"),
            y=alt.Y("category:N", sort="-x", title=None, axis=alt.Axis(labelLimit=160)),
            color=alt.Color(
                "category:N",
                scale=alt.Scale(domain=list(CATEGORY_COLORS), range=list(CATEGORY_COLORS.values())),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("category:N", title="Driver type"),
                alt.Tooltip("share_pct:Q", title="Share (%)", format=".1f"),
                alt.Tooltip("feature_count:Q", title="# features", format=","),
                alt.Tooltip("importance:Q", title="Summed importance", format=".2f"),
            ],
        )
        .properties(height=220)
    )


def shap_beeswarm_chart(beeswarm: pd.DataFrame) -> alt.Chart:
    df = beeswarm.copy()
    for col in ("shap_value", "value_norm", "mean_abs"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["shap_value", "value_norm"])
    df["value_norm"] = df["value_norm"].clip(0, 1)
    df["display_feature"] = df["feature"].apply(clean_feature_label)
    order = (
        df.groupby("display_feature")["mean_abs"].first().sort_values(ascending=False).index.tolist()
    )
    df["jitter"] = np.random.default_rng(7).uniform(-0.42, 0.42, len(df))

    zero = (
        alt.Chart(pd.DataFrame({"x": [0]}))
        .mark_rule(color="#5d7da0", strokeDash=[3, 3])
        .encode(x="x:Q")
    )
    points = alt.Chart(df).mark_circle(size=26, opacity=0.6).encode(
        x=alt.X("shap_value:Q", title="SHAP value  (← lowers risk    ·    raises risk →)"),
        y=alt.Y("display_feature:N", sort=order, title=None, axis=alt.Axis(labelLimit=200)),
        yOffset=alt.YOffset("jitter:Q", scale=alt.Scale(domain=[-0.5, 0.5])),
        color=alt.Color(
            "value_norm:Q",
            scale=alt.Scale(range=["#3b82f6", "#ef4444"]),
            legend=alt.Legend(title="Feature value", orient="right", gradientLength=120, format=".0%"),
        ),
        tooltip=[
            alt.Tooltip("display_feature:N", title="Feature"),
            alt.Tooltip("shap_value:Q", title="SHAP value", format=".3f"),
            alt.Tooltip("value_norm:Q", title="Feature value (norm)", format=".2f"),
        ],
    )
    return (zero + points).properties(height=340).configure_view(stroke=None)


def render_interpretation(category_df: pd.DataFrame) -> None:
    top_category = category_df.iloc[0]["category"] if not category_df.empty else "Route"
    top_share = float(category_df.iloc[0]["share_pct"]) if not category_df.empty else 0.0
    st.markdown(
        f"""
        <div class="interpretation-card">
            <h4>AI Interpretation Summary</h4>
            <div class="interpretation-row">
                <span>①</span>
                <span><strong>{escape(top_category)} factors</strong> carry the most SHAP importance
                (~{top_share:.0f}% of the total), though spread across many individual features.</span>
            </div>
            <div class="interpretation-row">
                <span>②</span>
                <span>In the beeswarm, each dot is one trip; colour is the feature's value (low → high)
                and position is how that value pushed the AI's risk up or down.</span>
            </div>
            <div class="interpretation-row">
                <span>③</span>
                <span>SHAP explains model behaviour, not proof of causation.</span>
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


def render_shap_page(features: pd.DataFrame, beeswarm: pd.DataFrame | None = None) -> None:
    inject_shap_css()
    st.subheader("What Types of Signals Drive AI Predictions")

    if features.empty:
        st.warning("AI explainability summary is unavailable.")
        return

    prepared = prepare_features(features)
    category_df = group_by_category(prepared)
    if not category_df.empty:
        _top = category_df.iloc[0]
        set_summary("SHAP Explainability", [
            f"Top driver type: {_top['category']} (~{_top['share_pct']:.0f}% of importance)",
            "Spread across hundreds of route features",
            "Weather contributes only a small share",
        ])
    individual = prepared[
        ~prepared["display_feature"].str.contains("low-frequency|grouped", case=False, na=False)
    ]

    st.altair_chart(shap_category_chart(category_df), use_container_width=True)
    st.caption(
        "Grouped SHAP importance by driver type across all model features. Route patterns carry the "
        "most importance but are spread thinly across hundreds of one-hot route features; time, "
        "service, weather and direction are each concentrated in only a few features."
    )

    st.subheader("How Context Features Move Each Prediction")
    if beeswarm is None or beeswarm.empty:
        st.warning("Per-row SHAP beeswarm sample is unavailable.")
    else:
        left, right = st.columns([2.4, 1])
        with left:
            st.altair_chart(shap_beeswarm_chart(beeswarm), use_container_width=True)
        with right:
            render_interpretation(category_df)
        st.caption(
            "Beeswarm of the continuous context features (one dot per sampled trip). Red = high "
            "feature value, blue = low; left of the dashed line lowers predicted risk, right raises "
            "it. SHAP from XGBoost TreeSHAP on a 1,000-row test sample. Route/categorical drivers are "
            "summarised in the grouped chart above."
        )

    with st.expander("Feature importance details (individual features)"):
        render_feature_table(individual.head(25))
