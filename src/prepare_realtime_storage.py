"""
Prepare final hybrid GTFS-Realtime storage outputs.

This entry point coordinates the storage modules that:
- preserve raw daily GTFS-Realtime CSV files as archival evidence;
- create all-file and model-baseline Parquet datasets;
- enrich rows with route metadata and collection completeness flags;
- write GitHub-safe summary CSV files.

DuckDB is handled separately by:
    python src/create_realtime_duckdb.py
"""

from __future__ import annotations

import argparse

from realtime_storage.cleaning import load_daily_frames
from realtime_storage.completeness import build_completeness_manifest
from realtime_storage.config import DAILY_DIR, PARQUET_DIR, SUMMARY_DIR
from realtime_storage.decision_engine_outputs import convert_decision_engine_outputs
from realtime_storage.legacy_split import split_legacy_csv
from realtime_storage.parquet_outputs import write_parquet_outputs
from realtime_storage.route_metadata import enrich_with_hybrid_fields
from realtime_storage.summaries import create_summaries
from realtime_storage.validation import validate_outputs


def build_hybrid_storage() -> dict[str, object]:
    """Run the final hybrid Parquet and summary generation workflow."""
    print(f"Loading daily CSV files from: {DAILY_DIR}")
    realtime_df, file_stats, counters = load_daily_frames()

    completeness = build_completeness_manifest(realtime_df, file_stats)
    enriched_df = enrich_with_hybrid_fields(realtime_df, completeness)
    counters.update(
        {
            "cleaned_rows": len(enriched_df),
            "complete_days": int(completeness["is_model_baseline_day"].sum()),
            "partial_days": int(completeness["is_partial_day"].sum()),
            "model_baseline_rows": int(enriched_df["is_model_baseline_day"].sum()),
            "delay_outliers_abs_gt_120": int(
                enriched_df["delay_minutes"].abs().gt(120).sum()
            ),
        }
    )

    print(f"Writing Parquet files to: {PARQUET_DIR}")
    all_df, _ = write_parquet_outputs(enriched_df)

    print(f"Writing summary CSV files to: {SUMMARY_DIR}")
    _, route_summary, _ = create_summaries(all_df, completeness)

    validation = validate_outputs(
        expected_rows=counters["cleaned_rows"],
        expected_model_rows=counters["model_baseline_rows"],
        expected_route_summary_rows=len(route_summary),
        expected_complete_days=counters["complete_days"],
        expected_partial_days=counters["partial_days"],
    )
    print("Writing Decision Engine Parquet outputs")
    decision_engine_validation = convert_decision_engine_outputs()

    return {
        "counters": counters,
        "validation": validation,
        "decision_engine_validation": decision_engine_validation,
    }


def print_validation_report(counters: dict[str, int], validation: dict[str, object]) -> None:
    """Print the final sanity check report for the storage module."""
    print("Done.")
    print("Hybrid storage validation:")
    print(f"- Daily files: {counters['daily_files']:,}")
    print(f"- Raw CSV rows: {counters['raw_csv_rows']:,}")
    print(f"- Duplicate header rows removed: {counters['duplicate_header_rows']:,}")
    print(f"- Delay outliers beyond +/-120 minutes: {counters['delay_outliers_abs_gt_120']:,}")
    print(f"- All-file cleaned rows: {validation['all_parquet_rows']:,}")
    print(f"- Model-baseline rows: {validation['model_baseline_rows']:,}")
    print(f"- Likely complete days: {validation['complete_days']:,}")
    print(f"- Partial/interrupted days: {validation['partial_days']:,}")
    print(f"- All row count matches: {validation['all_row_count_matches']}")
    print(f"- Model row count matches: {validation['model_row_count_matches']}")
    print(f"- Model baseline only complete days: {validation['model_only_complete_days']}")
    print(f"- Columns match expected schema: {validation['columns_match']}")
    print(f"- delay_minutes numeric: {validation['delay_minutes_numeric']}")
    print(f"- collection_time_utc datetime: {validation['collection_time_utc_datetime']}")
    print(
        "- Route metadata row match rate: "
        f"{validation['route_metadata_row_match_rate_percent']}%"
    )
    print(f"- S-prefix rows flagged: {validation['s_prefix_rows_flagged']:,}")
    print(f"- Default top delayed routes exclude S-prefix: {validation['top_routes_excludes_s_prefix']}")
    print(f"- All-file Parquet size MB: {validation['all_parquet_size_mb']}")
    print(f"- Model-baseline Parquet size MB: {validation['model_parquet_size_mb']}")
    print("DuckDB query layer is handled separately by src/create_realtime_duckdb.py")


def print_decision_engine_report(results: dict[str, dict[str, object]]) -> None:
    """Print row-count and dashboard schema checks for Decision Engine Parquet outputs."""
    print("Decision Engine Parquet validation:")
    for label, validation in results.items():
        print(f"- {label} CSV rows: {validation['csv_rows']:,}")
        print(f"- {label} Parquet rows: {validation['parquet_rows']:,}")
        print(f"- {label} row count matches: {validation['row_count_matches']}")
        print(f"- {label} missing required fields: {validation['missing_required_fields']}")
        print(f"- {label} delay_risk missing: {validation['delay_risk_missing']}")
        print(f"- {label} recommended_action missing: {validation['recommended_action_missing']}")
        print(f"- {label} special-route rows: {validation['special_route_rows']:,}")
        print(f"- {label} Parquet size MB: {validation['parquet_size_mb']}")


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split-legacy",
        action="store_true",
        help="Split the legacy gtfs_realtime_log.csv into daily CSV files.",
    )
    parser.add_argument(
        "--overwrite-daily",
        action="store_true",
        help="Overwrite daily CSV outputs during --split-legacy.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.split_legacy:
        split_legacy_csv(overwrite_daily=args.overwrite_daily)

    result = build_hybrid_storage()
    print_validation_report(result["counters"], result["validation"])
    print_decision_engine_report(result["decision_engine_validation"])


if __name__ == "__main__":
    main()
