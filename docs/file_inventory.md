# File Inventory

This inventory records the current project structure and the likely module ownership of key files.

Last reviewed: 2026-05-28

## Root Files

| Path | Purpose / Notes |
|---|---|
| `README.md` | Main project overview. Candidate for later documentation alignment. |
| `requirements.txt` | Python package requirements. |
| `collect_gtfs_realtime.py` | GTFS-Realtime collection script. |
| `.env` | Environment configuration. Do not expose secrets. |
| `.gitignore` | Git ignore rules. Updated to exclude large raw/generated GTFS-Realtime artifacts. |
| `archive/source_archives/source_papers.zip` | Archived source papers moved out of the active root folder. |
| `archive/source_archives/source_papers (2).zip` | Additional archived source papers moved out of the active root folder. |

## Notebooks

| Path | Module |
|---|---|
| `notebooks/01_gtfs_static_inspection.ipynb` | GTFS Static inspection |
| `notebooks/02_gtfs_realtime_collection.ipynb` | GTFS-Realtime collection |
| `notebooks/03_weather_integration.ipynb` | Weather integration |
| `notebooks/04_modeling_checkpoint.ipynb` | Kaggle prototype modeling |
| `notebooks/05_decision_engine.ipynb` | Kaggle prototype decision engine |
| `notebooks/06_sumo_scenario_preparation.ipynb` | Kaggle prototype SUMO scenario framework |
| `notebooks/07_validation_and_evaluation.ipynb` | Kaggle prototype validation |
| `notebooks/08_dashboard_prototype.ipynb` | Dashboard design/prototype |
| `notebooks/09_validation_and_evaluation_realtimegtfs.ipynb` | Real Auckland GTFS + Open-Meteo validation. Supports Parquet-first loading with daily CSV fallback and memory-aware hourly weather lookup. Current frozen baseline: 22 daily summaries, 2,529,972 decision output rows, and Parquet load shape of 2,530,712 rows by 13 columns. |

Not currently visible:

- `notebooks/10_sumo_minimal_prototype.ipynb`

## Source Code

| Path | Module |
|---|---|
| `src/prepare_realtime_storage.py` | Data storage / Parquet preparation. Current module script creates cleaned Parquet and storage summary CSVs from daily GTFS-Realtime files. |
| `scripts/commit_data_storage_checkpoint.ps1` | Helper script to stage and commit only the approved Data Storage checkpoint files. |
| `scripts/commit_notebook09_baseline_checkpoint.ps1` | Helper script to stage and commit only the approved Notebook 09 baseline checkpoint files. |
| `scripts/commit_decision_engine_reproducibility_checkpoint.ps1` | Helper script to stage and commit only the approved Decision Engine reproducibility checkpoint files. |
| `scripts/push_current_branch_manual.ps1` | Helper script for manually pushing the current branch after reviewing local commits. |
| `src/audit_decision_engine_outputs.py` | Reproducibility script that creates the Decision Engine manifest and small decision summary CSVs from the local row-level output. |

## Documentation

| Path | Purpose / Notes |
|---|---|
| `docs/decision_engine_manifest.md` | Real Auckland decision-engine output audit, traceability record, and dashboard-readiness guidance. |

## Raw Data

| Path | Purpose / Notes |
|---|---|
| `data/raw/modeling/public_transport_delays.csv` | Kaggle or prototype modeling dataset |
| `data/raw/gtfs_static/gtfs.zip` | GTFS Static archive |
| `data/raw/gtfs_static/agency.txt` | GTFS Static agency data |
| `data/raw/gtfs_static/calendar.txt` | GTFS Static calendar data |
| `data/raw/gtfs_static/calendar_dates.txt` | GTFS Static calendar exceptions |
| `data/raw/gtfs_static/fare_attributes.txt` | GTFS Static fare attributes |
| `data/raw/gtfs_static/fare_rules.txt` | GTFS Static fare rules |
| `data/raw/gtfs_static/feed_info.txt` | GTFS Static feed metadata |
| `data/raw/gtfs_static/frequencies.txt` | GTFS Static frequencies |
| `data/raw/gtfs_static/routes.txt` | GTFS Static route metadata |
| `data/raw/gtfs_static/shapes.txt` | GTFS Static route shapes |
| `data/raw/gtfs_static/stops.txt` | GTFS Static stops |
| `data/raw/gtfs_static/stop_times.txt` | GTFS Static stop times |
| `data/raw/gtfs_static/transfers.txt` | GTFS Static transfers |
| `data/raw/gtfs_static/trips.txt` | GTFS Static trips |
| `data/raw/gtfs_realtime/gtfs_realtime_log.csv` | Raw GTFS-Realtime log; keep as archival evidence |
| `data/raw/gtfs_realtime/gtfs_realtime_log _backup.csv` | Backup realtime log |
| `data/raw/gtfs_realtime/gtfs_realtime_log_old.csv` | Older realtime log |
| `data/raw/gtfs_realtime/gtfs_realtime_log_validation.csv` | Validation realtime log |
| `data/raw/gtfs_realtime/tripupdates_20260430_204204.json` | Raw GTFS-Realtime JSON sample |

## Daily GTFS-Realtime Files

Current daily CSV files are stored under:

`data/raw/gtfs_realtime/daily/`

Visible date range:

- `gtfs_realtime_2026-05-06.csv`
- `gtfs_realtime_2026-05-07.csv`
- `gtfs_realtime_2026-05-08.csv`
- `gtfs_realtime_2026-05-09.csv`
- `gtfs_realtime_2026-05-10.csv`
- `gtfs_realtime_2026-05-11.csv`
- `gtfs_realtime_2026-05-12.csv`
- `gtfs_realtime_2026-05-13.csv`
- `gtfs_realtime_2026-05-14.csv`
- `gtfs_realtime_2026-05-15.csv`
- `gtfs_realtime_2026-05-16.csv`
- `gtfs_realtime_2026-05-17.csv`
- `gtfs_realtime_2026-05-18.csv`
- `gtfs_realtime_2026-05-19.csv`
- `gtfs_realtime_2026-05-20.csv`
- `gtfs_realtime_2026-05-21.csv`
- `gtfs_realtime_2026-05-22.csv`
- `gtfs_realtime_2026-05-23.csv`
- `gtfs_realtime_2026-05-24.csv`
- `gtfs_realtime_2026-05-25.csv`
- `gtfs_realtime_2026-05-26.csv`
- `gtfs_realtime_2026-05-27.csv`

## Interim Data

| Path | Purpose / Notes |
|---|---|
| `data/interim/realtime_with_routes_sample.csv` | Realtime data merged with route metadata sample |
| `data/interim/gtfs_weather_integrated_sample.csv` | GTFS and weather integrated sample |

## Processed Data

| Path | Module |
|---|---|
| `data/processed/gtfs_realtime_cleaned.parquet` | Cleaned analysis-ready GTFS-Realtime Parquet file. Local generated artifact; do not commit unless explicitly approved. |
| `data/processed/gtfs_realtime.parquet` | Old empty placeholder removed during Data Storage checkpoint |
| `data/processed/decision_engine_output.csv` | Full row-level decision engine output. Local generated artifact; do not commit unless explicitly approved. |
| `data/processed/intervention_logic.csv` | Intervention logic output |
| `data/processed/summaries/decision_recommendation_summary.csv` | Decision recommendation summary; small output |
| `data/processed/summaries/decision_route_recommendation_counts.csv` | Route-level decision recommendation counts; small output |
| `data/processed/sumo_kpis.csv` | SUMO KPI output |
| `data/processed/sumo_scenarios.csv` | SUMO scenario output |
| `data/processed/sumo_validation_results.csv` | SUMO validation results |
| `data/processed/summaries/gtfs_realtime_daily_summary.csv` | Daily realtime summary |
| `data/processed/summaries/gtfs_realtime_route_daily_summary.csv` | Route daily realtime summary |
| `data/processed/summaries/gtfs_realtime_top_delayed_routes.csv` | Top delayed routes summary |
| `data/processed/summaries/gtfs_realtime_storage_daily_summary.csv` | Storage module daily summary; safe to commit if size remains small |
| `data/processed/summaries/gtfs_realtime_storage_route_daily_summary.csv` | Storage module route daily summary; safe to commit if size remains small |
| `data/processed/summaries/gtfs_realtime_storage_top_delayed_routes.csv` | Storage module top delayed routes summary; safe to commit if size remains small |

Notebook 09 original validation checkpoint output sizes reported on 2026-05-27:

- `data/processed/decision_engine_output.csv`: 2,560,237 rows
- `data/processed/intervention_logic.csv`: 4 rows
- `data/processed/summaries/gtfs_realtime_daily_summary.csv`: 22 rows
- `data/processed/summaries/gtfs_realtime_route_daily_summary.csv`: 8,622 rows
- `data/processed/summaries/gtfs_realtime_top_delayed_routes.csv`: 20 rows

Notebook 09 frozen baseline output sizes reported on 2026-05-28:

- `data/interim/realtime_with_routes_sample.csv`: 10,000 rows
- `data/interim/gtfs_weather_integrated_sample.csv`: 10,000 rows
- `data/processed/decision_engine_output.csv`: 2,529,972 rows; local generated artifact, do not commit
- `data/processed/intervention_logic.csv`: 4 rows
- `data/processed/summaries/gtfs_realtime_daily_summary.csv`: 22 rows
- `data/processed/summaries/gtfs_realtime_route_daily_summary.csv`: 8,575 rows
- `data/processed/summaries/gtfs_realtime_top_delayed_routes.csv`: 20 rows
- `data/processed/summaries/decision_recommendation_summary.csv`: 4 rows
- `data/processed/summaries/decision_route_recommendation_counts.csv`: 1,493 rows

Data Storage checkpoint output sizes reported on 2026-05-27:

- `data/processed/gtfs_realtime_cleaned.parquet`: 28.47 MB, 2,530,712 rows, local generated artifact
- `data/processed/summaries/gtfs_realtime_storage_daily_summary.csv`: summary CSV, safe to commit if size remains small
- `data/processed/summaries/gtfs_realtime_storage_route_daily_summary.csv`: summary CSV, safe to commit if size remains small
- `data/processed/summaries/gtfs_realtime_storage_top_delayed_routes.csv`: summary CSV, safe to commit if size remains small

Notebook 09 Parquet integration checkpoint reported on 2026-05-28:

- Preferred input: `data/processed/gtfs_realtime_cleaned.parquet`
- Input mode: `INPUT_MODE = "auto"`
- Verified source used: `cleaned_parquet`
- Loaded shape: 2,530,712 rows by 13 columns
- Fallback retained: daily CSV files under `data/raw/gtfs_realtime/daily/`, `gtfs_realtime_log_validation.csv`, and `gtfs_realtime_log.csv`
- Memory-aware weather integration added using hourly lookup instead of full dataframe merge
- `WRITE_OUTPUTS = False` remains the safe default to avoid accidental overwrites
- No project data outputs were created or overwritten during final inspection

## Documentation And Assessment Evidence

| Path | Purpose / Notes |
|---|---|
| `docs/architecture/` | Architecture documentation folder |
| `docs/proposal/` | Proposal documentation folder |
| `Assessment_1/` | Assessment 1 working files and evidence |
| `Assessment_1/Documentation/` | Assessment 1 documentation and proposal versions |
| `Assessment_1/Documentation/submission/` | Submitted Assessment 1 artifacts |

## Presentation Artifacts

| Path | Purpose / Notes |
|---|---|
| `presentation/` | Proposal and capstone presentation files |
| `outputs/figures/` | Figure outputs |
| `outputs/tables/` | Table outputs |
| `outputs/notebook09_validation_screenshots/` | Screenshot evidence from Notebook 09 validation outputs |
| `outputs/storage_audit/parquet_validation_summary.png` | Storage audit screenshot. Local generated artifact; do not commit unless explicitly approved |
| `outputs/manual-20260521-presentation/` | Presentation generation outputs |

## Archive

| Path | Purpose / Notes |
|---|---|
| `archive/source_archives/` | Root ZIP archives moved out of active project root |
| `archive/presentation_versions/` | Older presentation versions |
| `archive/notebook_checkpoints/` | Jupyter checkpoint folders moved out of active notebook paths |
| `archive/project_admin/` | Reserved for future project administration archive items |

## Missing Or Future Areas

| Path | Intended Use |
|---|---|
| `app/` | Future Streamlit dashboard folder. Do not recreate until the AI-DSS modeling checkpoint is complete. |
| `app/streamlit_app.py` | Future final Streamlit dashboard. Removed accidental early app draft from the active project scope. |
| `notebooks/10_sumo_minimal_prototype.ipynb` | Future one-corridor SUMO prototype |
| DuckDB database file | Potential later query layer, deferred until dashboard or analytics performance requires it |
