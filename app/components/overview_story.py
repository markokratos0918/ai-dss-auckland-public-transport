from html import escape

import pydeck as pdk
import streamlit as st

from services.route_focus_data import route_focus
from services.route_map_data import route_shape_path


def _format_route_delay(value) -> str:
    try:
        return f"{float(value):.2f} min"
    except (TypeError, ValueError):
        return "Unavailable"


def _route_context(route_id: str, service_type: str, include_special: bool, day: str, hour: str) -> dict[str, str]:
    route = route_focus(route_id, service_type, include_special, day, hour)
    if route.empty:
        return {
            "corridor": "Unavailable",
            "service": "Unavailable",
            "observed_delay": "Unavailable",
            "predicted_delay": "Unavailable",
        }
    row = route.iloc[0]
    corridor = str(row.get("corridor_name", "Unavailable"))
    if len(corridor) > 62:
        corridor = f"{corridor[:59]}..."
    return {
        "corridor": corridor,
        "service": str(row.get("service_type", "Unavailable")),
        "observed_delay": _format_route_delay(row.get("avg_observed_delay")),
        "predicted_delay": _format_route_delay(row.get("avg_predicted_delay")),
    }


def _overview_route_map(route_id: str) -> None:
    route_path = route_shape_path(route_id)
    if route_path.empty:
        st.caption("Scheduled GTFS route shape is unavailable for this route.")
        return
    row = route_path.iloc[0]
    layer = pdk.Layer(
        "PathLayer",
        route_path,
        get_path="path",
        get_color=[44, 189, 255],
        width_scale=14,
        width_min_pixels=3,
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=pdk.ViewState(
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                zoom=10,
                pitch=0,
            ),
            tooltip={"text": "Route {route_id}"},
            map_style="mapbox://styles/mapbox/dark-v10",
        ),
        use_container_width=True,
        height=265,
    )


def _story_style() -> None:
    st.html(
        """<style>
.decision-story-small-label { color:#ffffff; font-weight:800; font-size:0.92rem; }
.decision-story-big-value { color:#ffffff; font-size:1.75rem; line-height:1.15; margin-bottom:0.5rem; }
.decision-story-caption { color:rgba(255,255,255,0.64); font-weight:700; margin:0.25rem 0 0.9rem 0; }
div[data-testid="stButton"] { margin:-0.12rem 0 0.72rem; }
div[data-testid="stButton"] > button {
    border-radius:999px; padding:0.2rem 0.85rem 0.28rem; min-height:0;
    font-size:1.32rem; line-height:1.1; font-weight:900;
}
.decision-route-detail-panel { display:grid; gap:1rem; margin-top:0.15rem; }
.decision-route-detail-label {
    color:rgba(255,255,255,0.62); font-size:0.72rem; font-weight:850; text-transform:uppercase;
}
.decision-route-detail-value { color:#ffffff; font-size:0.94rem; font-weight:900; line-height:1.25; margin-top:0.18rem; }
.decision-route-detail-service { color:#dbeafe; font-size:0.82rem; font-weight:850; margin-top:0.26rem; }
.decision-action-evidence {
    display:grid; grid-template-columns:1fr 1fr; gap:0.7rem; margin-top:0.75rem;
}
.decision-action-evidence-card {
    border:1px solid rgba(93,125,160,0.55); border-radius:0.45rem;
    background:rgba(13,38,65,0.62); padding:0.65rem 0.75rem;
}
.decision-action-evidence-title {
    color:rgba(255,255,255,0.7); font-size:0.75rem; font-weight:850;
    text-transform:uppercase; margin-bottom:0.32rem;
}
.decision-action-evidence-route { color:#ffffff; font-size:1.15rem; font-weight:900; margin-bottom:0.45rem; }
.decision-action-evidence-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.55rem; }
.decision-action-evidence-label { color:rgba(255,255,255,0.66); font-size:0.72rem; font-weight:800; }
.decision-action-evidence-value { color:#ffffff; font-size:1.04rem; font-weight:900; line-height:1.15; }
</style>"""
    )


def _route_button(label: str, key: str, selected: str) -> bool:
    return st.button(label, key=key, type="primary" if selected == label else "secondary")


def render_decision_story(
    observed: dict[str, str],
    ai: dict[str, str],
    action: dict[str, str],
    service_type: str,
    include_special: bool,
    analysis_day: str,
    analysis_hour: str,
) -> None:
    observed_route = observed.get("Top Observed Delayed Route", "Unavailable")
    ai_route = ai.get("route_id", "Unavailable")
    primary_action = escape(action.get("common", "Unavailable"))
    observed_context = _route_context(observed_route, service_type, include_special, analysis_day, analysis_hour)
    ai_context = _route_context(ai_route, service_type, include_special, analysis_day, analysis_hour)

    _story_style()
    route_options = [observed_route, ai_route]
    if st.session_state.get("overview_risk_route_map_choice") not in route_options:
        st.session_state["overview_risk_route_map_choice"] = ai_route

    left, middle, right = st.columns(3)
    with left:
        with st.container(border=True, height=300):
            st.subheader("Where is the risk?")
            st.html('<div class="decision-story-caption">Observed evidence and AI attention can point to different routes.</div>')
            selector_col, detail_col = st.columns([0.72, 1.28])
            with selector_col:
                st.html('<div class="decision-story-small-label">Top Observed Delayed Route</div>')
                if _route_button(observed_route, "overview_observed_route_pill", st.session_state["overview_risk_route_map_choice"]):
                    st.session_state["overview_risk_route_map_choice"] = observed_route
                st.html('<div class="decision-story-small-label">Top AI-Risk Route</div>')
                if _route_button(ai_route, "overview_ai_route_pill", st.session_state["overview_risk_route_map_choice"]):
                    st.session_state["overview_risk_route_map_choice"] = ai_route
            with detail_col:
                st.html(_route_detail_html(observed_context, ai_context))

    with middle:
        with st.container(border=True, height=300):
            _overview_route_map(str(st.session_state["overview_risk_route_map_choice"] or ai_route))
    with right:
        with st.container(border=True, height=300):
            st.subheader("What action is recommended?")
            st.html(_action_evidence_html(primary_action, observed_route, ai_route, observed_context, ai_context))


def _route_detail_html(observed: dict[str, str], ai: dict[str, str]) -> str:
    return f"""<div class="decision-route-detail-panel">
    <div>
        <div class="decision-route-detail-label">Observed route corridor</div>
        <div class="decision-route-detail-value">{escape(observed["corridor"])}</div>
        <div class="decision-route-detail-service">Service: {escape(observed["service"])}</div>
    </div>
    <div>
        <div class="decision-route-detail-label">AI-risk route corridor</div>
        <div class="decision-route-detail-value">{escape(ai["corridor"])}</div>
        <div class="decision-route-detail-service">Service: {escape(ai["service"])}</div>
    </div>
</div>"""


def _action_evidence_html(primary_action: str, observed_route: str, ai_route: str, observed: dict[str, str], ai: dict[str, str]) -> str:
    return f"""<div class="decision-story-small-label">Primary AI Recommendation</div>
<div class="decision-story-big-value">{primary_action}</div>
<div class="decision-action-evidence">
    {_route_metric_card("Observed route", observed_route, observed)}
    {_route_metric_card("AI-risk route", ai_route, ai)}
</div>"""


def _route_metric_card(title: str, route_id: str, context: dict[str, str]) -> str:
    return f"""<div class="decision-action-evidence-card">
        <div class="decision-action-evidence-title">{title}</div>
        <div class="decision-action-evidence-route">{escape(route_id)}</div>
        <div class="decision-action-evidence-grid">
            <div><div class="decision-action-evidence-label">Observed delay</div>
            <div class="decision-action-evidence-value">{escape(context["observed_delay"])}</div></div>
            <div><div class="decision-action-evidence-label">Predicted delay</div>
            <div class="decision-action-evidence-value">{escape(context["predicted_delay"])}</div></div>
        </div>
    </div>"""
