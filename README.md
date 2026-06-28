# AI-Driven Decision Support System for Auckland Public Transport Delay Prediction

This repository contains a Master of Software Engineering capstone prototype for an AI-driven decision-support system using Auckland public transport delay data.

The project combines GTFS Static, GTFS-Realtime, and Open-Meteo weather data to support AI delay-risk prediction, AI-based operational recommendations, SUMO scenario validation, and a Streamlit dashboard.

In plain English, the project works like a decision-support assistant for transport operators: it looks at public transport delay data, predicts whether a situation may need attention, recommends an action, checks one example scenario in SUMO, and presents the result in a dashboard.

## Architecture

```text
GTFS Static + GTFS-Realtime + Open-Meteo
-> Data Storage / Parquet / DuckDB
-> Notebook 09 GTFS + Weather Validation
-> AI-DSS Modeling / SHAP
-> Decision Engine
-> SUMO Scenario Validation
-> M5.1 Streamlit Dashboard
-> Azure Container Apps Deployment
```

Short semantic flow:

```text
Data comes in
-> AI predicts risk
-> system recommends action
-> SUMO tests one scenario
-> dashboard explains it
```

The implementation is a prototype decision-support system. It is not a live operations control system. SUMO outputs are scenario-estimated validation results and do not prove real-world operational success.

## Risk And Recommendation Evidence

The project keeps two kinds of risk/action evidence separate:

| Evidence type | Meaning | Main use |
|---|---|---|
| Observed/reference risk | Risk created from actual delay records | Validation, training reference, comparison, and traceability |
| AI-predicted risk | Risk created by the AI model | Final dashboard decision support and AI-based recommendations |

The final dashboard should focus on AI-predicted risk, AI-based recommended action, and SUMO scenario-estimated impact.

Primary final dashboard source:

```text
data/processed/parquet/ai_decision_support_model_baseline.parquet
```

This local Parquet output contains AI-predicted risk, AI prediction probability, predicted delay minutes, AI-based recommended action, route/service/weather context, and observed/reference risk.

## Main Reproduction Commands

Run commands from the repository root unless stated otherwise.

Prepare scalable GTFS-Realtime storage:

```powershell
python src/prepare_realtime_storage.py
```

Audit Decision Engine outputs and regenerate lightweight recommendation summaries:

```powershell
python src/audit_decision_engine_outputs.py
```

Run the AI-DSS modeling checkpoint:

```powershell
python src/train_ai_dss_model.py
```

Run the AI-DSS modeling checkpoint without writing outputs:

```powershell
python src/train_ai_dss_model.py --dry-run
```

Run the Streamlit dashboard:

```powershell
cd app
streamlit run streamlit_app.py
```

## Environment Setup

Create and activate a Python environment:

```powershell
conda create -n capstone-gtfs python=3.11 -y
conda activate capstone-gtfs
pip install -r requirements.txt
```

Optional development checks:

```powershell
pip install -r requirements-dev.txt
pytest tests/smoke
```

Create a `.env` file in the project root when live GTFS-Realtime collection is required:

```text
AT_API_KEY=your_api_key_here
```

The `.env` file is not included in the repository.

## Required Data Artifacts

Some artifacts are generated locally and intentionally excluded from GitHub because they are large or raw evidence files.

| Artifact | Source | Role | GitHub policy |
|---|---|---|---|
| `data/raw/gtfs_static/*.txt` | Auckland Transport GTFS Static download | Route, trip, stop, and schedule reference data | Some static files may be included when small enough; large raw files should stay local |
| `data/raw/gtfs_realtime/daily/*.csv` | GTFS-Realtime collection script | Raw archival trip-update observations | Do not commit |
| `data/processed/parquet/gtfs_realtime_cleaned.parquet` | `python src/prepare_realtime_storage.py` | Cleaned scalable all-file GTFS-Realtime working dataset | Do not commit |
| `data/processed/parquet/gtfs_realtime_model_baseline.parquet` | `python src/prepare_realtime_storage.py` | Quality-controlled complete-day modelling baseline | Do not commit |
| `data/processed/parquet/decision_engine_model_baseline.parquet` | Notebook 09 / Decision Engine conversion | Observed/reference risk decision output for the model baseline | Do not commit |
| `data/processed/parquet/decision_engine_all_file.parquet` | Notebook 09 / Decision Engine conversion | Observed/reference risk decision output for all collected files | Do not commit |
| `data/processed/parquet/ai_predictions_model_baseline.parquet` | AI-DSS modeling | Full local AI prediction evidence for the model baseline | Do not commit |
| `data/processed/parquet/ai_decision_support_model_baseline.parquet` | AI-DSS + Decision Engine | Primary AI-based decision-support source for the final dashboard | Do not commit |
| `data/processed/duckdb/gtfs_realtime.duckdb` | DuckDB query-layer script | Local query layer over Parquet and summary outputs | Do not commit |
| `data/processed/summaries/*.csv` | Notebook 09, Decision Engine audit, and AI scripts | Lightweight reproducibility and dashboard summaries | Commit after review when small |
| `data/processed/sumo_*.csv` | SUMO scenario-validation module | Saved scenario validation outputs for dashboard use | Commit after review when small |

## Key Public Outputs

The dashboard and public reproducibility checks should use lightweight processed outputs by default:

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
data/processed/summaries/gtfs_realtime_storage_daily_summary.csv
data/processed/summaries/gtfs_realtime_storage_route_daily_summary.csv
data/processed/summaries/gtfs_realtime_storage_top_delayed_routes.csv
data/processed/summaries/gtfs_realtime_collection_completeness.csv
data/processed/sumo_scenarios.csv
data/processed/sumo_kpis.csv
data/processed/sumo_validation_results.csv
```

Large row-level CSV files should not be loaded by the dashboard. The final dashboard should use DuckDB direct queries over Parquet, especially `data/processed/parquet/ai_decision_support_model_baseline.parquet`.

## Module Summary

| Module | Purpose | Main files |
|---|---|---|
| GTFS and weather validation | Validate real Auckland GTFS-Realtime, GTFS Static, and weather integration | `notebooks/09_validation_and_evaluation_realtimegtfs.ipynb` |
| Scalable storage | Convert cleaned GTFS-Realtime and Decision Engine outputs into Parquet, with DuckDB as the query layer | `src/prepare_realtime_storage.py`, `src/create_realtime_duckdb.py` |
| AI-DSS modeling and SHAP | Train/evaluate prediction models and create full AI prediction Parquet outputs, metrics, samples, and explainability evidence | `src/train_ai_dss_model.py`, `src/ai_dss_modeling/` |
| Decision Engine | Convert observed/reference risk and AI-predicted risk into traceable recommendation fields | `src/audit_decision_engine_outputs.py` |
| SUMO validation | Compare baseline, disruption, and intervention scenarios | `notebooks/10_sumo_minimal_prototype.ipynb`, `data/processed/sumo_*.csv` |
| Dashboard | Present AI-predicted delay risk, AI-based recommended action, and SUMO scenario-estimated impact | `app/streamlit_app.py`, `app/pages/` |

## Documentation

Public reproducibility notes are kept in:

```text
docs/reproducibility_guide.md
docs/reproducibility/
```

Internal planning notes are local-only and are not part of the public project evidence.

## Scope Limits

- The current system is a capstone prototype.
- AI model outputs support prototype decision analysis and should not be described as highly accurate overall.
- High and Severe classes are rare in the current dataset.
- Weather is included, but route, time, and service features appear stronger in the current dataset.
- SUMO is used for scenario validation only.
- The SUMO scenario has different trip counts across scenarios, so it is not a controlled identical-volume experiment.
- The dashboard should display saved processed outputs and should not depend on live SUMO execution.
- The dashboard is a decision-support prototype, not a live operations system.
- The current dataset has 23 likely complete days, not a perfect 30-day dataset.
- S-prefix routes are school/special bus services and are excluded from default public transport ranking views unless explicitly included.
