"""Run the real Auckland AI-DSS modeling checkpoint.

Run from the project root:

    python src/train_ai_dss_model.py

Required local input:

    data/processed/decision_engine_output.csv

The input is a large Notebook 09 artifact and should stay out of GitHub. This
script writes small evidence outputs for Assessment 1 reproducibility.
"""

import argparse

import pandas as pd

from ai_dss_modeling.config import IMPORTANCE_CSV, MANIFEST_MD, METRICS_CSV, PREDICTION_SAMPLE_CSV, SUMMARY_DIR
from ai_dss_modeling.data import read_input, rel, sample_for_modeling, time_split
from ai_dss_modeling.explainability import shap_importance, xgb_importance
from ai_dss_modeling.metrics import add_metric
from ai_dss_modeling.models import arima_baseline, train_classification, train_regression
from ai_dss_modeling.reporting import build_manifest, write_importance, write_prediction_sample


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

    full_df = read_input()
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
    if not args.dry_run:
        write_importance(importance_rows)
        write_prediction_sample(test_df, class_pred, class_prob, reg_pred)
        MANIFEST_MD.write_text(
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
        )
        metric_frame.to_csv(METRICS_CSV, index=False)

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
    print(shap_note)
    print(arima_note)
    if args.dry_run:
        print("Dry run complete: no output files written.")
    else:
        print(f"Wrote: {rel(METRICS_CSV)}")
        print(f"Wrote: {rel(IMPORTANCE_CSV)}")
        print(f"Wrote: {rel(PREDICTION_SAMPLE_CSV)}")
        print(f"Wrote: {rel(MANIFEST_MD)}")
        print("GitHub note: commit only the AI module, manifest, and small summary CSVs after manual review.")


if __name__ == "__main__":
    main()
