# Data Storage Manifest

Last reviewed: 2026-06-26

Module: Data Storage / Parquet / DuckDB

Project: AI-Driven Decision Support System for Auckland Public Transport Delay Prediction Using GTFS-Realtime Data

## Storage Decision

The project keeps raw GTFS-Realtime CSV files as archival evidence, uses Parquet for cleaned and processed storage, and uses DuckDB as the local query layer over the canonical Parquet outputs.

Parquet is the official current format for large processed outputs. CSV is retained for lightweight summaries, fallback exports, and human-readable evidence, not as the main large-data path. DuckDB is implemented as the live local query layer for the M5.1 Streamlit dashboard so the dashboard can query Parquet through SQL views instead of loading large row-level CSV files directly.

DuckDB is a generated local query layer, not a production database and not the source of truth. It must be regenerated whenever the canonical Parquet outputs are regenerated.

## What Stays Raw

Raw GTFS-Realtime collection files stay under:

- `data/raw/gtfs_realtime/*.csv`
- `data/raw/gtfs_realtime/*.json`
- `data/raw/gtfs_realtime/daily/*.csv`

These files should not be deleted or rewritten during normal analysis. They are evidence of the live collection process and should be treated as local data artifacts, not lightweight source files.

The raw daily collection covers a 31-file calendar window. After daily completeness screening, 23 days were classified as likely complete and used as the quality-controlled modelling baseline. The remaining 8 days are startup partial, interrupted, or in-progress days and are retained as raw archival evidence only. Do not claim a clean 30-day dataset.

## What Becomes Parquet

Canonical Parquet outputs are written under `data/processed/parquet/`:

- `gtfs_realtime_cleaned.parquet` — all-file cleaned GTFS-Realtime working dataset, preferred for descriptive analytics and dashboard coverage.
- `gtfs_realtime_model_baseline.parquet` — quality-controlled complete-day records, preferred for AI modelling and evaluation.
- `decision_engine_model_baseline.parquet` — observed/reference risk decision output for the model baseline.
- `decision_engine_all_file.parquet` — observed/reference risk decision output for all collected files.
- `ai_predictions_model_baseline.parquet` — full AI prediction output for dashboard views.
- `ai_predictions_test_set.parquet` — held-out test-set AI prediction output for fair model-evaluation evidence.
- `ai_decision_support_model_baseline.parquet` — AI-based decision-support output; the primary final dashboard source.

Current validation result (final hybrid storage rerun):

- All-file cleaned Parquet rows: 3,904,432
- Model-baseline Parquet rows: 3,339,454
- Raw daily files inspected: 31
- Likely complete days: 23
- Partial/interrupted days: 8
- Route metadata match rate: 97.34%
- `route_display_name` missing rows: 0
- S-prefix rows flagged: 228,038
- Default top delayed route summary excludes S-prefix special services
- Columns match expected schema: true
- `delay_minutes` numeric: true
- `collection_time_utc` datetime-compatible: true
- Duplicated header rows: 0

The Decision Engine row-level CSV outputs were later converted to Parquet for dashboard use:

- Model-baseline Decision Engine rows (CSV / Parquet / DuckDB): 3,338,383
- All-file Decision Engine rows (CSV / Parquet / DuckDB): 3,903,290

Expected cleaned GTFS-Realtime Parquet schema:

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

## DuckDB Query Layer

DuckDB is created by a separate local query-layer script and stored under `data/processed/duckdb/`:

- Script: `src/create_realtime_duckdb.py`
- Output: `data/processed/duckdb/gtfs_realtime.duckdb`

Current DuckDB views:

- `decision_engine_model_baseline`
- `decision_engine_all_file`
- `realtime_all`
- `realtime_model_baseline`
- `route_daily_summary`
- `collection_completeness`

Use `decision_engine_model_baseline` for quality-controlled modelling/evaluation dashboard views and `decision_engine_all_file` for full descriptive/dashboard coverage. The AI decision-support Parquet (`ai_decision_support_model_baseline.parquet`) is the primary dashboard source; a dedicated DuckDB view over it should be added/confirmed before relying on it through SQL rather than direct Parquet reads.

Regenerate DuckDB whenever the canonical Parquet outputs are regenerated:

```bash
python src/prepare_realtime_storage.py
python src/create_realtime_duckdb.py
```

## What Should Not Be Committed

The following are large generated or raw data artifacts and should stay out of GitHub unless explicitly approved:

- `data/raw/gtfs_realtime/*.csv`
- `data/raw/gtfs_realtime/*.json`
- `data/raw/gtfs_realtime/daily/*.csv`
- `data/processed/parquet/*.parquet`
- `data/processed/duckdb/*.duckdb`
- `data/processed/outputs/**/decision_engine_output.csv`
- `outputs/`

Folder placeholders (`data/processed/parquet/.gitkeep.txt`, `data/processed/duckdb/.gitkeep.txt`) are kept in Git so the canonical folders exist; the generated Parquet/DuckDB contents are not committed.

## What Can Be Committed

The following are small and useful for reproducibility or assessment evidence:

- `src/prepare_realtime_storage.py`
- `src/create_realtime_duckdb.py`
- `src/realtime_storage/` modules
- `docs/data_storage_manifest.md`
- `data/processed/summaries/*.csv` (after review when small)
- SUMO scenario summary CSVs, if intentionally kept small

Storage-specific summaries use the `gtfs_realtime_storage_` prefix so they do not overwrite Notebook 09 validation summaries.

Current storage-specific summary outputs:

- `data/processed/summaries/gtfs_realtime_storage_daily_summary.csv`
- `data/processed/summaries/gtfs_realtime_storage_route_daily_summary.csv`
- `data/processed/summaries/gtfs_realtime_storage_top_delayed_routes.csv`
- `data/processed/summaries/gtfs_realtime_collection_completeness.csv`

The old root-level generated outputs (for example `data/processed/decision_engine_output.csv`, `data/processed/intervention_logic.csv`, and the non-prefixed `gtfs_realtime_daily_summary.csv` / `gtfs_realtime_route_daily_summary.csv` / `gtfs_realtime_top_delayed_routes.csv`) were old duplicates and have been moved to a local archive. Do not reference them as current outputs.

## Streamlit Loading Guidance

Streamlit should prefer this order:

1. Use DuckDB views over the canonical Parquet outputs for large row-level risk/action/weather dashboard views.
2. Use small summary CSVs for overview KPIs and lightweight charts.
3. Avoid loading large row-level CSV files directly by default.
4. Avoid loading raw daily CSV files in the dashboard unless debugging collection history.

## Required Sanity Checks

Before using the canonical Parquet datasets:

- CSV row count matches Parquet row count after cleaning.
- DuckDB row counts match the corresponding Parquet row counts.
- Column names match the expected schema.
- `delay_minutes` is numeric.
- `collection_time_utc` is datetime-compatible.
- Duplicated header rows are removed.
- Files load successfully in pandas/pyarrow.
- DuckDB regenerated after any Parquet regeneration.
- Raw CSV files remain unchanged.
