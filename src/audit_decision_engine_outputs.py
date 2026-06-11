"""Audit Decision Engine outputs from the official current folder.

Run from the project root:

    python src/audit_decision_engine_outputs.py --dry-run
    python src/audit_decision_engine_outputs.py

Official current input:

    data/processed/outputs/model_baseline/decision_engine_output.csv

The input is a large local generated output and should stay out of GitHub.
The script checks the Decision Engine rules and creates small summary CSVs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "data" / "processed" / "outputs" / "model_baseline"
DECISION_CSV = INPUT_DIR / "decision_engine_output.csv"
INTERVENTION_CSV = INPUT_DIR / "intervention_logic.csv"
SUMMARY_DIR = ROOT / "data" / "processed" / "summaries"
RECOMMENDATION_CSV = SUMMARY_DIR / "decision_recommendation_summary.csv"
ROUTE_RECOMMENDATION_CSV = SUMMARY_DIR / "decision_route_recommendation_counts.csv"

RISK_ORDER = ["Low", "Medium", "High", "Severe"]
RISK_ACTIONS = {
    "Low": "No operational action required",
    "Medium": "Monitor route conditions",
    "High": "Adjust service headway",
    "Severe": "Deploy standby bus or supervisor review",
}
REQUIRED_COLUMNS = ["route_id", "delay_risk", "recommended_action"]
OPTIONAL_ROUTE_COLUMNS = [
    "route_short_name",
    "route_long_name",
    "route_corridor_name",
    "service_type",
    "route_display_name",
    "is_special_route",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(message: str) -> None:
    raise SystemExit(f"Decision Engine audit failed: {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit model-baseline Decision Engine outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Run checks without writing summary files.")
    parser.add_argument(
        "--include-special-routes",
        action="store_true",
        help="Include S-prefix/special routes in route-level summary outputs.",
    )
    return parser.parse_args()


def read_header(path: Path) -> list[str]:
    if not path.exists():
        fail(f"`{rel(path)}` is missing. Use the official current model-baseline output folder.")
    return pd.read_csv(path, nrows=0).columns.tolist()


def read_decision_output() -> pd.DataFrame:
    header = read_header(DECISION_CSV)
    missing = sorted(set(REQUIRED_COLUMNS) - set(header))
    if missing:
        fail(f"required column(s) missing from `{rel(DECISION_CSV)}`: {missing}")

    usecols = REQUIRED_COLUMNS + [column for column in OPTIONAL_ROUTE_COLUMNS if column in header]
    return pd.read_csv(DECISION_CSV, usecols=usecols)


def ordered_risk(series: pd.Series) -> pd.Series:
    return pd.Categorical(series, categories=RISK_ORDER, ordered=True)


def validate_traceability(df: pd.DataFrame) -> tuple[int, int, pd.DataFrame]:
    missing_risk = int(df["delay_risk"].isna().sum())
    missing_action = int(df["recommended_action"].isna().sum())
    if missing_risk or missing_action:
        fail(f"missing values found: delay_risk={missing_risk:,}, recommended_action={missing_action:,}")

    pairs = df.groupby(["delay_risk", "recommended_action"], dropna=False).size().reset_index(name="records")
    expected_pairs = set(RISK_ACTIONS.items())
    observed_pairs = {(str(row.delay_risk), str(row.recommended_action)) for row in pairs.itertuples()}
    invalid_pairs = sorted(observed_pairs - expected_pairs)
    if invalid_pairs:
        fail(f"unexpected risk/action pair(s): {invalid_pairs}")

    action_risk_counts = pairs.groupby("recommended_action")["delay_risk"].nunique()
    ambiguous = action_risk_counts[action_risk_counts != 1]
    if not ambiguous.empty:
        fail(f"recommended actions mapped to multiple risks: {ambiguous.to_dict()}")

    return missing_risk, missing_action, pairs


def build_recommendation_summary(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    summary = df.groupby(["delay_risk", "recommended_action"], dropna=False).size().reset_index(name="records")
    summary["delay_risk"] = ordered_risk(summary["delay_risk"])
    summary = summary.sort_values("delay_risk").reset_index(drop=True)
    summary["delay_risk"] = summary["delay_risk"].astype(str)
    summary["share_pct"] = (summary["records"] / total * 100).round(2)
    return summary


def build_route_summary(df: pd.DataFrame, include_special_routes: bool) -> pd.DataFrame:
    route_df = df.copy()
    if "is_special_route" in route_df.columns and not include_special_routes:
        route_df = route_df[~route_df["is_special_route"].astype(str).str.lower().eq("true")].copy()

    group_columns = [
        column
        for column in [
            "route_id",
            "route_short_name",
            "route_long_name",
            "route_corridor_name",
            "service_type",
            "route_display_name",
            "is_special_route",
            "delay_risk",
            "recommended_action",
        ]
        if column in route_df.columns
    ]
    route_summary = route_df.groupby(group_columns, dropna=False).size().reset_index(name="records")
    route_summary["delay_risk"] = ordered_risk(route_summary["delay_risk"])
    sort_columns = [column for column in ["route_display_name", "route_id", "delay_risk"] if column in route_summary]
    route_summary = route_summary.sort_values(sort_columns, na_position="last").reset_index(drop=True)
    route_summary["delay_risk"] = route_summary["delay_risk"].astype(str)
    route_summary["share_pct"] = (route_summary["records"] / len(df) * 100).round(4)
    return route_summary


def print_field_checks(df: pd.DataFrame) -> None:
    for column in ["route_corridor_name", "service_type", "route_display_name", "is_special_route"]:
        if column in df.columns:
            print(f"{column}: present, missing={int(df[column].isna().sum()):,}")
        else:
            print(f"{column}: not available")

    s_prefix_count = int(df["route_id"].astype(str).str.upper().str.startswith("S").sum())
    special_count = (
        int(df["is_special_route"].astype(str).str.lower().eq("true").sum())
        if "is_special_route" in df.columns
        else "not available"
    )
    print(f"S-prefix route records retained in source: {s_prefix_count:,}")
    print(f"is_special_route=True records: {special_count}")


def write_outputs(recommendation: pd.DataFrame, route_summary: pd.DataFrame) -> None:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    recommendation.to_csv(RECOMMENDATION_CSV, index=False)
    route_summary.to_csv(ROUTE_RECOMMENDATION_CSV, index=False)


def main() -> None:
    args = parse_args()
    if not INTERVENTION_CSV.exists():
        fail(f"`{rel(INTERVENTION_CSV)}` is missing.")

    decision = read_decision_output()
    missing_risk, missing_action, pairs = validate_traceability(decision)
    recommendation = build_recommendation_summary(decision)
    route_summary = build_route_summary(decision, args.include_special_routes)

    print("Decision Engine audit")
    print(f"Input: {rel(DECISION_CSV)}")
    print(f"Rows audited: {len(decision):,}")
    print(f"Missing delay_risk: {missing_risk:,}")
    print(f"Missing recommended_action: {missing_action:,}")
    print("Risk-to-action traceability: 100%")
    print("\nRecommendation distribution:")
    print(recommendation.to_string(index=False))
    print()
    print_field_checks(decision)
    print(f"Route-level summary rows: {len(route_summary):,}")
    print(
        "Special route handling: "
        + ("included in route summary" if args.include_special_routes else "excluded from default route summary")
    )

    if args.dry_run:
        print("\nDry run complete. No files were written.")
        return

    write_outputs(recommendation, route_summary)
    print(f"\nWrote: {rel(RECOMMENDATION_CSV)}")
    print(f"Wrote: {rel(ROUTE_RECOMMENDATION_CSV)}")
    print("GitHub note: commit the script and small summaries; do not commit large row-level outputs.")


if __name__ == "__main__":
    main()
