import streamlit as st


st.set_page_config(
    page_title="AI-Driven Transport Decision Support",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.html(
    """<style>
@media (min-width: 1200px) {
    .block-container {
        max-width: 96vw;
        padding-top: 2.6rem;
        padding-left: 1.4rem;
        padding-right: 1.4rem;
        padding-bottom: 1.2rem;
    }

    h1 {
        font-size: 2.1rem;
        line-height: 1.15;
    }

    h2, h3 {
        font-size: 1.45rem;
        line-height: 1.2;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0.75rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0.75rem;
    }
}
</style>"""
)

pages = [
    st.Page("pages/01_Overview.py", title="Overview", url_path="overview"),
    st.Page("pages/02_Delay_Risk_Monitor.py", title="Delay Risk Monitor", url_path="delay-risk-monitor"),
    st.Page("pages/03_AI_Prediction_Results.py", title="AI Prediction Results", url_path="ai-prediction-results"),
    st.Page("pages/04_Weather_Impact.py", title="Weather Impact", url_path="weather-impact"),
    st.Page("pages/05_SHAP_Explainability.py", title="SHAP Explainability", url_path="shap-explainability"),
    st.Page("pages/06_Decision_Engine.py", title="Decision Engine", url_path="decision-engine"),
    st.Page("pages/07_SUMO_Validation.py", title="SUMO Validation", url_path="sumo-validation"),
    st.Page("pages/08_Route_Corridor_Focus.py", title="Route / Corridor Focus", url_path="route-corridor-focus"),
]

navigation = st.navigation(pages)
navigation.run()
