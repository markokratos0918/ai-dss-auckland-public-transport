from __future__ import annotations

import pandas as pd


def classify_feature(feature: str) -> str:
    feature_l = str(feature).lower()

    if "route" in feature_l or "low-frequency" in feature_l:
        return "Route"
    if "service" in feature_l or "train" in feature_l or "rail" in feature_l:
        return "Service"
    if "hour" in feature_l or "weekday" in feature_l or "day" in feature_l or "month" in feature_l:
        return "Time"
    if any(term in feature_l for term in ["rain", "wind", "temperature", "humidity", "weather"]):
        return "Weather"
    if "direction" in feature_l:
        return "Direction"

    return "Other"


def clean_feature_label(feature: str) -> str:
    label = str(feature)
    replacements = {
        "trip_hour": "Time of day",
        "weekday": "Day of week",
        "day of month": "Date pattern",
        "direction_id_0": "Direction of travel",
        "direction_id 0": "Direction of travel",
        "route_id_": "Route ",
        "route id ": "Route ",
        "service_type_": "Service type: ",
    }

    for old, new in replacements.items():
        label = label.replace(old, new)

    return label.replace("_", " ").strip()


def prepare_features(features: pd.DataFrame) -> pd.DataFrame:
    df = features.copy()

    if "importance" not in df.columns:
        df["importance"] = 0

    df["importance"] = pd.to_numeric(df["importance"], errors="coerce").fillna(0)
    df["display_feature"] = df["feature"].apply(clean_feature_label)
    df["category"] = df["display_feature"].apply(classify_feature)
    df["importance_label"] = df["importance"].map(lambda value: f"{value:.3f}")

    return df.sort_values("importance", ascending=False)
