# Layer 5: Dashboard Readiness

Last reviewed: 2026-06-26

Architecture position:

```text
SUMO Scenario Validation
-> M5.1 Streamlit Dashboard
-> Azure Container Apps Deployment
```

## Purpose

This layer identifies which outputs the M5.1 Streamlit dashboard loads. The dashboard is built and its visual design is locked for the Assessment 2 checkpoint. The goal is to keep the dashboard fast, reproducible, and suitable for public demonstration.

The dashboard should answer:

- Where is the AI-predicted delay risk?
- What AI-based action is recommended?
- What is the expected SUMO scenario impact?

## Primary Final Dashboard Source

Query this Parquet file through DuckDB:

```text
data/processed/parquet/ai_decision_support_model_baseline.parquet
```

This file contains AI-predicted risk, AI prediction probability, predicted delay minutes, AI-based recommended action, route/service/weather context, and observed/reference risk.

Where a dedicated DuckDB view over this file is not yet registered, the dashboard reads the Parquet file directly through DuckDB. Either way, the dashboard should not load large row-level CSVs directly.

## Supporting Small Inputs

Use these small files for metrics, summaries, and lightweight charts:

```text
data/processed/summaries/ai_model_metrics.csv
data/processed/summaries/ai_feature_importance.csv
data/processed/summaries/ai_prediction_sample.csv
data/processed/summaries/ai_decision_recommendation_summary.csv
data/processed/summaries/ai_decision_route_recommendation_counts.csv
data/processed/summaries/decision_recommendation_summary.csv
data/processed/summaries/decision_route_recommendation_counts.csv
data/processed/summaries/route_delay_risk_summary.csv
data/processed/summaries/service_type_delay_summary.csv
data/processed/summaries/weather_delay_risk_summary.csv
data/processed/summaries/ai_feature_explanation_lookup.csv
data/processed/summaries/gtfs_realtime_collection_completeness.csv
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
