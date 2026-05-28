# Project Roadmap

Project: AI-Driven Decision Support System for Auckland Public Transport Delay Prediction Using GTFS-Realtime Data

Student: Mark Dela Torre

Course: MSE907 - Industry-based Capstone Research Project

## Architecture Guardrails

- GTFS Static, GTFS-Realtime, and Open-Meteo form the data foundation.
- The AI-DSS layer is mandatory and must include real Auckland prediction/evaluation before final dashboard work.
- XGBoost or another structured ML model, a baseline comparison, and SHAP or feature-importance evidence are required to satisfy the Assessment 1 proposal.
- AI prediction and the decision engine support operational delay-risk decisions.
- SUMO is a scenario-validation module for selected corridors or routes only.
- Streamlit is the final dashboard and presentation layer.
- The dashboard should load processed outputs where possible and should not depend on live SUMO execution.
- Kaggle prototype notebooks must stay clearly separated from the real Auckland GTFS validation pipeline.
- Module chats must not drift into another module. Each send-off and handoff must state how the work supports GitHub reproducibility and the Assessment 1 architecture.

## Roadmap

| Phase | Module | Goal | Main Output | Commit Alert |
|---|---|---|---|---|
| 1 | Project Controller | Maintain architecture, Notion updates, GitHub checkpoints, and sanity checks | Roadmap, weekly updates, commit reminders | After roadmap/spec docs are approved |
| 2 | File Inventory | Document current project files and module ownership | Project and module inventory | After inventory is saved |
| 3 | Data Storage | Validate daily GTFS-Realtime CSVs, confirm or create Parquet, and plan DuckDB | Clean Parquet and validation report | Checkpoint reached on 2026-05-27 |
| 4 | Notebook 09 | Run the real Auckland GTFS-Realtime, GTFS Static, and Open-Meteo validation pipeline | Dashboard-ready validation outputs | Final baseline checkpoint reached on 2026-05-28 |
| 5 | Decision Engine | Convert delay risk into operational recommendations | Recommendation tables | Checkpoint reached on 2026-05-28 |
| 6 | AI-DSS Modeling and SHAP | Build real Auckland prediction benchmarks and explainability outputs | Model metrics and SHAP outputs | Next required checkpoint |
| 7 | SUMO Prototype | Validate one selected corridor or route scenario | Scenario KPI tables | After baseline, disruption, and intervention outputs exist |
| 8 | Streamlit Dashboard | Build the final presentation dashboard | `app/streamlit_app.py` | After dashboard runs locally |
| 9 | Documentation | Align README, report evidence, and implementation claims | Updated documentation | After final documentation review |

## Module Checkpoints

### Decision Engine - Real Auckland Outputs Audit

Checkpoint date: 2026-05-28

Status: Decision-engine outputs from Notebook 09 were audited and validated as dashboard-ready, provided the dashboard uses summary outputs instead of the large row-level CSV by default.

Validated outputs:

- Row-level decision output: `data/processed/decision_engine_output.csv`
- Row-level decision rows: 2,529,972
- Missing `delay_risk`: 0
- Missing `recommended_action`: 0
- Risk-to-action pairs: 4
- Recommendation-to-risk mapping: exactly one risk category per recommendation
- Risk-to-action traceability: 100%
- Recommendation summary: `data/processed/summaries/decision_recommendation_summary.csv`
- Route-level recommendation counts: `data/processed/summaries/decision_route_recommendation_counts.csv`
- Decision manifest: `docs/decision_engine_manifest.md`
- Reproducibility script: `src/audit_decision_engine_outputs.py`
- Reproducibility command: `python src/audit_decision_engine_outputs.py`

Recommendation distribution:

- Low / No operational action required: 1,965,777
- Medium / Monitor route conditions: 525,781
- High / Adjust service headway: 28,826
- Severe / Deploy standby bus or supervisor review: 9,588

Dashboard decision:

- Streamlit should use `decision_recommendation_summary.csv`, `decision_route_recommendation_counts.csv`, and the existing daily, route-daily, and top-delayed summaries by default.
- Streamlit should avoid loading `data/processed/decision_engine_output.csv` unless a specific detail view requires it and performance is acceptable.

GitHub reproducibility:

- GitHub should track the audit script, manifest, and small summary CSVs.
- The full row-level `data/processed/decision_engine_output.csv` is required locally to regenerate the audit but should not be committed.
- This audit validates Decision Engine rule consistency and risk-to-action traceability. It does not validate ML prediction accuracy.

Known limitations:

- The 30-day GTFS-Realtime collection is still ongoing.
- Some route metadata remains blank for S-prefix or special-service routes.
- `data/processed/decision_engine_output.csv` is about 480 MB and should not be committed to GitHub.
- Streamlit-related local changes should be reviewed in the dedicated Streamlit module chat.

### Data Storage / Parquet / DuckDB

Checkpoint date: 2026-05-27

Status: Completed current Parquet storage validation for the real GTFS-Realtime daily collection.

Validated outputs:

- Cleaned Parquet file: `data/processed/gtfs_realtime_cleaned.parquet`
- Parquet size: 28.47 MB
- Parquet rows: 2,530,712
- Source daily files represented: 22
- Date range: 2026-05-06 to 2026-05-27
- Expected schema match: true
- `delay_minutes` numeric: true
- `collection_time_utc` datetime-compatible: true
- Duplicated header rows: 0
- Old empty `data/processed/gtfs_realtime.parquet` placeholder removed

Storage decision:

- Raw daily GTFS-Realtime CSV files remain archival evidence.
- Cleaned, analysis-ready realtime records are stored as Parquet under `data/processed/`.
- Large generated CSVs, raw daily files, Parquet files, and output screenshots should not be committed unless explicitly approved.
- DuckDB is deferred until Streamlit or analytics queries require SQL-style querying or faster filtering.

Evidence:

- Storage audit screenshot generated under `outputs/storage_audit/parquet_validation_summary.png`
- Storage-specific summary CSVs generated under `data/processed/summaries/`

Known limitations:

- The raw collection is still growing toward the planned 30-day dataset.
- Parquet should be regenerated after the final collection window.
- DuckDB has not been tested because it is not required yet.

### Notebook 09 - Real Auckland GTFS-Realtime Validation

Checkpoint date: 2026-05-27

Status: Completed current pipeline validation using the available daily GTFS-Realtime collection.

Validated outputs:

- Source daily files represented: 22
- Decision output rows: 2,560,237
- Daily summary rows: 22
- Route daily summary rows: 8,622
- Top delayed routes: 20
- Intervention logic rows: 4
- Route match rate: 97.47%
- Weather match rate in exported outputs: 100.0%
- Delay range after filtering: about -59.97 to 119.95 minutes
- Notebook execution: 20 / 20 code cells, 0 error outputs

Evidence:

- Screenshots generated under `outputs/notebook09_validation_screenshots/`
- Large CSV outputs were generated locally but should not be committed until the storage strategy is confirmed.

Known limitations:

- The collection is still growing toward the planned 30-day dataset.
- S-prefix routes remain unmatched in GTFS Static metadata, likely school or special service variants.
- Large generated outputs require Parquet/DuckDB storage decisions before GitHub upload decisions.

### Notebook 09 - Parquet Input Integration

Checkpoint date: 2026-05-28

Status: Notebook 09 now supports the cleaned Parquet dataset as the preferred input path, with daily CSV loading preserved as a fallback and audit path. This checkpoint is the frozen 21/22-day baseline for downstream modules until a deliberate 30-day re-export is approved.

Validated behavior:

- `INPUT_MODE = "auto"` added for source selection.
- If `data/processed/gtfs_realtime_cleaned.parquet` exists and can be read, Notebook 09 loads Parquet.
- If Parquet is missing or unreadable, Notebook 09 prints the fallback reason and loads daily CSV files.
- If `INPUT_MODE = "parquet"` is selected, Parquet is required and failure is explicit.
- Verified input source: `cleaned_parquet`
- Loaded GTFS-Realtime shape: 2,530,712 rows and 13 columns.
- Rows dropped during basic cleaning: 0
- Source files represented: 22
- Notebook syntax check: 0 errors
- No dashboard CSV outputs were overwritten.

Final baseline outputs validated:

- `data/interim/realtime_with_routes_sample.csv`: 10,000 rows
- `data/interim/gtfs_weather_integrated_sample.csv`: 10,000 rows
- `data/processed/decision_engine_output.csv`: 2,529,972 rows
- `data/processed/intervention_logic.csv`: 4 rows
- `data/processed/summaries/gtfs_realtime_daily_summary.csv`: 22 rows
- `data/processed/summaries/gtfs_realtime_route_daily_summary.csv`: 8,575 rows
- `data/processed/summaries/gtfs_realtime_top_delayed_routes.csv`: 20 rows

Resolved issue:

- The original full-data pandas weather merge caused a memory error on the multi-million-row dataset.
- Notebook 09 now uses an hourly weather lookup instead of a heavy dataframe merge.
- The weather lookup keeps the validation logic but is safer for the current baseline and future 30-day collection.

Environment note:

- `pyarrow==16.1.0` was installed in the VS Code/Jupyter project environment at `C:\Users\DTMAR\anaconda3\envs\capstone-gtfs`.

Commit guidance:

- Commit `notebooks/09_validation_and_evaluation_realtimegtfs.ipynb` and related controller documentation only.
- Do not commit large generated outputs, especially `data/processed/decision_engine_output.csv`.

## Weekly Control Rhythm

- Update Notion before starting project work each Monday.
- Record what was completed, current work, next-week plan, blockers, supervisor questions, meeting notes, and supervisor feedback.
- Ask for a GitHub commit checkpoint after each stable module output.
- Do not run `git add`, `git commit`, or `git push` from Codex. Mark will handle GitHub updates manually.

## Current Priority Order

1. Build the AI-DSS Modeling module using the real Auckland GTFS-Realtime + weather baseline.
2. Produce reproducible model metrics and explainability evidence.
3. Integrate predicted delay/risk outputs back into the Decision Engine.
4. Build and verify the Streamlit dashboard only after the AI-DSS outputs exist.
5. Scope the SUMO minimal prototype after the dashboard-ready AI/decision outputs are stable.
6. Align README and final report documentation.
7. Continue 30-day GTFS-Realtime collection in parallel.
8. Rerun the validated pipeline, Parquet build, AI model, and decision audit on the final 30-day dataset only after a controlled export checkpoint is approved.
