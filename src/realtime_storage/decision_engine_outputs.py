"""Decision Engine row-level CSV to Parquet conversion helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from realtime_storage.config import (
    DECISION_ENGINE_ALL_FILE_CSV,
    DECISION_ENGINE_ALL_FILE_PARQUET,
    DECISION_ENGINE_MODEL_BASELINE_CSV,
    DECISION_ENGINE_MODEL_BASELINE_PARQUET,
    PARQUET_DIR,
    REQUIRED_DECISION_ENGINE_DASHBOARD_FIELDS,
)


DECISION_ENGINE_DATASETS = {
    "model_baseline": {
        "csv": DECISION_ENGINE_MODEL_BASELINE_CSV,
        "parquet": DECISION_ENGINE_MODEL_BASELINE_PARQUET,
    },
    "all_file": {
        "csv": DECISION_ENGINE_ALL_FILE_CSV,
        "parquet": DECISION_ENGINE_ALL_FILE_PARQUET,
    },
}

STRING_COLUMNS = [
    "collection_time_utc",
    "collection_date",
    "collection_day_status",
    "route_id",
    "route_short_name",
    "route_long_name",
    "agency_id",
    "service_type",
    "route_display_name",
    "route_corridor_name",
    "trip_id",
    "delay_risk",
    "recommended_action",
    "source_file",
]

BOOLEAN_COLUMNS = [
    "is_partial_day",
    "is_model_baseline_day",
    "is_special_route",
]

INTEGER_COLUMNS = [
    "route_type",
    "direction_id",
    "delay_seconds",
    "trip_hour",
    "weekday",
    "day_of_month",
]

FLOAT_COLUMNS = [
    "collection_coverage_hours",
    "delay_minutes",
    "temperature_2m",
    "precipitation",
    "rain",
    "relative_humidity_2m",
    "wind_speed_10m",
]


def require_csv_schema(path: Path) -> list[str]:
    """Return CSV columns and fail early if dashboard fields are missing."""
    if not path.exists():
        raise FileNotFoundError(f"Decision Engine CSV not found: {path}")

    columns = list(pd.read_csv(path, nrows=0).columns)
    missing = [
        column
        for column in REQUIRED_DECISION_ENGINE_DASHBOARD_FIELDS
        if column not in columns
    ]
    if missing:
        raise ValueError(f"Missing required dashboard fields in {path}: {missing}")
    return columns


def normalize_chunk_types(chunk: pd.DataFrame) -> pd.DataFrame:
    """Apply stable dtypes so Parquet chunks share one schema."""
    chunk = chunk.copy()
    for column in STRING_COLUMNS:
        if column in chunk.columns:
            chunk[column] = chunk[column].astype("string")

    for column in BOOLEAN_COLUMNS:
        if column in chunk.columns:
            if chunk[column].dtype == bool:
                continue
            chunk[column] = (
                chunk[column]
                .astype("string")
                .str.lower()
                .map({"true": True, "1": True, "false": False, "0": False})
                .astype("boolean")
            )

    for column in INTEGER_COLUMNS:
        if column in chunk.columns:
            chunk[column] = pd.to_numeric(chunk[column], errors="coerce").astype("Int64")

    for column in FLOAT_COLUMNS:
        if column in chunk.columns:
            chunk[column] = pd.to_numeric(chunk[column], errors="coerce").astype("float64")

    return chunk


def write_decision_engine_parquet(
    csv_path: Path,
    parquet_path: Path,
    chunksize: int = 200_000,
) -> int:
    """Convert a large Decision Engine CSV to Parquet and return CSV row count."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ImportError(
            "Decision Engine Parquet conversion requires pyarrow. Install project "
            "requirements, then rerun this script."
        ) from exc

    require_csv_schema(csv_path)
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    if parquet_path.exists():
        parquet_path.unlink()

    writer = None
    row_count = 0
    try:
        for chunk in pd.read_csv(csv_path, chunksize=chunksize, low_memory=False):
            chunk = normalize_chunk_types(chunk)
            table = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(parquet_path, table.schema)
            writer.write_table(table)
            row_count += len(chunk)
    finally:
        if writer is not None:
            writer.close()

    return row_count


def validate_decision_engine_parquet(
    csv_path: Path,
    parquet_path: Path,
    expected_csv_rows: int,
) -> dict[str, object]:
    """Validate row counts and dashboard fields after Parquet conversion."""
    parquet_df = pd.read_parquet(parquet_path)
    missing_required = [
        column
        for column in REQUIRED_DECISION_ENGINE_DASHBOARD_FIELDS
        if column not in parquet_df.columns
    ]

    required_missing_counts = {}
    for column in REQUIRED_DECISION_ENGINE_DASHBOARD_FIELDS:
        if column in parquet_df.columns:
            missing_count = int(parquet_df[column].isna().sum())
            if parquet_df[column].dtype == object:
                missing_count += int(parquet_df[column].astype(str).str.strip().eq("").sum())
            required_missing_counts[column] = missing_count

    special_route_count = (
        int(parquet_df["is_special_route"].astype(str).str.lower().isin(["true", "1"]).sum())
        if "is_special_route" in parquet_df.columns
        else None
    )

    return {
        "csv_path": str(csv_path),
        "parquet_path": str(parquet_path),
        "csv_rows": expected_csv_rows,
        "parquet_rows": len(parquet_df),
        "row_count_matches": len(parquet_df) == expected_csv_rows,
        "missing_required_fields": missing_required,
        "required_missing_counts": required_missing_counts,
        "delay_risk_missing": required_missing_counts.get("delay_risk"),
        "recommended_action_missing": required_missing_counts.get("recommended_action"),
        "special_route_rows": special_route_count,
        "parquet_size_mb": round(parquet_path.stat().st_size / 1024 / 1024, 2),
    }


def convert_decision_engine_outputs() -> dict[str, dict[str, object]]:
    """Convert both final Decision Engine CSV outputs to Parquet."""
    results = {}
    for label, paths in DECISION_ENGINE_DATASETS.items():
        csv_path = paths["csv"]
        parquet_path = paths["parquet"]
        print(f"Writing Decision Engine Parquet ({label}): {parquet_path}")
        csv_rows = write_decision_engine_parquet(csv_path, parquet_path)
        results[label] = validate_decision_engine_parquet(
            csv_path=csv_path,
            parquet_path=parquet_path,
            expected_csv_rows=csv_rows,
        )
    return results
