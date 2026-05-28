# Test Outputs Checklist

This checklist defines the minimum test outputs and sanity checks expected before each module is considered ready for a GitHub checkpoint.

## Universal Sanity Check

Before moving to the next step, record:

1. What was completed?
2. What files were read?
3. What files may be changed?
4. What outputs were produced?
5. What errors or risks remain?
6. Is permission needed before continuing?

## Data Storage / Parquet / DuckDB

Latest checkpoint: 2026-05-27

Passed checks:

- Cleaned Parquet created at `data/processed/gtfs_realtime_cleaned.parquet`.
- Parquet size: 28.47 MB.
- Parquet rows: 2,530,712.
- Source daily files represented: 22.
- Date range: 2026-05-06 to 2026-05-27.
- Columns match expected schema: true.
- `delay_minutes` numeric: true.
- `collection_time_utc` datetime-compatible: true.
- Duplicated header rows: 0.
- Old 0-byte Parquet placeholder exists: false.
- Raw daily GTFS-Realtime CSV files remain archival evidence.

Remaining risks:

- Raw daily CSV collection is still growing toward the planned 30-day dataset.
- `data/processed/decision_engine_output.csv` is still modified and very large; avoid committing it.
- DuckDB has not been tested because Parquet is sufficient at this stage.
- Parquet should be regenerated after the final collection window.

Required checks:

- CSV row count matches Parquet row count after intended cleaning rules are applied.
- Column names match the expected schema.
- `delay_minutes` is numeric.
- `collection_time_utc` is datetime-compatible.
- Duplicated header rows are removed.
- Parquet file loads successfully in pandas.
- Raw CSV files remain unchanged.

Expected test outputs:

- Row-count comparison table.
- Schema summary.
- Duplicated-header count before and after cleaning.
- File load confirmation.

## Notebook 09 - Real Auckland GTFS-Realtime Validation

Latest checkpoint: 2026-05-28

Passed checks:

- Parquet-first input integration added with `INPUT_MODE = "auto"`.
- Verified input source used: `cleaned_parquet`.
- Parquet load shape: 2,530,712 rows and 13 columns.
- Rows dropped during basic cleaning after Parquet load: 0.
- Source files represented from Parquet input: 22.
- Parquet date range: 2026-05-06 09:34:55+00:00 to 2026-05-27 06:43:26+00:00.
- `delay_minutes` numeric: true.
- `collection_time_utc` datetime-compatible: true.
- Duplicate header rows: 0.
- Notebook syntax check: 0 errors.
- No dashboard CSV outputs were overwritten during Parquet integration.
- Memory-aware weather lookup added to avoid full-data pandas weather merge memory errors.
- `WRITE_OUTPUTS = False` preserved as the safe default.
- Required operational columns present in exported outputs.
- Weather fields present and numeric in integrated output.
- Decision output contains `delay_risk` and `recommended_action`.
- Final frozen baseline output rows verified: 2,529,972 decision rows, 22 daily summary rows, 8,575 route daily summary rows, 20 top delayed routes, and 4 intervention logic rows.
- Notebook 09 executed successfully with `MAX_DAILY_FILES = None`.
- 20 / 20 code cells executed.
- 0 error outputs.
- Source daily files represented: 22.
- Decision output rows: 2,560,237.
- Daily summary rows: 22.
- Route daily summary rows: 8,622.
- Top delayed routes: 20.
- Intervention logic rows: 4.
- Route match rate: 97.47%.
- Weather match rate in exported outputs: 100.0%.
- Delay range after filtering: about -59.97 to 119.95 minutes.
- Daily summary total matched the decision output row count.
- Required decision output columns were present.
- Screenshots were generated from actual notebook outputs.

Remaining risks:

- Collection is still growing toward the planned 30-day dataset.
- S-prefix routes remain unmatched in GTFS Static metadata, likely school or special services.
- Large generated CSV outputs should not be committed until the storage strategy is confirmed.
- Parquet must be regenerated after the final 30-day collection window and Notebook 09 should be rerun against that final Parquet.
- Downstream modules should treat the current 21/22-day outputs as frozen unless a deliberate export checkpoint is approved.

Required checks:

- Realtime file loads safely.
- Cleaned Parquet loads safely when present.
- Daily CSV fallback remains available when Parquet is missing or unreadable.
- Headers are cleaned.
- `delay_seconds` and `delay_minutes` are numeric.
- Unreasonable delay outliers are filtered or flagged.
- Temporal features exist: `trip_hour`, `weekday`, `day_of_month`.
- GTFS Static route merge succeeds.
- Route match rate is printed.
- Weather data is loaded or fetched.
- GTFS timestamps align to hourly weather timestamps.
- Weather integration is memory-aware for multi-million-row validation data.
- Weather match rate is printed.
- Delay-risk categories are created.
- Operational recommendations are created.
- Dashboard-ready outputs are exported only after approval.

Expected test outputs:

- Data shape after each major stage.
- Missing-value summary.
- Route match-rate summary.
- Weather match-rate summary.
- Delay-risk distribution.
- Recommendation distribution.

## Decision Engine

Required checks:

- No missing `delay_risk`.
- No missing `recommended_action`.
- 100% recommendation traceability from risk category to action.
- Recommendation distribution is printed.
- Route-level recommendation counts are generated.

Expected test outputs:

- `src/audit_decision_engine_outputs.py`: reproducibility script.
- `data/processed/summaries/decision_recommendation_summary.csv`: 4 rows.
- `data/processed/summaries/decision_route_recommendation_counts.csv`: 1,493 rows.
- `docs/decision_engine_manifest.md`: traceability and dashboard-readiness record.

Validated 2026-05-28:

- Reproducibility command: `python src/audit_decision_engine_outputs.py`.
- Decision output rows: 2,529,972.
- Missing `delay_risk`: 0.
- Missing `recommended_action`: 0.
- Risk-to-action traceability: 100%.
- Recommendation-to-risk mapping: exactly one risk category per recommendation.
- `data/processed/decision_engine_output.csv` is a local generated artifact and should not be committed.
- This validates Decision Engine rule consistency and traceability, not ML prediction accuracy.
- Downstream presentation modules should use summary outputs where possible instead of loading the full row-level CSV.

## AI-DSS Modeling / SHAP

This module is the next required scope checkpoint. It must happen before final Streamlit dashboard development.

Required checks:

- Train/test split is reproducible.
- Real Auckland GTFS-Realtime + weather features are used, not only the Kaggle prototype dataset.
- Target variable is clearly defined.
- Baseline model result is recorded.
- Selected model metrics are recorded.
- Feature columns are listed.
- SHAP or feature-importance output is generated if supported.
- Prediction outputs are linked back to the Decision Engine.
- GitHub reproducibility is documented with scripts/notebooks and small evidence outputs; large generated data remains local unless approved.

Expected test outputs:

- Model metrics table.
- Feature importance table or chart.
- SHAP summary artifact where available.
- Notes on model limitations.

## SUMO Minimal Prototype

Required checks:

- SUMO can run locally or the limitation is documented.
- Required SUMO files exist.
- Baseline scenario output exists.
- Disruption scenario output exists.
- Intervention scenario output exists.
- Scenario output table is created.
- Results can be exported for dashboard use.

Expected test outputs:

- Average delay.
- Travel time.
- Congestion index.
- Queue length if available.
- Intervention improvement summary.

## Streamlit Dashboard

Do not proceed to this module until the AI-DSS Modeling / SHAP checkpoint exists.

Required checks:

- `streamlit run app/streamlit_app.py` starts successfully.
- Dashboard loads without errors.
- Missing files show friendly messages.
- KPIs match processed data.
- SUMO section displays saved validation outputs.
- Dashboard does not require live SUMO execution.
- Dashboard avoids loading huge raw CSV files when processed files exist.

Expected test outputs:

- Local run confirmation.
- Screenshot or visual check notes.
- Missing-file behavior check.
- KPI consistency check.

## Documentation Alignment

Required checks:

- Implementation still matches the approved architecture.
- GTFS + Open-Meteo integration is documented.
- AI prediction scope is documented.
- SHAP explainability status is documented.
- Decision engine logic is documented.
- SUMO scope is documented as scenario validation.
- Streamlit dashboard role is documented.
- Design Science Research framing is preserved.
- Overclaims are identified and corrected.

Expected test outputs:

- Alignment checklist.
- List of implementation changes since Assessment 1.
- Suggested README updates.
- Overclaim prevention notes.
