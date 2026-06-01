"""Create Decision Engine audit evidence from local Notebook 09 outputs.

Run from the project root:

    python src/audit_decision_engine_outputs.py

Required local input:

    data/processed/decision_engine_output.parquet
    or data/processed/decision_engine_output.csv

That input is a large generated Notebook 09 artifact and should stay out of
GitHub. Parquet is preferred for scalable local use; CSV is kept only as a
fallback/export format. The script writes small summary CSVs used by the
project audit trail and downstream presentation layers.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DECISION_CSV = ROOT / "data" / "processed" / "decision_engine_output.csv"
DECISION_PARQUET = ROOT / "data" / "processed" / "decision_engine_output.parquet"
INTERVENTION_CSV = ROOT / "data" / "processed" / "intervention_logic.csv"
SUMMARY_DIR = ROOT / "data" / "processed" / "summaries"
MANIFEST_MD = ROOT / "docs" / "decision_engine_manifest.md"
RECOMMENDATION_CSV = SUMMARY_DIR / "decision_recommendation_summary.csv"
ROUTE_RECOMMENDATION_CSV = SUMMARY_DIR / "decision_route_recommendation_counts.csv"

RISK_ORDER = ["Low", "Medium", "High", "Severe"]
RISK_ACTIONS = {
    "Low": "No operational action required",
    "Medium": "Monitor route conditions",
    "High": "Adjust service headway",
    "Severe": "Deploy standby bus or supervisor review",
}
USE_COLUMNS = [
    "route_id",
    "route_short_name",
    "route_long_name",
    "delay_risk",
    "recommended_action",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def abort(message: str) -> None:
    raise SystemExit(f"Decision Engine audit failed: {message}")


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8", newline="") as file:
        return max(sum(1 for _ in file) - 1, 0)


def md_table(headers, rows) -> str:
    divider = ["---" for _ in headers]
    lines = [headers, divider, *rows]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in lines)


def require_inputs() -> None:
    if not DECISION_PARQUET.exists() and not DECISION_CSV.exists():
        abort(
            f"`{rel(DECISION_PARQUET)}` or `{rel(DECISION_CSV)}` is missing. "
            "Place the local Notebook 09 decision output at one of these paths "
            "before running the audit."
        )
    if not INTERVENTION_CSV.exists():
        abort(f"`{rel(INTERVENTION_CSV)}` is missing.")


def read_decision_output() -> pd.DataFrame:
    if DECISION_PARQUET.exists():
        try:
            return pd.read_parquet(DECISION_PARQUET, columns=USE_COLUMNS)
        except ValueError:
            columns = pd.read_parquet(DECISION_PARQUET).columns
            missing = sorted(set(USE_COLUMNS) - set(columns))
            abort(f"required decision output columns are missing: {missing}")

    try:
        return pd.read_csv(DECISION_CSV, usecols=USE_COLUMNS)
    except ValueError:
        columns = pd.read_csv(DECISION_CSV, nrows=0).columns
        missing = sorted(set(USE_COLUMNS) - set(columns))
        abort(f"required decision output columns are missing: {missing}")


def create_parquet_from_csv_if_needed() -> None:
    if DECISION_PARQUET.exists() or not DECISION_CSV.exists():
        return

    print(f"Creating scalable local Parquet copy: {rel(DECISION_PARQUET)}")
    df = pd.read_csv(DECISION_CSV)
    df.to_parquet(DECISION_PARQUET, index=False)


def ordered_risk(series: pd.Series) -> pd.Series:
    return pd.Categorical(series, categories=RISK_ORDER, ordered=True)


def validate_decisions(df: pd.DataFrame) -> tuple[int, int, pd.DataFrame]:
    missing_risk = int(df["delay_risk"].isna().sum())
    missing_action = int(df["recommended_action"].isna().sum())
    if missing_risk or missing_action:
        abort(
            "missing values found: "
            f"delay_risk={missing_risk:,}, recommended_action={missing_action:,}"
        )

    pairs = df.groupby(["delay_risk", "recommended_action"], dropna=False).size().reset_index(name="records")
    expected_pairs = {(risk, action) for risk, action in RISK_ACTIONS.items()}
    observed_pairs = {(str(row.delay_risk), str(row.recommended_action)) for row in pairs.itertuples()}
    invalid_pairs = sorted(observed_pairs - expected_pairs)
    missing_pairs = sorted(expected_pairs - observed_pairs)

    if invalid_pairs:
        abort(f"unexpected risk/action pair(s): {invalid_pairs}")
    if missing_pairs:
        abort(f"expected risk/action pair(s) not present: {missing_pairs}")

    action_counts = pairs.groupby("recommended_action")["delay_risk"].nunique()
    ambiguous = action_counts[action_counts != 1]
    if not ambiguous.empty:
        abort(f"actions linked to multiple risks: {ambiguous.to_dict()}")

    return missing_risk, missing_action, pairs


def build_outputs(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    total = len(df)

    recommendation = (
        df.groupby(["delay_risk", "recommended_action"], dropna=False)
        .size()
        .reset_index(name="records")
    )
    recommendation["delay_risk"] = ordered_risk(recommendation["delay_risk"])
    recommendation = recommendation.sort_values("delay_risk").reset_index(drop=True)
    recommendation["delay_risk"] = recommendation["delay_risk"].astype(str)
    recommendation["share_pct"] = (recommendation["records"] / total * 100).round(2)

    route_recommendation = (
        df.groupby(
            ["route_id", "route_short_name", "route_long_name", "delay_risk", "recommended_action"],
            dropna=False,
        )
        .size()
        .reset_index(name="records")
    )
    route_recommendation["delay_risk"] = ordered_risk(route_recommendation["delay_risk"])
    route_recommendation = route_recommendation.sort_values(
        ["route_short_name", "route_id", "delay_risk"], na_position="first"
    ).reset_index(drop=True)
    route_recommendation["delay_risk"] = route_recommendation["delay_risk"].astype(str)
    route_recommendation["share_pct"] = (route_recommendation["records"] / total * 100).round(4)

    return recommendation, route_recommendation


def manifest(total, missing_risk, missing_action, recommendation, route_recommendation) -> str:
    source_rows = [
        [f"`{rel(DECISION_PARQUET)}`", f"{total:,}", "Preferred full row-level real Auckland decision output", "Local artifact; do not commit"],
        [f"`{rel(DECISION_CSV)}`", f"{csv_rows(DECISION_CSV):,}", "Legacy/export row-level decision output", "Local artifact; do not commit"],
        [f"`{rel(INTERVENTION_CSV)}`", csv_rows(INTERVENTION_CSV), "Risk-to-action rule mapping", "Small output"],
        ["`data/processed/summaries/gtfs_realtime_daily_summary.csv`", csv_rows(SUMMARY_DIR / "gtfs_realtime_daily_summary.csv"), "Daily operational summary", "Small output"],
        ["`data/processed/summaries/gtfs_realtime_route_daily_summary.csv`", f"{csv_rows(SUMMARY_DIR / 'gtfs_realtime_route_daily_summary.csv'):,}", "Route-day operational summary", "Small output"],
        ["`data/processed/summaries/gtfs_realtime_top_delayed_routes.csv`", csv_rows(SUMMARY_DIR / "gtfs_realtime_top_delayed_routes.csv"), "Top delayed routes summary", "Small output"],
        [f"`{rel(RECOMMENDATION_CSV)}`", len(recommendation), "Decision recommendation summary", "Small output"],
        [f"`{rel(ROUTE_RECOMMENDATION_CSV)}`", f"{len(route_recommendation):,}", "Route-level recommendation counts", "Small output"],
    ]
    logic_rows = [
        ["Low", "0 to 5 minutes absolute delay", RISK_ACTIONS["Low"]],
        ["Medium", "More than 5 and up to 15 minutes absolute delay", RISK_ACTIONS["Medium"]],
        ["High", "More than 15 and up to 25 minutes absolute delay", RISK_ACTIONS["High"]],
        ["Severe", "More than 25 minutes absolute delay", RISK_ACTIONS["Severe"]],
    ]
    audit_rows = [
        ["Decision output rows", f"{total:,}"],
        ["Missing `delay_risk`", missing_risk],
        ["Missing `recommended_action`", missing_action],
        ["Unique risk-to-action pairs", len(recommendation)],
        ["Recommendation-to-risk cardinality", "1 risk per recommendation"],
        ["Risk-to-action traceability", "100%"],
    ]
    distribution_rows = [
        [row.delay_risk, row.recommended_action, f"{int(row.records):,}", f"{row.share_pct:.2f}%"]
        for row in recommendation.itertuples(index=False)
    ]

    return f"""# Decision Engine Manifest

Last reviewed: 2026-05-28

## Scope

This manifest records the real Auckland GTFS-Realtime decision-engine outputs produced from Notebook 09. It is the traceability note for downstream decision-support modules and does not replace Notebook 09 as the real Auckland validation source.

This audit validates Decision Engine rule consistency and risk-to-action traceability. It does not validate machine-learning prediction accuracy; model evaluation belongs to the AI-DSS modeling module.

Notebook roles:

- `notebooks/05_decision_engine.ipynb`: Kaggle prototype decision-engine reference.
- `notebooks/09_validation_and_evaluation_realtimegtfs.ipynb`: Real Auckland GTFS-Realtime validation source.
- `notebooks/10_sumo_minimal_prototype.ipynb`: Reserved for the SUMO minimal prototype.

Replication command:

```bash
python src/audit_decision_engine_outputs.py
```

Local input required:

- `{rel(DECISION_PARQUET)}` should exist locally. It is the preferred large Notebook 09 decision output and should not be committed to GitHub.
- `{rel(DECISION_CSV)}` can be used as a fallback/export source when Parquet is not available.

Outputs created:

- `{rel(MANIFEST_MD)}`
- `{rel(RECOMMENDATION_CSV)}`
- `{rel(ROUTE_RECOMMENDATION_CSV)}`

## Source Outputs

{md_table(["File", "Rows", "Role", "Commit guidance"], source_rows)}

## Decision Logic

{md_table(["Delay risk", "Delay rule", "Recommended action"], logic_rows)}

The recommendation language is decision support only. It does not represent automated control of services.

## Audit Result

{md_table(["Check", "Result"], audit_rows)}

Recommendation distribution:

{md_table(["Delay risk", "Recommended action", "Records", "Share"], distribution_rows)}

## Downstream Use

The current decision-engine output is valid enough for downstream decision-support presentation. Later dashboard modules should use summary files where possible:

- Use `decision_recommendation_summary.csv` for overall recommendation distribution.
- Use `decision_route_recommendation_counts.csv` for route-level action counts.
- Use `gtfs_realtime_daily_summary.csv`, `gtfs_realtime_route_daily_summary.csv`, and `gtfs_realtime_top_delayed_routes.csv` for operational overview pages.
- Avoid loading `decision_engine_output.csv` by default because it is a large local artifact.
- Prefer `decision_engine_output.parquet` for row-level local analysis when detailed records are required.

## GitHub Reproducibility

Commit the audit script, this manifest, and the small summary CSVs. Do not commit `{rel(DECISION_PARQUET)}` or `{rel(DECISION_CSV)}`. A future examiner can place or regenerate the local decision output at the expected path and run the replication command above to create the same audit evidence.

## Remaining Risks

- The 30-day GTFS-Realtime collection is still continuing, so this remains a frozen 21/22-day baseline until the final collection window is validated.
- Some route metadata remains blank for S-prefix or special routes. Downstream presentation layers should label blank route names clearly.
- Notebook 09 should remain the source of truth for real Auckland validation. Do not create a separate decision-engine notebook unless a later module needs new analysis that cannot be represented by a manifest and summary outputs.
"""


def main() -> None:
    require_inputs()
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_MD.parent.mkdir(parents=True, exist_ok=True)
    create_parquet_from_csv_if_needed()

    print("Decision Engine audit")
    input_path = DECISION_PARQUET if DECISION_PARQUET.exists() else DECISION_CSV
    print(f"Input: {rel(input_path)}")

    decision = read_decision_output()
    missing_risk, missing_action, _ = validate_decisions(decision)
    recommendation, route_recommendation = build_outputs(decision)

    recommendation.to_csv(RECOMMENDATION_CSV, index=False)
    route_recommendation.to_csv(ROUTE_RECOMMENDATION_CSV, index=False)
    MANIFEST_MD.write_text(
        manifest(len(decision), missing_risk, missing_action, recommendation, route_recommendation),
        encoding="utf-8",
    )

    print(f"Rows audited: {len(decision):,}")
    print(f"Missing delay_risk: {missing_risk:,}")
    print(f"Missing recommended_action: {missing_action:,}")
    print("Risk-to-action traceability: 100%")
    print(f"Wrote: {rel(RECOMMENDATION_CSV)} ({len(recommendation):,} rows)")
    print(f"Wrote: {rel(ROUTE_RECOMMENDATION_CSV)} ({len(route_recommendation):,} rows)")
    print(f"Wrote: {rel(MANIFEST_MD)}")
    print("GitHub note: commit the script and small summaries; do not commit full row-level CSV or Parquet outputs.")


if __name__ == "__main__":
    main()
