"""Create AI-based Decision Engine outputs from M2 prediction results.

Run from the project root:

    python src/build_ai_decision_support_outputs.py --dry-run
    python src/build_ai_decision_support_outputs.py

Input:

    data/processed/parquet/ai_predictions_model_baseline.parquet

Outputs:

    data/processed/parquet/ai_decision_support_model_baseline.parquet
    data/processed/summaries/ai_decision_recommendation_summary.csv
    data/processed/summaries/ai_decision_route_recommendation_counts.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PARQUET = ROOT / "data" / "processed" / "parquet" / "ai_predictions_model_baseline.parquet"
OUTPUT_PARQUET = ROOT / "data" / "processed" / "parquet" / "ai_decision_support_model_baseline.parquet"
SUMMARY_DIR = ROOT / "data" / "processed" / "summaries"
RECOMMENDATION_CSV = SUMMARY_DIR / "ai_decision_recommendation_summary.csv"
ROUTE_RECOMMENDATION_CSV = SUMMARY_DIR / "ai_decision_route_recommendation_counts.csv"

CONTEXT_COLUMNS = [
    "collection_time_utc",
    "collection_date",
    "route_id",
    "route_short_name",
    "route_display_name",
    "route_corridor_name",
    "service_type",
    "route_type",
    "direction_id",
    "is_special_route",
    "trip_hour",
    "weekday",
    "day_of_month",
    "temperature_2m",
    "precipitation",
    "rain",
    "relative_humidity_2m",
    "wind_speed_10m",
    "collection_day_status",
    "collection_coverage_hours",
    "is_partial_day",
    "is_model_baseline_day",
]
OBSERVED_COLUMNS = ["delay_minutes", "delay_risk", "recommended_action", "actual_actionable_delay_risk"]
PREDICTION_COLUMNS = [
    "predicted_actionable_delay_risk",
    "predicted_actionable_probability",
    "predicted_delay_minutes",
]
REQUIRED_COLUMNS = CONTEXT_COLUMNS + OBSERVED_COLUMNS + PREDICTION_COLUMNS

RISK_ORDER = ["Low", "Medium", "High", "Severe"]
AI_ACTIONS = {
    "Low": "No operational action required",
    "Medium": "Monitor route conditions",
    "High": "Adjust service headway",
    "Severe": "Deploy standby bus or supervisor review",
}
CONFIDENCE_BANDS = {
    "Low": "Low action probability",
    "Medium": "Moderate action probability",
    "High": "High action probability",
    "Severe": "Severe action probability",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(message: str) -> None:
    raise SystemExit(f"AI Decision Engine build failed: {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build AI-based Decision Engine outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Run validation without writing output files.")
    parser.add_argument(
        "--include-special-routes",
        action="store_true",
        help="Include S-prefix/special services in route-level summary.",
    )
    return parser.parse_args()


def read_predictions() -> pd.DataFrame:
    if not INPUT_PARQUET.exists():
        fail(f"`{rel(INPUT_PARQUET)}` is missing.")
    columns = pd.read_parquet(INPUT_PARQUET).head(0).columns.tolist()
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        fail(f"required column(s) missing from AI prediction input: {missing}")
    return pd.read_parquet(INPUT_PARQUET, columns=REQUIRED_COLUMNS)


def assign_ai_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    probability = output["predicted_actionable_probability"]
    if probability.isna().any():
        fail("`predicted_actionable_probability` contains missing values.")
    if not ((probability >= 0) & (probability <= 1)).all():
        fail("`predicted_actionable_probability` contains values outside 0 to 1.")

    output["ai_delay_risk"] = pd.cut(
        probability,
        bins=[-0.000001, 0.50, 0.70, 0.85, 1.000001],
        labels=RISK_ORDER,
        right=False,
    ).astype(str)
    output["ai_recommended_action"] = output["ai_delay_risk"].map(AI_ACTIONS)
    output["ai_confidence_band"] = output["ai_delay_risk"].map(CONFIDENCE_BANDS)
    output["ai_decision_basis"] = "AI actionable-risk probability mapped to operational recommendation."
    return output


def validate_output(df: pd.DataFrame) -> None:
    for column in ["ai_delay_risk", "ai_recommended_action", "ai_confidence_band", "ai_decision_basis"]:
        if column not in df.columns:
            fail(f"`{column}` was not created.")
        if df[column].isna().any():
            fail(f"`{column}` contains missing values.")

    pairs = df.groupby(["ai_delay_risk", "ai_recommended_action"]).size().reset_index(name="records")
    expected = set(AI_ACTIONS.items())
    observed = {(str(row.ai_delay_risk), str(row.ai_recommended_action)) for row in pairs.itertuples()}
    invalid = sorted(observed - expected)
    if invalid:
        fail(f"unexpected AI risk/action pair(s): {invalid}")

    action_counts = pairs.groupby("ai_recommended_action")["ai_delay_risk"].nunique()
    ambiguous = action_counts[action_counts != 1]
    if not ambiguous.empty:
        fail(f"AI actions mapped to multiple risks: {ambiguous.to_dict()}")


def ordered_risk(series: pd.Series) -> pd.Series:
    return pd.Categorical(series, categories=RISK_ORDER, ordered=True)


def recommendation_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["ai_delay_risk", "ai_recommended_action", "ai_confidence_band"], dropna=False)
        .size()
        .reset_index(name="records")
    )
    summary["ai_delay_risk"] = ordered_risk(summary["ai_delay_risk"])
    summary = summary.sort_values("ai_delay_risk").reset_index(drop=True)
    summary["ai_delay_risk"] = summary["ai_delay_risk"].astype(str)
    summary["share_pct"] = (summary["records"] / len(df) * 100).round(2)
    return summary


def route_summary(df: pd.DataFrame, include_special_routes: bool) -> pd.DataFrame:
    route_df = df.copy()
    if "is_special_route" in route_df.columns and not include_special_routes:
        route_df = route_df[~route_df["is_special_route"].astype(str).str.lower().eq("true")].copy()

    groups = [
        "route_id",
        "route_short_name",
        "route_display_name",
        "route_corridor_name",
        "service_type",
        "is_special_route",
        "ai_delay_risk",
        "ai_recommended_action",
        "ai_confidence_band",
    ]
    summary = route_df.groupby(groups, dropna=False).size().reset_index(name="records")
    summary["ai_delay_risk"] = ordered_risk(summary["ai_delay_risk"])
    summary = summary.sort_values(["route_display_name", "route_id", "ai_delay_risk"]).reset_index(drop=True)
    summary["ai_delay_risk"] = summary["ai_delay_risk"].astype(str)
    summary["share_pct"] = (summary["records"] / len(df) * 100).round(4)
    return summary


def print_checks(df: pd.DataFrame, route_counts: pd.DataFrame) -> None:
    print(f"Rows: {len(df):,}")
    print(f"Missing ai_delay_risk: {int(df['ai_delay_risk'].isna().sum()):,}")
    print(f"Missing ai_recommended_action: {int(df['ai_recommended_action'].isna().sum()):,}")
    print(f"Probability min: {df['predicted_actionable_probability'].min():.6f}")
    print(f"Probability max: {df['predicted_actionable_probability'].max():.6f}")
    print(f"S-prefix records retained in source: {int(df['route_id'].astype(str).str.upper().str.startswith('S').sum()):,}")
    print(
        "is_special_route=True records: "
        f"{int(df['is_special_route'].astype(str).str.lower().eq('true').sum()):,}"
    )
    print(f"Route-level summary rows: {len(route_counts):,}")
    print("\nAI recommendation distribution:")
    print(recommendation_summary(df).to_string(index=False))


def main() -> None:
    args = parse_args()
    predictions = read_predictions()
    output = assign_ai_recommendations(predictions)
    validate_output(output)
    rec_summary = recommendation_summary(output)
    route_counts = route_summary(output, args.include_special_routes)

    print("AI-based Decision Engine build")
    print(f"Input: {rel(INPUT_PARQUET)}")
    print_checks(output, route_counts)
    print(
        "Special route handling: "
        + ("included in route summary" if args.include_special_routes else "excluded from default route summary")
    )

    if args.dry_run:
        print("\nDry run complete. No files were written.")
        return

    OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    output.to_parquet(OUTPUT_PARQUET, index=False)
    rec_summary.to_csv(RECOMMENDATION_CSV, index=False)
    route_counts.to_csv(ROUTE_RECOMMENDATION_CSV, index=False)
    print(f"\nWrote: {rel(OUTPUT_PARQUET)}")
    print(f"Wrote: {rel(RECOMMENDATION_CSV)}")
    print(f"Wrote: {rel(ROUTE_RECOMMENDATION_CSV)}")
    print("GitHub note: commit the script and small summaries; do not commit large Parquet outputs.")


if __name__ == "__main__":
    main()
