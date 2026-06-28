"""Explainability helpers for the AI-DSS modeling checkpoint."""

import numpy as np

from ai_dss_modeling.config import FEATURES, MAX_SHAP_ROWS, RANDOM_STATE
from ai_dss_modeling.models import feature_names

try:
    import shap
except Exception:  # pragma: no cover - optional runtime dependency
    shap = None


def xgb_importance(model, output_rows: list[dict], source: str) -> None:
    names = feature_names(model.named_steps["preprocess"])
    importances = getattr(model.named_steps["model"], "feature_importances_", np.array([]))
    for name, importance in zip(names, importances):
        output_rows.append(
            {
                "source": source,
                "explainability_type": "xgboost_feature_importance",
                "feature": name,
                "importance": float(importance),
                "notes": "Model-native feature importance from the fitted XGBoost model.",
            }
        )


def shap_importance(model, test_df, output_rows: list[dict]) -> str:
    if shap is None:
        return "SHAP was not run because the shap package was unavailable."

    sample = test_df[FEATURES].sample(n=min(MAX_SHAP_ROWS, len(test_df)), random_state=RANDOM_STATE)
    transformed = model.named_steps["preprocess"].transform(sample)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    names = feature_names(model.named_steps["preprocess"])

    try:
        explainer = shap.TreeExplainer(model.named_steps["model"])
        values = np.array(explainer.shap_values(transformed))
        if values.ndim == 3:
            values = values[:, :, -1]
        mean_abs = np.abs(values).mean(axis=0)
        for name, value in zip(names, mean_abs):
            output_rows.append(
                {
                    "source": "XGBoost classifier",
                    "explainability_type": "mean_abs_shap",
                    "feature": name,
                    "importance": float(value),
                    "notes": f"Mean absolute SHAP value on {len(sample):,} test rows.",
                }
            )
        return f"SHAP completed on {len(sample):,} sampled test rows."
    except Exception as error:
        return f"SHAP was attempted but did not complete: {error}"



def shap_beeswarm_sample(model, test_df, top_n: int = 10, max_rows: int = 400,
                         exclude: tuple = ("route_id_infrequent_sklearn",),
                         features_subset=None):
    """Persist per-row SHAP values for the top features (for a beeswarm plot).

    Uses XGBoost native TreeSHAP (pred_contribs) for version stability.
    Returns long rows: feature, shap_value, value_norm, mean_abs, row_id.
    """
    import pandas as pd
    import xgboost as xgb

    sample = test_df[FEATURES].sample(n=min(MAX_SHAP_ROWS, len(test_df)), random_state=RANDOM_STATE)
    transformed = model.named_steps["preprocess"].transform(sample)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    transformed = np.asarray(transformed, dtype=float)
    names = feature_names(model.named_steps["preprocess"])

    booster = model.named_steps["model"].get_booster()
    contribs = np.asarray(booster.predict(xgb.DMatrix(transformed), pred_contribs=True))
    values = contribs[:, :-1]  # drop bias column

    mean_abs = np.abs(values).mean(axis=0)
    if features_subset is not None:
        wanted = set(features_subset)
        order = [i for i in np.argsort(mean_abs)[::-1] if names[i] in wanted]
    else:
        order = [i for i in np.argsort(mean_abs)[::-1] if names[i] not in exclude][:top_n]

    n_rows = min(max_rows, transformed.shape[0])
    rng = np.random.default_rng(RANDOM_STATE)
    row_idx = rng.choice(transformed.shape[0], size=n_rows, replace=False)

    records = []
    for j in order:
        col = transformed[row_idx, j]
        vmin = float(col.min())
        span = (float(col.max()) - vmin) or 1.0
        for r, ridx in enumerate(row_idx):
            records.append(
                {
                    "feature": names[j],
                    "shap_value": float(values[ridx, j]),
                    "value_norm": (float(transformed[ridx, j]) - vmin) / span,
                    "mean_abs": float(mean_abs[j]),
                    "row_id": int(r),
                }
            )
    return pd.DataFrame.from_records(records)
