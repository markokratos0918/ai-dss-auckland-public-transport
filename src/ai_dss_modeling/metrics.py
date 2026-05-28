"""Metric helpers for the AI-DSS modeling checkpoint."""

import math

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)


def add_metric(rows: list[dict], model: str, target_type: str, target: str, metric: str, value, notes: str = "") -> None:
    if isinstance(value, (float, np.floating)):
        if math.isnan(value) or math.isinf(value):
            value = ""
        else:
            value = round(float(value), 6)
    rows.append(
        {
            "model": model,
            "target_type": target_type,
            "target": target,
            "metric": metric,
            "value": value,
            "notes": notes,
        }
    )


def classification_metrics(rows: list[dict], model_name: str, y_true, y_pred) -> None:
    target = "actionable_delay_risk"
    add_metric(rows, model_name, "classification", target, "accuracy", accuracy_score(y_true, y_pred))
    add_metric(rows, model_name, "classification", target, "precision", precision_score(y_true, y_pred, zero_division=0))
    add_metric(rows, model_name, "classification", target, "recall", recall_score(y_true, y_pred, zero_division=0))
    add_metric(rows, model_name, "classification", target, "f1", f1_score(y_true, y_pred, zero_division=0))
    add_metric(rows, model_name, "classification", target, "macro_f1", f1_score(y_true, y_pred, average="macro", zero_division=0))
    add_metric(rows, model_name, "classification", target, "weighted_f1", f1_score(y_true, y_pred, average="weighted", zero_division=0))
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    add_metric(rows, model_name, "classification", target, "true_negative_low", int(tn))
    add_metric(rows, model_name, "classification", target, "false_positive_actionable", int(fp))
    add_metric(rows, model_name, "classification", target, "false_negative_actionable", int(fn))
    add_metric(rows, model_name, "classification", target, "true_positive_actionable", int(tp))


def regression_metrics(rows: list[dict], model_name: str, target: str, y_true, y_pred, notes: str = "") -> None:
    mse = mean_squared_error(y_true, y_pred)
    add_metric(rows, model_name, "regression", target, "mae", mean_absolute_error(y_true, y_pred), notes)
    add_metric(rows, model_name, "regression", target, "mse", mse, notes)
    add_metric(rows, model_name, "regression", target, "rmse", math.sqrt(mse), notes)
    add_metric(rows, model_name, "regression", target, "r2", r2_score(y_true, y_pred), notes)

