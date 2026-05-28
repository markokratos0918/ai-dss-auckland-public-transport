# Layer 5: Dashboard Readiness

Architecture position:

```text
SUMO -> Dashboard
```

## Purpose

This layer identifies which outputs the future Streamlit dashboard should load. The goal is to keep the dashboard fast, reproducible, and suitable for public demonstration.

## Recommended Default Inputs

Load these small files by default:

```text
data/processed/summaries/ai_model_metrics.csv
data/processed/summaries/ai_feature_importance.csv
data/processed/summaries/ai_prediction_sample.csv
data/processed/summaries/decision_recommendation_summary.csv
data/processed/summaries/decision_route_recommendation_counts.csv
data/processed/summaries/gtfs_realtime_daily_summary.csv
data/processed/summaries/gtfs_realtime_route_daily_summary.csv
data/processed/summaries/gtfs_realtime_top_delayed_routes.csv
data/processed/intervention_logic.csv
data/processed/sumo_scenarios.csv
data/processed/sumo_kpis.csv
data/processed/sumo_validation_results.csv
```

## Optional Detailed Local Input

Use this only when detailed filtering is required:

```text
data/processed/gtfs_realtime_cleaned.parquet
```

## Avoid Loading by Default

```text
data/processed/decision_engine_output.csv
data/raw/gtfs_realtime/daily/*.csv
```

## Dashboard Sections Supported

- Dataset overview.
- Delay trend summaries.
- Route-level delay summaries.
- AI model metrics.
- SHAP or feature-importance evidence.
- Decision recommendation distribution.
- Route-level recommendation counts.
- SUMO scenario comparison.

## Scope Limits

- The dashboard should present decision-support evidence.
- It should avoid loading large row-level CSVs by default.
- It should work from small summary outputs where possible.
