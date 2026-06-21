from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from services.operator_constants import PROJECT_ROOT


GTFS_STATIC_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs_static"
TRIPS_PATH = GTFS_STATIC_DIR / "trips.txt"
SHAPES_PATH = GTFS_STATIC_DIR / "shapes.txt"


@st.cache_data(show_spinner=False)
def _route_shape_ids() -> pd.DataFrame:
    if not TRIPS_PATH.exists():
        return pd.DataFrame(columns=["route_id", "shape_id", "trip_count"])
    trips = pd.read_csv(TRIPS_PATH, usecols=["route_id", "shape_id"], dtype=str)
    trips = trips.dropna(subset=["route_id", "shape_id"])
    return trips.groupby(["route_id", "shape_id"], as_index=False).size().rename(columns={"size": "trip_count"})


@st.cache_data(show_spinner=False)
def _shape_points(shape_id: str, path_text: str) -> pd.DataFrame:
    path = Path(path_text)
    if not path.exists():
        return pd.DataFrame()
    points = pd.read_csv(
        path,
        usecols=["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
        dtype={"shape_id": str},
    )
    points = points[points["shape_id"] == shape_id].copy()
    if points.empty:
        return points
    points["shape_pt_sequence"] = pd.to_numeric(points["shape_pt_sequence"], errors="coerce")
    return points.sort_values("shape_pt_sequence")


def route_shape_path(route_id: str) -> pd.DataFrame:
    shape_ids = _route_shape_ids()
    if shape_ids.empty:
        return pd.DataFrame()
    matches = shape_ids[shape_ids["route_id"].astype(str) == str(route_id)]
    if matches.empty:
        return pd.DataFrame()
    shape_id = matches.sort_values("trip_count", ascending=False).iloc[0]["shape_id"]
    points = _shape_points(str(shape_id), str(SHAPES_PATH))
    if points.empty:
        return pd.DataFrame()
    path = points[["shape_pt_lon", "shape_pt_lat"]].values.tolist()
    return pd.DataFrame(
        {
            "route_id": [route_id],
            "shape_id": [shape_id],
            "path": [path],
            "latitude": [points["shape_pt_lat"].mean()],
            "longitude": [points["shape_pt_lon"].mean()],
        }
    )
