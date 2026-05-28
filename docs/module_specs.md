# Module Specifications

This document defines the scope, expected files, outputs, and restrictions for each project module.

## General Rules For All Modules

- Inspect existing files before proposing changes.
- Explain the current state before implementation.
- Ask permission before creating, deleting, renaming, or modifying files.
- Work module by module.
- Add sanity checks before moving to the next step.
- Every send-off and handoff must explain how the module supports the Assessment 1 architecture and GitHub reproducibility.
- Do not drift into another module's implementation. If the next logical task belongs elsewhere, stop and create a send-off.
- The AI-DSS modeling layer is mandatory before final Streamlit dashboard work.
- Do not run `git add`, `git commit`, or `git push`.
- Do not overwrite notebooks unless explicitly approved.
- Keep SUMO as scenario validation only.
- Keep Streamlit as the final dashboard layer.
- Do not confuse Kaggle prototype work with the real Auckland GTFS validation pipeline.

## Project Controller

Scope:
- Maintain project roadmap, weekly Notion updates, GitHub checkpoint alerts, and architecture alignment.

Likely files:
- `docs/project_roadmap.md`
- `docs/module_specs.md`
- `docs/test_outputs_checklist.md`
- `docs/file_inventory.md`
- `README.md` only if approved

Expected outputs:
- Weekly progress notes
- Module handoff summaries
- Commit checkpoint recommendations

Restrictions:
- No code or data changes without explicit approval.

## Data Storage / Parquet / DuckDB

Scope:
- Validate large GTFS-Realtime CSV files.
- Preserve raw CSV files as archival evidence.
- Use Parquet for scalable processed storage.
- Plan DuckDB as a later query layer only if Parquet is not sufficient for Streamlit or analytics performance.

Likely files:
- `data/raw/gtfs_realtime/gtfs_realtime_log.csv`
- `data/raw/gtfs_realtime/daily/*.csv`
- `data/processed/gtfs_realtime.parquet`
- `data/processed/gtfs_realtime_cleaned.parquet`
- `src/prepare_realtime_storage.py`

Expected outputs:
- Cleaned Parquet file
- Row-count comparison
- Schema validation summary
- Storage-specific summary CSVs with the `gtfs_realtime_storage_` prefix

Restrictions:
- Do not delete CSV files.
- Do not invalidate earlier notebook outputs without documenting the reason.
- Do not commit raw daily CSV files, large generated CSV outputs, Parquet files, DuckDB files, or output screenshots unless explicitly approved.
- Treat `data/processed/gtfs_realtime_cleaned.parquet` as a local generated artifact.

## Notebook 09 - Real Auckland GTFS-Realtime Validation

Scope:
- Reproduce the real Auckland validation pipeline using repaired GTFS-Realtime data, GTFS Static routes, and Open-Meteo weather.

Likely files:
- `notebooks/09_validation_and_evaluation_realtimegtfs.ipynb`
- `data/raw/gtfs_realtime/*`
- `data/raw/gtfs_static/routes.txt`
- `data/processed/*`
- `data/interim/*`

Required notebook steps:
- Load cleaned Parquet safely when available, with daily CSV and repaired log fallback.
- Clean headers and data types.
- Handle duplicated header rows.
- Convert `delay_seconds` and `delay_minutes` to numeric.
- Filter unreasonable delay outliers.
- Create `trip_hour`, `weekday`, and `day_of_month`.
- Merge GTFS-Realtime with GTFS Static routes.
- Validate route match rate.
- Fetch or load Open-Meteo hourly weather.
- Align GTFS timestamps to hourly weather timestamps.
- Merge weather data using a memory-aware hourly lookup for large real GTFS-Realtime datasets.
- Validate weather match rate.
- Create delay-risk categories.
- Generate operational recommendations.
- Export dashboard-ready outputs.
- Include markdown explanations for non-technical readers.
- Include sanity checks after each major step.

Restrictions:
- Do not delete existing work.
- Do not overwrite outputs without approval.
- Do not commit to GitHub.
- Keep `WRITE_OUTPUTS = False` as the safe default for inspection and documentation runs.

## Decision Engine

Scope:
- Convert delay-risk categories into traceable operational recommendations.

Likely files:
- `notebooks/05_decision_engine.ipynb`
- `notebooks/09_validation_and_evaluation_realtimegtfs.ipynb`
- `src/audit_decision_engine_outputs.py`
- `docs/decision_engine_manifest.md`
- `data/processed/decision_engine_output.csv`
- `data/processed/intervention_logic.csv`
- `data/processed/summaries/decision_recommendation_summary.csv`
- `data/processed/summaries/decision_route_recommendation_counts.csv`

Decision rules:
- Low risk: No operational action required
- Medium risk: Monitor route conditions
- High risk: Adjust service headway
- Severe risk: Deploy standby bus or supervisor review

Expected outputs:
- Recommendation summary table
- Route-level recommendation counts
- Small downstream recommendation output

Restrictions:
- Every recommendation must be traceable to a risk category.
- Keep the full row-level decision CSV local unless explicitly approved for sharing.
- Downstream presentation modules should load summary outputs before falling back to the full decision output.
- Create the manifest and decision summary outputs with `python src/audit_decision_engine_outputs.py`.

## AI-DSS Modeling / SHAP

Scope:
- Build or refine real Auckland AI prediction benchmarks and explainability outputs before final dashboard development.

Likely files:
- `notebooks/04_modeling_checkpoint.ipynb`
- Processed feature tables under `data/processed/`
- Potential new model/evaluation script or notebook only after inspection and permission.

Expected outputs:
- Model metric table
- Feature importance summary
- SHAP explainability artifacts if supported by the model stage
- Predicted delay or delay-risk outputs that can be passed to the Decision Engine

Restrictions:
- Do not overclaim prediction accuracy.
- Keep Kaggle prototype results separate from real Auckland validation results.
- Do not proceed to Streamlit final dashboard work until this module produces reproducible model evidence.

## SUMO Minimal Prototype

Scope:
- Build a minimal one-corridor or one-route SUMO scenario.
- Compare baseline, disruption, and intervention scenarios.

Likely files:
- `notebooks/06_sumo_scenario_preparation.ipynb`
- `notebooks/10_sumo_minimal_prototype.ipynb`
- `data/processed/sumo_scenarios.csv`
- `data/processed/sumo_kpis.csv`
- `data/processed/sumo_validation_results.csv`

Expected outputs:
- Average delay
- Travel time
- Congestion index
- Queue length if available
- Intervention improvement summary

Restrictions:
- Do not claim the SUMO module proves real-world deployment success.
- Do not represent the prototype as a full Auckland network simulation.

## Streamlit Dashboard

Scope:
- Build the final dashboard under `app/`.
- This module is downstream of AI-DSS Modeling and should not restart until model outputs exist.

Likely files:
- `app/streamlit_app.py`
- `data/processed/*.csv`
- `data/processed/*.parquet`
- `data/processed/summaries/*.csv`

Dashboard sections:
- Overview
- Delay Risk Monitor
- AI Prediction Results
- Weather Impact
- SHAP Explainability
- Decision Engine
- SUMO Validation
- Route / Corridor Focus
- Final Insights

Dashboard questions:
- Where is the delay risk?
- What action is recommended?
- What is the expected impact?

Restrictions:
- Load processed outputs instead of raw huge CSVs where possible.
- Show friendly messages when optional files are missing.
- Use decision summary outputs before falling back to row-level decision data.

## Documentation Alignment

Scope:
- Keep implementation aligned with the Assessment 1 proposal and final report direction.

Likely files:
- `README.md`
- `docs/`
- `Assessment_1/Documentation/`

Expected outputs:
- Proposal alignment checklist
- README update suggestions
- Overclaim prevention notes

Restrictions:
- Do not modify documentation without approval.
