from html import escape

import pydeck as pdk
import streamlit as st

from services.route_focus_data import route_focus
from services.route_map_data import route_shape_path
from utils.formatters import format_delay, format_weather

MAP_VIEW = {
    "latitude": -36.866,
    "longitude": 174.77,
    "zoom": 10.45,
    "pitch": 0,
    "bearing": 0,
}


def _readable_corridor(value) -> str:
    corridor = str(value or "Unavailable")
    return corridor.split(" - ", 1)[1] if " - " in corridor else corridor


def _route_context(route_id: str, service_type: str, include_special: bool, day: str, hour: str) -> dict[str, str]:
    route = route_focus(route_id, service_type, include_special, day, hour)
    if route.empty:
        return {
            "corridor": "Unavailable",
            "service": "Unavailable",
            "observed_delay": "Unavailable",
            "predicted_delay": "Unavailable",
            "recommended_action": "Unavailable",
            "rain": "Unavailable",
            "wind": "Unavailable",
            "precipitation": "Unavailable",
        }
    row = route.iloc[0]
    corridor = _readable_corridor(row.get("corridor_name", "Unavailable"))
    if len(corridor) > 62:
        corridor = f"{corridor[:59]}..."
    return {
        "corridor": corridor,
        "service": str(row.get("service_type", "Unavailable")),
        "observed_delay": format_delay(row.get("avg_observed_delay")),
        "predicted_delay": format_delay(row.get("avg_predicted_delay")),
        "recommended_action": str(row.get("recommended_action", "Unavailable")),
        "rain": format_weather(row.get("avg_rain_pct"), "%", 1),
        "wind": format_weather(row.get("max_wind_speed"), " km/h", 1),
        "precipitation": format_weather(row.get("avg_precipitation"), " mm", 2),
    }


def _overview_route_map(route_id: str) -> None:
    route_path = route_shape_path(route_id)
    if route_path.empty:
        st.caption("Scheduled GTFS route shape is unavailable for this route.")
        return
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
                latitude=MAP_VIEW["latitude"],
                longitude=MAP_VIEW["longitude"],
                zoom=MAP_VIEW["zoom"],
                pitch=MAP_VIEW["pitch"],
                bearing=MAP_VIEW["bearing"],
            ),
            tooltip={"text": "Route {route_id}"},
            map_style="mapbox://styles/mapbox/dark-v10",
        ),
        use_container_width=True,
        height=265,
    )


def render_decision_story(
    observed: dict[str, str],
    ai: dict[str, str],
    action: dict[str, str],
    service_type: str,
    include_special: bool,
    analysis_day: str,
    analysis_hour: str,
) -> None:
    risk_route = ai.get("route_id", "Unavailable")
    route_context = _route_context(risk_route, service_type, include_special, analysis_day, analysis_hour)
    route_action = escape(route_context.get("recommended_action") or action.get("common", "Unavailable"))

    left, middle, right = st.columns(3)
    with left:
        with st.container(border=True, height=300):
            st.subheader("Where is the risk?")
            st.html(_risk_route_html(risk_route, route_context))

    with middle:
        with st.container(border=True, height=300):
            _overview_route_map(str(risk_route))
    with right:
        with st.container(border=True, height=300):
            st.subheader("What action is recommended?")
            st.html(_action_html(route_action, risk_route, route_context))


def _risk_route_html(route_id: str, context: dict[str, str]) -> str:
    return f"""<div class="risk-route-story">
    <div class="risk-route-top">
        <div>
            <div class="decision-story-small-label">Top Risk Route</div>
            <div class="risk-route-id">{escape(route_id)}</div>
        </div>
        <div>
            <div class="decision-story-small-label">Avg Predicted Delay</div>
            <div class="risk-route-delay">{escape(context["predicted_delay"])}</div>
        </div>
    </div>
    <div>
        <div class="decision-route-detail-label">Risk Route Corridor</div>
        <div class="decision-route-detail-value">{escape(context["corridor"])}</div>
        <div class="decision-route-detail-service">Service: {escape(context["service"])}</div>
    </div>
</div>"""


def _action_html(route_action: str, route_id: str, context: dict[str, str]) -> str:
    return f"""<div class="decision-story-caption">Recommendation for the current risk route.</div>
<div class="route-action-panel">
    <div class="decision-story-action-value">{route_action}</div>
</div>
<div class="route-context-strip">
    <div class="route-context-cell">
        <div class="route-context-label">Avg Rain</div>
        <div class="route-context-value">{escape(context["rain"])}</div>
    </div>
    <div class="route-context-cell">
        <div class="route-context-label">Max Wind</div>
        <div class="route-context-value">{escape(context["wind"])}</div>
    </div>
    <div class="route-context-cell">
        <div class="route-context-label">Avg Precipitation</div>
        <div class="route-context-value">{escape(context["precipitation"])}</div>
    </div>
</div>"""
