# Layer 5: Dashboard Readiness

Architecture position:

```text
SUMO Scenario Validation
-> M5.1 Streamlit Dashboard
-> Azure Container Apps Deployment
```

## Purpose

This layer identifies which outputs the future Streamlit dashboard should load. The goal is to keep the dashboard fast, reproducible, and suitable for public demonstration.

The dashboard should answer:

- Where is the AI-predicted delay risk?
- What AI-based action is recommended?
- What is the expected SUMO scenario impact?

## Primary Final Dashboard Source

Use DuckDB direct queries over this Parquet file:

```text
data/processed/parquet/ai_decision_support_model_baseline.parquet
```

This file contains AI-predicted risk, AI prediction probability, predicted delay minutes, AI-based recommended action, route/service/weather context, and observed/reference risk.

The dashboard should not load large row-level CSVs directly.

## Supporting Small Inputs

Use these small files for metrics, summaries, and lightweight charts:

```text
data/processed/summaries/ai_model_metrics.csv
data/processed/summaries/ai_feature_importance.csv
data/processed/summaries/ai_prediction_sample.csv
data/processed/summaries/ai_decision_recommendation_summary.csv
data/processed/summaries/ai_decision_route_recommendation_counts.csv
data/processed/summaries/gtfs_realtime_daily_summary.csv
data/processed/summaries/gtfs_realtime_route_daily_summary.csv
data/processed/summaries/gtfs_realtime_top_delayed_routes.csv
data/processed/sumo_scenarios.csv
data/processed/sumo_kpis.csv
data/processed/sumo_validation_results.csv
```

## Avoid Loading by Default

```text
data/processed/decision_engine_output.csv
data/processed/outputs/model_baseline/decision_engine_output.csv
data/processed/outputs/all_file/decision_engine_output.csv
data/raw/gtfs_realtime/daily/*.csv
```

## Dashboard Sections Supported

- Dataset overview.
- Delay trend summaries.
- Route-level delay summaries.
- AI model metrics.
- SHAP or feature-importance evidence.
- AI-predicted delay-risk view.
- AI-based recommendation distribution.
- Route-level AI recommendation counts.
- SUMO scenario comparison.

## Scope Limits

- The dashboard should present decision-support evidence.
- It should focus on AI-predicted risk and AI-based recommended action.
- Observed/reference risk should be used for comparison and traceability, not confused with the AI prediction.
- It should avoid loading large row-level CSVs.
- It should use DuckDB direct queries over Parquet for detailed views.
- It is a decision-support prototype, not a live operations system.
