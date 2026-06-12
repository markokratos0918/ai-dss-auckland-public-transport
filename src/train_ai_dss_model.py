"""Run the real Auckland AI-DSS modeling checkpoint.

Run from the project root:

    python src/train_ai_dss_model.py

Required local input:

    data/processed/parquet/decision_engine_model_baseline.parquet
    or fallback data/processed/outputs/model_baseline/decision_engine_output.csv

The preferred input is the final model-baseline Parquet output. The CSV remains
fallback/export evidence. Both are local generated outputs and should stay out
of GitHub.
"""

import argparse

import pandas as pd

from ai_dss_modeling.config import (
    AI_PREDICTIONS_MODEL_BASELINE_PARQUET,
    AI_PREDICTIONS_TEST_SET_PARQUET,
    IMPORTANCE_CSV,
    MANIFEST_MD,
    METRICS_CSV,
    PREDICTION_SAMPLE_CSV,
    SUMMARY_DIR,
)
from ai_dss_modeling.data import input_path, read_input, rel, sample_for_modeling, time_split
from ai_dss_modeling.explainability import shap_importance, xgb_importance
from ai_dss_modeling.metrics import add_metric
from ai_dss_modeling.models import arima_baseline, train_classification, train_regression
from ai_dss_modeling.reporting import build_manifest, write_importance, write_prediction_parquets, write_prediction_sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the real Auckland AI-DSS modeling checkpoint.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the full modeling/evaluation workflow without writing output files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.dry_run:
        SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
        MANIFEST_MD.parent.mkdir(parents=True, exist_ok=True)

    print("AI-DSS modeling checkpoint")
    if args.dry_run:
        print("Mode: dry run - no output files will be written")
    active_input, input_source = input_path()
    print(f"Input source: {input_source}")
    print(f"Input: {rel(active_input)}")

    full_df = read_input()
    print("Target distribution:")
    for risk, count in full_df["delay_risk"].value_counts().sort_index().items():
        print(f"- {risk}: {count:,}")
    special_count = int(full_df["is_special_route"].astype("string").str.lower().eq("true").sum())
    print(f"Special-route records included: {special_count:,}")

    model_df = sample_for_modeling(full_df)
    train_df, test_df, train_dates, test_dates = time_split(model_df)

    metrics: list[dict] = []
    add_metric(metrics, "Input", "data", "decision_engine_output", "full_rows", len(full_df))
    add_metric(metrics, "Input", "data", "modeling_sample", "rows", len(model_df))
    add_metric(metrics, "Split", "data", "time_based", "train_rows", len(train_df))
    add_metric(metrics, "Split", "data", "time_based", "test_rows", len(test_df))
    add_metric(metrics, "Target distribution", "classification", "actionable_delay_risk", "train_positive_share", train_df["actionable_delay_risk"].mean())
    add_metric(metrics, "Target distribution", "classification", "actionable_delay_risk", "test_positive_share", test_df["actionable_delay_risk"].mean())

    classifier, class_pred, class_prob = train_classification(train_df, test_df, metrics)
    regressor, reg_pred = train_regression(train_df, test_df, metrics)
    arima_note = arima_baseline(full_df, metrics)

    importance_rows: list[dict] = []
    xgb_importance(classifier, importance_rows, "XGBoost classifier")
    xgb_importance(regressor, importance_rows, "XGBoost regressor")
    shap_note = shap_importance(classifier, test_df, importance_rows)

    metric_frame = pd.DataFrame(metrics)
    write_warnings = []
    written_labels = []
    if not args.dry_run:
        full_prediction_rows, test_prediction_rows = write_prediction_parquets(
            full_df,
            test_df,
            classifier,
            regressor,
            class_pred,
            class_prob,
            reg_pred,
        )
        for label, writer in [
            ("feature importance", lambda: write_importance(importance_rows)),
            ("prediction sample", lambda: write_prediction_sample(test_df, class_pred, class_prob, reg_pred)),
            (
                "modeling manifest",
                lambda: MANIFEST_MD.write_text(
                    build_manifest(
                        full_rows=len(full_df),
                        model_rows=len(model_df),
                        train_rows=len(train_df),
                        test_rows=len(test_df),
                        train_dates=train_dates,
                        test_dates=test_dates,
                        metrics=metric_frame,
                        importance_rows=importance_rows,
                        arima_note=arima_note,
                        shap_note=shap_note,
                    ),
                    encoding="utf-8",
                ),
            ),
            ("model metrics", lambda: metric_frame.to_csv(METRICS_CSV, index=False)),
        ]:
            try:
                writer()
                written_labels.append(label)
            except PermissionError as error:
                write_warnings.append(f"Could not write {label}: {error}")
    else:
        full_prediction_rows = len(full_df)
        test_prediction_rows = len(test_df)

    print(f"Full input rows: {len(full_df):,}")
    print(f"Modeling rows: {len(model_df):,}")
    print(f"Train rows: {len(train_df):,} | Test rows: {len(test_df):,}")
    key_metrics = metric_frame[
        metric_frame["metric"].isin(["accuracy", "precision", "recall", "f1", "macro_f1", "mae", "mse", "rmse", "r2"])
    ]
    print("Key metrics:")
    for row in key_metrics.itertuples(index=False):
        print(f"- {row.model} | {row.target} | {row.metric}: {row.value}")
    print(f"Explainability rows generated in memory: {len(importance_rows):,}")
    print(f"Full prediction rows prepared: {full_prediction_rows:,}")
    print(f"Test-set prediction rows prepared: {test_prediction_rows:,}")
    print(shap_note)
    print(arima_note)
    if args.dry_run:
        print("Dry run complete: no output files written.")
    else:
        print(f"Wrote: {rel(AI_PREDICTIONS_MODEL_BASELINE_PARQUET)}")
        print(f"Wrote: {rel(AI_PREDICTIONS_TEST_SET_PARQUET)}")
        optional_outputs = {
            "feature importance": IMPORTANCE_CSV,
            "prediction sample": PREDICTION_SAMPLE_CSV,
            "modeling manifest": MANIFEST_MD,
            "model metrics": METRICS_CSV,
        }
        for label in written_labels:
            print(f"Wrote: {rel(optional_outputs[label])}")
        for warning in write_warnings:
            print(f"Warning: {warning}")
        print("GitHub note: commit only the AI module, manifest, and small summary CSVs after manual review.")


if __name__ == "__main__":
    main()
