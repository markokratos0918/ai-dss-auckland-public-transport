# Data Storage Manifest

Last reviewed: 2026-05-27

Module: Data Storage / Parquet / DuckDB

Project: AI-Driven Decision Support System for Auckland Public Transport Delay Prediction Using GTFS-Realtime Data

## Storage Decision

The project keeps raw GTFS-Realtime CSV files as archival evidence and uses Parquet for cleaned, processed storage. DuckDB is planned as an optional later query layer after the Parquet dataset is stable.

Current checkpoint result: Parquet is sufficient for the storage layer as of 2026-05-27. DuckDB is deferred until dashboard or analytics performance requires it.

## What Stays Raw

Raw GTFS-Realtime collection files stay under:

- `data/raw/gtfs_realtime/*.csv`
- `data/raw/gtfs_realtime/*.json`
- `data/raw/gtfs_realtime/daily/*.csv`

These files should not be deleted or rewritten during normal analysis. They are evidence of the live collection process and should be treated as local data artifacts, not lightweight source files.

## What Becomes Parquet

Cleaned daily GTFS-Realtime records are written to:

- `data/processed/gtfs_realtime_cleaned.parquet`

This file is the preferred local input for analytics, validation work, and dashboard loading when detailed row-level GTFS-Realtime records are needed.

Current validation result:

- File: `data/processed/gtfs_realtime_cleaned.parquet`
- Size: 28.47 MB
- Rows: 2,530,712
- Source daily files: 22
- Date range: 2026-05-06 to 2026-05-27
- Columns match expected schema: true
- `delay_minutes` numeric: true
- `collection_time_utc` datetime-compatible: true
- Duplicated header rows: 0
- Old empty Parquet placeholder exists: false

Expected Parquet schema:

- `collection_time_utc`
- `entity_id`
- `trip_id`
- `route_id`
- `direction_id`
- `start_time`
- `start_date`
- `timestamp`
- `delay_seconds`
- `is_deleted`
- `delay_minutes`
- `collection_date`
- `source_file`

## What Should Not Be Committed

The following are large generated or raw data artifacts and should stay out of GitHub unless explicitly approved:

- `data/raw/gtfs_realtime/*.csv`
- `data/raw/gtfs_realtime/*.json`
- `data/raw/gtfs_realtime/daily/*.csv`
- `data/processed/*.parquet`
- `data/processed/*.duckdb`
- `data/processed/decision_engine_output.csv`
- `outputs/`

This includes `outputs/storage_audit/parquet_validation_summary.png` unless explicitly approved for assessment evidence.

## What Can Be Committed

The following are small and useful for reproducibility or assessment evidence:

- `src/prepare_realtime_storage.py`
- `docs/data_storage_manifest.md`
- `data/processed/summaries/*.csv`
- `data/processed/intervention_logic.csv`
- SUMO scenario summary CSVs, if intentionally kept small

Storage-specific summaries use the `gtfs_realtime_storage_` prefix so they do not overwrite Notebook 09 validation summaries.

Current storage-specific summary outputs:

- `data/processed/summaries/gtfs_realtime_storage_daily_summary.csv`
- `data/processed/summaries/gtfs_realtime_storage_route_daily_summary.csv`
- `data/processed/summaries/gtfs_realtime_storage_top_delayed_routes.csv`

## DuckDB Decision

DuckDB is not required immediately. The current priority is to establish one reliable cleaned Parquet dataset and validate row counts, schema, and datatypes.

DuckDB should be added later if:

- Streamlit becomes slow when filtering Parquet directly.
- Multiple processed tables need SQL joins.
- The dashboard needs route/date/time-window queries without loading all rows into memory.

If added, DuckDB should be treated as a generated local query cache, not the source of truth.

## Streamlit Loading Guidance

Streamlit should prefer this order:

1. Load small summary CSVs for overview KPIs and charts.
2. Load `data/processed/gtfs_realtime_cleaned.parquet` for detailed row-level filtering.
3. Use DuckDB later only if query performance requires it.
4. Avoid loading raw daily CSV files in the dashboard unless debugging collection history.

## Required Sanity Checks

Before using the cleaned Parquet dataset:

- CSV row count matches Parquet row count after cleaning.
- Column names match the expected schema.
- `delay_minutes` is numeric.
- `collection_time_utc` is datetime-compatible.
- Duplicated header rows are removed.
- File loads successfully in pandas.
- Raw CSV files remain unchanged.
