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

