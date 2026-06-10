"""Output writing and manifest helpers for the AI-DSS modeling checkpoint."""

import numpy as np
import pandas as pd

from ai_dss_modeling.config import (
    CATEGORICAL_FEATURES,
    FEATURES,
    IMPORTANCE_CSV,
    INPUT_CSV,
    MANIFEST_MD,
    METRICS_CSV,
    NUMERIC_FEATURES,
    PREDICTION_SAMPLE_CSV,
    PREDICTION_SAMPLE_ROWS,
)
from ai_dss_modeling.data import rel


def md_table(headers, rows) -> str:
    divider = ["---" for _ in headers]
    lines = [headers, divider, *rows]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in lines)


def write_prediction_sample(test_df, classification_pred, classification_prob, regression_pred) -> None:
    base_columns = [
        "collection_time_utc",
        "collection_date",
        "route_id",
        "route_short_name",
        "delay_minutes",
        "delay_risk",
        "recommended_action",
    ]
    sample_columns = base_columns + [column for column in FEATURES if column not in base_columns]
    sample = test_df[sample_columns].copy()
    sample["actual_actionable_delay_risk"] = test_df["actionable_delay_risk"].to_numpy()
    sample["predicted_actionable_delay_risk"] = classification_pred
    sample["predicted_actionable_probability"] = classification_prob.round(6)
    sample["predicted_delay_minutes"] = np.round(regression_pred, 6)
    sample.sort_values("collection_time_utc").head(PREDICTION_SAMPLE_ROWS).to_csv(PREDICTION_SAMPLE_CSV, index=False)


def write_importance(importance_rows: list[dict]) -> None:
    columns = ["source", "explainability_type", "feature", "importance", "notes"]
    importance = pd.DataFrame(importance_rows, columns=columns)
    if not importance.empty:
        importance = importance.sort_values(["source", "explainability_type", "importance"], ascending=[True, True, False])
    importance.to_csv(IMPORTANCE_CSV, index=False)


def top_rows(rows: list[dict], source: str, explainability_type: str, limit: int = 10) -> list[dict]:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return []
    subset = frame[(frame["source"] == source) & (frame["explainability_type"] == explainability_type)].copy()
    if subset.empty:
        return []
    return subset.sort_values("importance", ascending=False).head(limit).to_dict("records")


def build_manifest(
    full_rows: int,
    model_rows: int,
    train_rows: int,
    test_rows: int,
    train_dates: list[str],
    test_dates: list[str],
    metrics: pd.DataFrame,
    importance_rows: list[dict],
    arima_note: str,
    shap_note: str,
) -> str:
    selected = metrics[
        metrics["metric"].isin(["accuracy", "precision", "recall", "f1", "macro_f1", "mae", "mse", "rmse", "r2"])
    ]
    metric_rows = [[r.model, r.target_type, r.target, r.metric, r.value] for r in selected.itertuples(index=False)]

    feature_rows = [
        [r["source"], r["explainability_type"], r["feature"], round(r["importance"], 6)]
        for r in top_rows(importance_rows, "XGBoost classifier", "mean_abs_shap")
    ]
    if not feature_rows:
        feature_rows = [
            [r["source"], r["explainability_type"], r["feature"], round(r["importance"], 6)]
            for r in top_rows(importance_rows, "XGBoost classifier", "xgboost_feature_importance")
        ]

    return f"""# AI-DSS Modeling Manifest

Last reviewed: 2026-06-10

## Scope

This manifest records the real Auckland AI-DSS modeling checkpoint for the capstone project. It uses the official current Notebook 09 model-baseline output as the prepared feature table, then writes small evidence files that are safe to review and commit.

This is an AI-layer checkpoint only. It does not modify Notebook 09, the Decision Engine, SUMO, or Streamlit.

## Assessment 1 Alignment

- Structured ML prediction: XGBoost classifier and XGBoost regressor.
- Baseline comparison: most-frequent classification baseline, median regression baseline, and ARIMA hourly delay baseline.
- Explainability: SHAP mean absolute values when feasible, plus XGBoost feature importance.
- Metrics: accuracy, precision, recall, F1, macro F1, MAE, MSE, RMSE, and R2.
- Downstream connection: the primary classification target predicts whether a record is actionable for the Decision Engine.

## Input

Required local input:

- `{rel(INPUT_CSV)}`

This input is a large local generated output and should not be committed to GitHub.

Rows in local input: {full_rows:,}
Rows used in compact modeling checkpoint: {model_rows:,}

## Target Choice

Primary target:

- `actionable_delay_risk`: 1 when `delay_risk` is Medium, High, or Severe; 0 when Low.

This is more defensible than using four risk classes as the main target because High and Severe remain rare in the current model-baseline dataset. It also connects directly to downstream decision recommendations.

Secondary targets:

- `delay_minutes` row-level regression.
- `hourly_avg_delay_minutes` ARIMA baseline.

## Features

Categorical features:

- {", ".join(CATEGORICAL_FEATURES)}

Numeric features:

- {", ".join(NUMERIC_FEATURES)}

Excluded leakage fields:

- `delay_minutes` is excluded from classification features.
- `delay_risk` and `recommended_action` are excluded from all model features.
- `trip_id` and raw identifiers that do not support general decision rules are excluded.

Special-route records are included by default. They are preserved through `is_special_route` and related route fields so their effect can be reviewed, but the model should not overclaim performance for special services.

## Split

The checkpoint uses a time-based split rather than a random split.

- Train rows: {train_rows:,}
- Test rows: {test_rows:,}
- Train dates: {train_dates[0]} to {train_dates[-1]}
- Test dates: {test_dates[0]} to {test_dates[-1]}

## Results

{md_table(["Model", "Target type", "Target", "Metric", "Value"], metric_rows)}

## Explainability

{shap_note}

Top explainability rows:

{md_table(["Source", "Type", "Feature", "Importance"], feature_rows)}

Full explainability table:

- `{rel(IMPORTANCE_CSV)}`

## ARIMA Baseline

{arima_note}

ARIMA is used only as a time-series baseline on hourly average delay. It is not the main row-level prediction model.

## Outputs

- `{rel(METRICS_CSV)}`
- `{rel(IMPORTANCE_CSV)}`
- `{rel(PREDICTION_SAMPLE_CSV)}`
- `{rel(MANIFEST_MD)}`

## Reproduction Command

```bash
python src/train_ai_dss_model.py
```

No-write manual test command:

```bash
python src/train_ai_dss_model.py --dry-run
```

If plain `python` is not on PATH in the local shell, use the project conda Python configured for the capstone environment.

## GitHub Guidance

Safe to commit after review:

- `src/train_ai_dss_model.py`
- `src/ai_dss_modeling/`
- `docs/ai_modeling_manifest.md`
- `data/processed/summaries/ai_model_metrics.csv`
- `data/processed/summaries/ai_feature_importance.csv`
- `data/processed/summaries/ai_prediction_sample.csv`

Do not commit:

- `{rel(INPUT_CSV)}`
- `data/processed/gtfs_realtime_cleaned.parquet`
- raw GTFS-Realtime daily CSV files
- large model artifacts or cache folders

## Manual Audit Guide

1. Confirm `{rel(METRICS_CSV)}` contains baseline, XGBoost classifier, XGBoost regressor, and ARIMA rows.
2. Confirm the split above trains on earlier dates and tests on later dates.
3. Confirm the baseline classifier has zero actionable-risk recall, while XGBoost has non-zero recall and F1.
4. Confirm XGBoost regression RMSE is lower than median baseline RMSE.
5. Confirm `{rel(IMPORTANCE_CSV)}` contains SHAP or feature-importance rows.
6. Confirm `{rel(PREDICTION_SAMPLE_CSV)}` contains actual and predicted values.
7. Confirm `delay_minutes`, `delay_risk`, and `recommended_action` are not used as model input features.

## Limitations

- The model-baseline folder is the official current AI input. Older duplicate root-level decision outputs should not be used.
- The model predicts risk from observed route, time, and weather patterns. It should not be described as a deployment-ready live predictor.
- High and Severe classes are rare, so the main classification target is binary actionable risk.
- Weather was included and validated, but route and temporal features may be stronger predictors in the current dataset. Do not overclaim weather impact.
- Ferry records are a small part of the model-baseline data, so avoid strong ferry-weather conclusions.
- SHAP is sampled to keep the checkpoint reproducible and lightweight.
- Model outputs support Decision Engine prioritisation evidence; they do not automate transport operations.
"""
