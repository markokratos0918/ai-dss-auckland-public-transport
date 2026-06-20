from __future__ import annotations

import re

import pandas as pd

from services.operator_data import load_dataset, numeric


SHAP_LABELS = {
    "route_id_infrequent_sklearn": "Other low-frequency routes",
    "route_id_326-203": "Route 326-203",
    "route_id_NX1-203": "Route NX1-203",
    "route_id_738-221": "Route 738-221",
    "service_type_Train / Rail": "Service type: Train / Rail",
}


def sumo_summary() -> tuple[pd.DataFrame, dict[str, str]]:
    df = numeric(load_dataset("sumo_validation"), ["avg_delay_min", "max_delay_min", "congestion_index"])
    scenarios = load_dataset("sumo_scenarios")
    if df.empty:
        return df, {}
    values = {str(row["scenario_name"]): row for _, row in df.iterrows()}
    disruption = values.get("Disruption Scenario")
    intervention = values.get("Intervention Scenario")
    improvement = None
    if disruption is not None and intervention is not None and disruption["avg_delay_min"]:
        improvement = (disruption["avg_delay_min"] - intervention["avg_delay_min"]) / disruption["avg_delay_min"] * 100
    interpretation = " ".join(df.get("validation_interpretation", pd.Series(dtype=str)).dropna().astype(str))
    improvement_match = re.search(r"(\d+(?:\.\d+)?)\s*percent\s+lower", interpretation, flags=re.I)
    description = " ".join(scenarios.get("description", pd.Series(dtype=str)).dropna().astype(str))
    date_match = re.search(r"20\d{2}-\d{2}-\d{2}", description)
    selected = str(df["selected_route"].dropna().iloc[0]) if "selected_route" in df.columns else "Unavailable"
    improvement_text = "Unavailable"
    if improvement_match:
        improvement_text = f"{improvement_match.group(1)}%"
    elif improvement is not None:
        improvement_text = f"{improvement:.1f}%"
    return df, {
        "route_id": selected,
        "route_name": selected,
        "scenario_date": date_match.group(0) if date_match else "Documented in SUMO output",
        "improvement": improvement_text,
    }


def top_features(limit: int = 10) -> pd.DataFrame:
    df = numeric(load_dataset("feature_importance"), ["importance"])
    if df.empty:
        return df
    features = df.sort_values("importance", ascending=False).head(limit).copy()
    if "feature" in features.columns:
        features["feature"] = features["feature"].replace(SHAP_LABELS)
    return features
