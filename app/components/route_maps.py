from __future__ import annotations

import pydeck as pdk
import streamlit as st

from services.route_map_data import route_shape_path


DEFAULT_MAP_VIEW = {
    "latitude": -36.866,
    "longitude": 174.77,
    "zoom": 10.45,
}


def scheduled_route_map(route_id: str, height: int = 320, zoom: float = 10.0) -> None:
    route_path = route_shape_path(route_id)
    if route_path.empty:
        st.info("Scheduled GTFS route shape is unavailable for this selected route.")
        return

    # Validate required columns for map centering
    has_coords = "latitude" in route_path.columns and "longitude" in route_path.columns
    if not has_coords:
        st.warning("Route coordinates are unavailable. Showing Auckland region map.")
        latitude, longitude = DEFAULT_MAP_VIEW["latitude"], DEFAULT_MAP_VIEW["longitude"]
    else:
        try:
            map_row = route_path.iloc[0]
            latitude = float(map_row["latitude"])
            longitude = float(map_row["longitude"])
        except (ValueError, KeyError, TypeError):
            st.warning("Route coordinates are invalid. Showing Auckland region map.")
            latitude, longitude = DEFAULT_MAP_VIEW["latitude"], DEFAULT_MAP_VIEW["longitude"]

    layer = pdk.Layer(
        "PathLayer",
        route_path,
        get_path="path",
        get_color=[20, 184, 232],
        width_scale=18,
        width_min_pixels=4,
        pickable=True,
    )
    view_state = pdk.ViewState(
        latitude=latitude,
        longitude=longitude,
        zoom=zoom,
        pitch=0,
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "Route {route_id}\nGTFS shape {shape_id}"},
            map_style="mapbox://styles/mapbox/dark-v10",
        ),
        use_container_width=True,
        height=height,
    )
